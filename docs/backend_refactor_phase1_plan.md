# 阶段 1 细化实施方案：核心数据闭环

> 范围：让新建 `backend/`（FastAPI）真正跑通两条主链路——
> **(A) 知识库文档真实上传 → 解析 → 切分 → 向量化入库**（含状态回流）
> **(B) `WORK_FLOW` 类型应用的对话真正走 `WorkflowEngine`，不再降级为 SIMPLE 流式**
>
> 这两项是 `docs/backend_refactor_api_diff.md` 中判定为"最阻塞"的能力。本方案是路线图阶段 1 的可执行细化。

---

## 0. 关键结论：阶段 1 主要是"接线"，不是"重写"

经核对，`backend/` 已有 80% 的底层实现，只是**没有接上线**：

| 能力 | 实现位置 | 现状 |
|------|----------|------|
| 解析/切分/向量化/入库 | `app/rag/pipeline.py:ingest_document` | ✅ 完整 |
| 多格式解析器（PDF/HTML/DOCX/XLSX/CSV/ZIP） | `app/rag/parsers.py` | ✅ 完整 |
| 结构感知切分器 | `app/rag/splitter.py` | ✅ 完整 |
| arq 异步入库任务 | `app/core/tasks.py:ingest_document_task` | ✅ 完整 |
| web→arq 入队辅助 | `app/core/tasks.py:enqueue_ingest` | ✅ 完整 |
| 工作流引擎（run/stream） | `app/workflows/engine.py:WorkflowEngine` | ✅ 完整 |
| 36 个工作流节点（含 llm/检索/条件/回复/表单…） | `app/workflows/nodes/*` | ✅ 完整 |
| **知识库上传端点** | `app/api/knowledge.py` | ❌ **不存在**（仅 `split` 预览） |
| **`enqueue_ingest` 的调用方** | `app/api/knowledge.py` | ❌ **无人调用**（`trigger_embedding`/`refresh` 只改 status 标志） |
| **`WORK_FLOW` 接入对话** | `app/api/chat.py:chat_message` | ❌ **228–230 行强制降级为 SIMPLE** |

因此阶段 1 的工作量集中在**端点接线 + 状态回流 + 配置注入**，而非算法实现。

---

## 1. 验收标准（Done Definition）

**链路 A — 知识库真实入库**
1. `POST /api/knowledge/{knowledge_id}/document/{document_id}/upload` 上传文件后，该文档的段落（paragraph）与向量（embedding）真实写入 `paragraph` / `embedding` 表。
2. 入库完成后 `document.status` 由 `WAIT` → `SUCCESS`（失败 → `ERROR`，并在 `status_meta.error` 记录原因）。
3. `GET /api/knowledge/{knowledge_id}/hit_test` 能检索到刚入库的内容（复用已实现的 `PgVectorRetriever`）。
4. 向量化在 arq worker 中异步执行，web 请求不阻塞。

**链路 B — WORK_FLOW 对话**
5. 当 `application.type == "WORK_FLOW"` 时，`POST /api/chat/chat_message/{chat_id}` 真正构造 `WorkflowEngine(application.work_flow, ...)` 并 `stream()`，输出与节点执行对应的 SSE 帧。
6. 工作流内的 `search-knowledge-node` 能基于入库的向量做检索，`ai-chat-node` 能基于检索上下文生成回答。
7. 对话结束后 `ChatRecord` 被持久化（answer 取自工作流最终 answer）。

**通用**
8. 不修改 `db.py` 的"禁止 create_all"约束（表由 legacy Django 创建）。
9. `uvx ruff check app` 与 `uv run pytest -q` 通过。

---

## 2. 改动一：知识库真实上传 + 异步向量化

### 2.1 新增上传端点（文件 `app/api/knowledge.py`）

在 `create_document`（213 行）之后、`get_document`（240 行）之前新增：

```python
@router.post("/{knowledge_id}/document/{document_id}/upload")
async def upload_document(
    knowledge_id: str,
    document_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    """Receive a source file and enqueue async ingestion (parse→split→embed→store)."""
    knowledge = await session.get(Knowledge, knowledge_id)
    if knowledge is None:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    document = await session.get(Document, document_id)
    if document is None or str(document.knowledge_id) != knowledge_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if not knowledge.embedding_model_id:
        raise HTTPException(status_code=400, detail="No embedding model configured for knowledge base")

    model_row = await session.get(Model, knowledge.embedding_model_id)
    if model_row is None:
        raise HTTPException(status_code=400, detail="Embedding model not found")

    content = await file.read()
    embedding = {
        "provider": model_row.provider,
        "model_name": model_row.model_name,
        "credential": model_row.credential or {},
        "dimensions": (model_row.meta or {}).get("dimensions"),
    }

    # Mark as PENDING then enqueue; arq worker flips it to SUCCESS / ERROR.
    document.status = "PENDING"
    document.status_meta = {"step": "queued", "filename": file.filename}
    await session.commit()

    from app.core.tasks import enqueue_ingest

    await enqueue_ingest(
        knowledge_id=str(knowledge_id),
        document_id=str(document_id),
        user_id=str(document.user_id) if document.user_id else None,
        filename=file.filename or "document",
        content=content,
        embedding=embedding,
    )
    return {"result": True, "document_id": str(document_id), "status": "PENDING"}
```

> 说明：复用 `chat.py:_embedding_dict()` 的相同字段结构（`provider/model_name/credential/dimensions`），保证与 `search_knowledge` 节点约定一致。

### 2.2 入库后状态回流（文件 `app/core/tasks.py`）

`ingest_document_task`（46 行）当前在 `ingest_document` 成功后**没有更新 `Document.status`**。在 `async with SessionLocal()` 内补充状态写回：

```python
async def ingest_document_task(ctx, *, knowledge_id, document_id, user_id, filename, content, embedding, **kwargs):
    from app.rag.pipeline import ingest_document
    from app.models.knowledge import Document as DocRow

    async with SessionLocal() as session:
        try:
            result = await ingest_document(
                session, knowledge_id=knowledge_id, document_id=document_id,
                user_id=user_id, filename=filename, content=content, embedding=embedding, **kwargs,
            )
            doc = await session.get(DocRow, document_id)
            if doc is not None:
                doc.status = "SUCCESS"
                doc.status_meta = {
                    "step": "done",
                    "paragraph_count": result.paragraph_count,
                    "embedding_count": result.embedding_count,
                    "char_length": result.char_length,
                }
            await session.commit()
            return { ... }  # 现有返回值
        except Exception as exc:
            doc = await session.get(DocRow, document_id)
            if doc is not None:
                doc.status = "ERROR"
                doc.status_meta = {"step": "failed", "error": str(exc)}
            await session.commit()
            raise
```

> 注意：`SessionLocal` 与 `engine` 已在文件顶部导入（31 行），`DocRow` 即 `app/models/knowledge.py:Document`，需补 import。

### 2.3 关于"重新向量化"（trigger_embedding / refresh）

当前 `trigger_embedding`（471 行）、`refresh_document`（691 行）只把 `status` 置 `PENDING`，**未调用 `enqueue_ingest`**，且 `backend/` 没有持久化源文件（Django 依赖 `file` 表的 `loid` 大对象）。

**阶段 1 取舍**：
- 主链路 = **上传即向量化**（2.1 已覆盖首次入库），无需 `trigger_embedding` 立即重跑。
- 真正的"重跑"依赖**源文件持久化**（写 `file` 表 / 本地 OSS），列为阶段 2 子任务。
- 阶段 1 仅做最小修正：在 `trigger_embedding` / `refresh_document` 中，若 `Document.meta` 已含 `source_file_id`（阶段 2 落地的产物），则调用 `enqueue_ingest` 重跑；否则保持现状并返回明确提示，避免"假成功"。即：

```python
# trigger_embedding / refresh_document 内
source_file_id = (doc.meta or {}).get("source_file_id")
if source_file_id:
    # 阶段 2 落地源文件存储后，这里读取 bytes 并 enqueue_ingest
    ...
else:
    # 阶段 1：尚未持久化源文件，提示依赖上传端点触发首次入库
    logger.warning("source file not persisted; use upload endpoint for first ingestion")
```

> 这样阶段 1 不会出现"置 PENDING 却永不跑"的伪状态。

---

## 3. 改动二：WORK_FLOW 对话接入 WorkflowEngine

### 3.1 chat_message 分支改造（文件 `app/api/chat.py`）

当前 225–230 行：

```python
    if body.stream and application.type == "SIMPLE":
        return await _chat_simple_stream(application, body, chat, session)
    return await _chat_simple_stream(application, body, chat, session)   # ← 强制降级
```

改为：

```python
    if application.type == "WORK_FLOW":
        return await _chat_workflow_stream(application, body, chat, session)
    return await _chat_simple_stream(application, body, chat, session)   # SIMPLE / 默认
```

### 3.2 新增 `_chat_workflow_stream`（文件 `app/api/chat.py`）

```python
async def _chat_workflow_stream(application, body, chat, session) -> StreamingResponse:
    # 1) LLM 模型配置（来自 application.model_id）
    model_row = await session.get(Model, application.model_id) if application.model_id else None
    if model_row is None:
        raise HTTPException(status_code=400, detail="No chat model configured")
    model_config = {
        "provider": model_row.provider,
        "model_name": model_row.model_name,
        "credential": model_row.credential or {},
        # 后续增强：把 application.model_params_setting 透传给节点
    }

    # 2) Embedding 配置（来自 application.knowledge_setting.embedding_model_id）
    ks = application.knowledge_setting or {}
    embedding_model_row = (
        await session.get(Model, ks["embedding_model_id"]) if ks.get("embedding_model_id") else None
    )
    embedding_config = None
    if embedding_model_row is not None:
        embedding_config = {
            "provider": embedding_model_row.provider,
            "model_name": embedding_model_row.model_name,
            "credential": embedding_model_row.credential or {},
            "dimensions": (embedding_model_row.meta or {}).get("dimensions"),
        }

    # 3) 构造引擎（flow 即 application.work_flow 的 JSON 图）
    from app.workflows.engine import WorkflowEngine

    params = {
        "question": body.message,
        "chat_id": str(chat.id),
        "model_config": model_config,
        "embedding_config": embedding_config,
    }
    engine = WorkflowEngine(
        application.work_flow,
        params,
        model_config=model_config,
        embedding_config=embedding_config,
    )

    # 4) 流式透传 + 持久化
    async def event_source():
        full_answer = ""
        try:
            async for sse in engine.stream():
                # WorkflowEngine 已产出标准 SSE 帧（type=answer/node_start/...)
                if '"type": "answer"' in sse or '"type":"answer"' in sse:
                    full_answer += sse
                yield sse
        except Exception as exc:
            yield "data: " + json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n\n"
        finally:
            _persist_chat_record(chat, body.message, _extract_answer(full_answer), session)

    return StreamingResponse(event_source(), media_type="text/event-stream")
```

> 节点契约（已确认）：`llm_chat.py:17` 读 `params["model_config"]`；`search_knowledge.py:42` 读 `params["embedding_config"]`；`start.py:12` 读 `params["question"]`。因此上面的注入字段可直接被节点消费。

### 3.3 抽取 ChatRecord 持久化辅助

把 `chat.py:279–294` 的"持久化 ChatRecord"逻辑抽出为 `_persist_chat_record(chat, problem, answer, session)`（SIMPLE 与 WORK_FLOW 共用），避免重复。answer 提取：WORK_FLOW 的最终 answer 在 `engine.stream()` 末尾的 `{"type":"done","answer":...}` 帧中；在 `event_source` 里捕获该帧的 `answer` 字段即可（比正则拼接更稳）。

> 建议：在 `WorkflowEngine.stream()` 的 `done` 帧里已携带 `answer`，`_chat_workflow_stream` 解析该帧填充 `final_answer`，再传给 `_persist_chat_record`。

---

## 4. 改动文件清单（精确）

| 文件 | 行/位置 | 改动 |
|------|---------|------|
| `app/api/knowledge.py` | 213 行后 | 新增 `POST /{knowledge_id}/document/{document_id}/upload` |
| `app/api/knowledge.py` | 471 / 691 行 | `trigger_embedding`/`refresh_document` 增加"若 source_file_id 存在则 enqueue"分支 |
| `app/core/tasks.py` | 46–80 行 | `ingest_document_task` 增加 SUCCESS/ERROR 状态回流（import `Document`） |
| `app/api/chat.py` | 225–230 行 | `chat_message` 增加 `WORK_FLOW` 分支，去除强制降级 |
| `app/api/chat.py` | 末尾 | 新增 `_chat_workflow_stream`、`_persist_chat_record` 辅助 |
| `app/workflows/engine.py` | （可选增强） | `done` 帧已含 answer；无需改 |

无需改动：`app/rag/*`、`app/workflows/nodes/*`、`app/providers/*`、`app/core/db.py`。

---

## 5. 端到端验证（需 PG + Redis + worker 三件套）

```bash
# 终端 1：PostgreSQL(pgvector) + Redis 已就绪前提下，启动 web
cd backend && uv run python main.py
# 终端 2：启动 arq worker
cd backend && uv run python -c "from app.core.tasks import run_worker; run_worker()"
```

### 链路 A
```bash
# 1) 建知识库（已可用）
KB=$(curl -s -X POST :8080/api/knowledge -H 'Authorization: Bearer <JWT>' \
     -d '{"name":"kb1","embedding_model_id":"<model_uuid>"}' | jq -r .id)
# 2) 建文档空记录
DOC=$(curl -s -X POST :8080/api/knowledge/$KB/document -H 'Authorization: Bearer <JWT>' \
     -d '{"name":"d1","type":0}' | jq -r .id)
# 3) 上传文件 → 触发异步入库
curl -X POST :8080/api/knowledge/$KB/document/$DOC/upload \
     -H 'Authorization: Bearer <JWT>' -F "file=@/path/to/sample.md"
# 4) 轮询状态（期待 SUCCESS）
curl :8080/api/knowledge/$KB/document/$DOC | jq .status
# 5) hit_test 应返回刚入库内容
curl -X POST :8080/api/knowledge/$KB/hit_test -H 'Authorization: Bearer <JWT>' \
     -d '{"query_text":"...","top_number":3,"similarity":0.5}'
```

### 链路 B
```bash
# 准备一个 type=WORK_FLOW 且 work_flow 含 start→search-knowledge→ai-chat→reply 的应用
APP=<application_uuid>
TOKEN=<anonymous access_token>
CHAT=$(curl -s ":8080/api/chat/open?access_token=$TOKEN" | jq -r .id)
curl -N -X POST :8080/api/chat/chat_message/$CHAT \
     -H "Content-Type: application/json" -d '{"message":"知识库里有什么？","stream":true}'
# 期望看到 node_start / answer / node_end / done 帧，且最终 answer 有内容
```

### 自动化
- 在 `app/tests/` 新增 `test_phase1_ingest.py`（用 fakeredis + sqlite/测试 PG 若可用）与 `test_phase1_workflow_chat.py`（用 mock provider），纳入 `uv run pytest -q`。

---

## 6. 风险与回退

| 风险 | 缓解 |
|------|------|
| arq 经 Redis 序列化大文件 bytes 占内存 | 阶段 1 接受（文件 ≤ `file_size_limit` 默认 100MB）；阶段 2 改为源文件持久化后传引用 |
| `WorkflowEngine.stream()` 的 SSE 字段与前端期望不完全一致 | 阶段 1 先保证"能跑通、有 answer"；字段对齐在阶段 5 契约测试中统一校验 |
| embedding 维度与 `embedding` 表 `Vector(1536)` 不匹配导致入库失败 | `enqueue_ingest` 的 `dimensions` 取自 `model_row.meta.dimensions`，与 legacy 一致；异常会被状态回流捕获为 ERROR |
| `WORK_FLOW` 引用了未实现节点类型 | 引擎已对未知类型抛 `unsupported node type`；阶段 1 用含已知节点（start/search/ai-chat/reply）的 flow 验证 |

回退：两条链路均为**新增分支/新增端点**，不改动 SIMPLE 主路径；若 worker 不可用，上传端点会置 PENDING 但 web 不报错，可随时回滚端点接线。

---

## 7. 工作量估算

| 任务 | 估计 |
|------|------|
| 上传端点 + 状态回流 | 0.5 天 |
| chat_message WORK_FLOW 分支 + `_chat_workflow_stream` | 0.5 天 |
| 端到端联调（PG+Redis+worker） | 1 天 |
| 自动化测试补充 | 0.5 天 |
| **合计** | **约 2.5 天** |

---

## 8. 后续阶段何时启动

- **阶段 2（管理功能闭环）**：QA/表格/版本/历史/工具/触发器补齐，以及本方案 2.3 的"源文件持久化 + 重跑"。
- **阶段 3（模型与 Provider）**：`model_params_setting` 透传给节点、TTS/STT/TTI 等多媒体节点 SDK 接入。
- **阶段 4（统计/仪表盘/运维）**：排行真实聚合、权限持久化、邮件验证码。
- **阶段 5（兼容与验证收尾）**：workspace 前缀、SSE 字段契约测试、CI 集成。
