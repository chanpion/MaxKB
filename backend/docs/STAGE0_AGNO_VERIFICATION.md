# 阶段 0：Agno 能力验证报告

> 生成时间：2026-07-08
> 目的：验证 Agno（最新稳定版，实现时由 `uv` 锁定）对 MaxKB 现有模型供应商的覆盖度，为 `backend/app/providers/` 的"原生 vs 自研"分级提供依据。

## 1. 环境说明

- Python：**3.11.9**（已通过 `install_binary` 安装，路径 `/Users/logenswolf/.workbuddy/binaries/python/versions/3.11.9/bin/python3`）。
- `backend/.venv` 虚拟环境已创建（Python 3.11）。
- ⚠️ **当前交互式 shell 无外网**（`pip`/`curl` 均被沙箱跳过），因此 Agno 依赖**尚未本地安装**，无法运行 `introspect` 或 `pytest`。
  - 缓解：本阶段结论基于 Agno 官方文档（docs.agno.com model-index）与仓库概览，属静态验证。
  - 后续阶段需在**可联网环境**执行 `uv sync` 后再做动态校验（import 路径、API 签名以实际安装版本为准）。

## 2. Agno 安装方式（关键）

Agno 基础包**不含任何模型 provider**，必须按 extra 安装：

```bash
# 基础
uv add "agno"
# 常用 provider extras（覆盖 MaxKB 绝大多数厂商）
uv add "agno[openai,anthropic,google,groq,ollama,aws,azure,dashscope,litellm,postgres,pgvector,memory]"
```

## 3. Agno 官方 Provider 分类（来自 docs.agno.com/models/providers/model-index）

| 类别 | 原生 Provider |
| --- | --- |
| **Native** | Anthropic、Cohere、DashScope(阿里)、DeepSeek、Google Gemini、Inception、Meta、MiniMax、Mistral、OpenAI、OpenAI Responses、Perplexity、Vercel、xAI、Xiaomi MiMo |
| **Local** | LlamaCpp、LM Studio、Ollama、VLLM |
| **Cloud** | AWS Bedrock、Claude via AWS Bedrock、Azure AI Foundry、Azure OpenAI、Vertex AI Claude、IBM WatsonX |
| **Gateways** | AI/ML API、Cerebras、Cloudflare、CometAPI、DeepInfra、Fireworks、Groq、Hugging Face、LangDB、LiteLLM、LiteLLM OpenAI、Nebius、Neosantara、Nexus、NVIDIA、OpenRouter、Portkey、Requesty、Sambanova、SiliconFlow、Together |

要点：
- 默认支持上述所有厂商的全部模型。
- 通过 **`agno.models.litellm.LiteLLM`** 网关可进一步覆盖长尾厂商。
- 通过 **`agno.models.openai.OpenAIChat(base_url=...)`** 可接入任何 OpenAI 兼容端点（国内厂商普遍支持）。

## 4. MaxKB `impl/` 厂商 → Agno 映射（核心结论）

MaxKB `apps/models_provider/impl/` 共 24 个 provider。映射分级如下：

### 4.1 Agno 原生覆盖（直接使用 `agno.models.*`）

| MaxKB provider | Agno 对应 | 备注 |
| --- | --- | --- |
| `openai` | `agno.models.openai.OpenAIChat` | 原生 |
| `anthropic` | `agno.models.anthropic.Anthropic` | 原生 |
| `gemini` | `agno.models.google.Gemini` | 原生 |
| `deepseek` | `agno.models.deepseek.DeepSeek` | 原生 |
| `minimax` | `agno.models.minimax.MiniMax` | 原生（Native 列表含 MiniMax） |
| `ollama` | `agno.models.ollama.Ollama` | 原生（Local） |
| `vllm` | `agno.models.vllm.VLLM` | 原生（Local） |
| `aws_bedrock` | `agno.models.aws.Bedrock` | 原生（Cloud） |
| `azure` | `agno.models.azure.AzureOpenAI` | 原生（Cloud） |
| `aliyun_bai_lian` / `qwen` | `agno.models.dashscope.DashScope` | 原生（DashScope=阿里通义/百炼） |
| `siliconCloud` | `agno.models.gateways.siliconflow`(SiliconFlow) | 网关原生 |

### 4.2 OpenAI 兼容端点覆盖（统一用 `agno.models.openai.OpenAIChat(base_url=..., api_key=..., id=...)`）

仅需轻量适配层做"凭据 + 端点映射"，**无需重写模型调用逻辑**：

| MaxKB provider | OpenAI 兼容端点 | 说明 |
| --- | --- | --- |
| `kimi` | Moonshot `/v1` | 月之暗面兼容 |
| `qwen`（备用） | 通义 `/compatible-mode/v1` | 也可用 4.1 的 DashScope |
| `local_model` | 本地服务 `/v1` | 本地模型服务（含 `local_model` 进程） |
| `regolo` | Regolo AI `/v1` | 意大利厂商，提供兼容端点 |
| `tencent` / `tencent_cloud` | 腾讯混元 `/v1` | 混元 OpenAI 兼容 |
| `volcanic_engine` | 火山方舟 `ark` `/api/v3` | 兼容 OpenAI |
| `xinference` | xinference `/v1` | 自托管兼容 |
| `zhipu` | 智谱 `/api/paas/v4` | GLM 兼容 OpenAI |

### 4.3 通过 LiteLLM 网关覆盖

| MaxKB provider | 方式 | 说明 |
| --- | --- | --- |
| `wenxin`（文心） | `agno.models.litellm.LiteLLM(model="ernie-...")` | LiteLLM 支持文心/ERNIE；若 LiteLLM 不支持特定模型再降级自研 |
| `docker_ai` | `agno.models.litellm.LiteLLM(...)` | Docker AI 经 LiteLLM |

### 4.4 需真正自研 Agno Model 适配器（非 OpenAI 兼容、LiteLLM 不支持）

| MaxKB provider | 原因 | 方案 |
| --- | --- | --- |
| `xf`（讯飞星火） | 自定义 WebSocket 协议，非 OpenAI 兼容，LiteLLM 不支持 | 自研 `XunfeiModel(agno.models.base.Model)` 子类，实现 `invoke`/`stream`，沿用 MaxKB `base_stt`/星火逻辑 |

> 结论：**24 个 provider 中，23 个可由 Agno 原生 / OpenAI-compatible / LiteLLM 覆盖，仅 1 个（讯飞 XF）需自研适配器**。这极大降低了 `providers/` 层工作量，符合"优先 Agno 原生"约束。

## 5. 多模态（TTI/TTS/STT）覆盖范围

MaxKB 现有 `base_tti.py` / `base_tts.py` / `base_stt.py` 及 `ModelTypeConst` 含 IMAGE/TTI/TTV/ITV/STT/TTS。

- Agno 以**文本 LLM + 工具 + 知识库**为核心，多模态（图像生成、语音合成/识别）原生支持有限。
- 方案：多模态模型在 `providers/` 中保留**轻量适配层**（封装厂商 SDK/HTTP），对外暴露为 Agno `Tool` 或 `Model` 子类，沿用 MaxKB `base_tti/base_tts/base_stt` 的调用逻辑，不强行塞入 Agno 文本模型接口。

## 6. Agno 其他能力核对（供后续阶段）

| 能力 | Agno 原生 | 后续阶段 |
| --- | --- | --- |
| Agent 对话 | `agno.agent.Agent` + `add_history_to_messages`/`storage` | 阶段 6 重写 chat_pipeline |
| 长期记忆 | `agno.memory`（Memory 类 + `db` 后端） | 阶段 6 接入 long_term_memory |
| 工作流 | `agno.workflow.Workflow` + `@workflow.run`/step | 阶段 7 重写 flow |
| 工具/函数调用 | `agno.tools`（FunctionCall / 自定义 Tool） | 阶段 4/8 |
| 检索 | `agno.retriever.base.Retriever` 自定义子类 | 阶段 5 Custom Retriever |
| 知识库 | `agno.knowledge` + `agno.vectordb`（含 `PgVector`） | 阶段 5 仅用 Retriever 适配，不直接用 Agno PgVector（保持现有 pgvector 表兼容） |

> 注：Agno 的具体导入路径与 API 签名以**实现时实际安装的版本**为准（阶段 4 实现前需 `uv sync` 后 `python -c "import agno; ..."` 复核）。

## 7. 给阶段 1/4 的下一步

1. 阶段 1 的 `pyproject.toml` 必须声明 Agno 及所需 extras（见 §2）。
2. 阶段 4 按 §4 的分级实现 `backend/app/providers/`：`native_*`（直接 agno.models.*）、`openai_compat_*`（OpenAIChat+base_url）、`litellm_*`（LiteLLM）、`xunfei`（自研）。
3. 凭据校验/加密（`BaseModelCredential.is_valid`/`encryption_dict`）在 `providers/base.py` 统一保留。
