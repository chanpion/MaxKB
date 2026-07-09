---
name: create-codebuddy-md
overview: 在仓库根目录创建 CODEBUDDY.md，为后续 CodeBuddy 实例提供常用的构建/运行/测试/lint 命令，以及 MaxKB 后端的高层架构说明（Django 单体 + 多领域 app、RAG 流水线、模型供应商抽象、Celery 异步、多服务入口等）。
todos:
  - id: verify-rule-files
    content: 确认仓库根无既有 AGENTS/CODEBUDDY/CLAUDE/Cursor/Copilot 规则文件（已确认均不存在）
    status: completed
  - id: write-commands
    content: 编写 CODEBUDDY.md 命令章节：uv 安装、迁移、runserver、Celery、local_model、ruff、单测、Docker 构建
    status: completed
    dependencies:
      - verify-rule-files
  - id: write-architecture
    content: 编写架构章节：模块职责、RAG/对话/工具数据流、配置与部署、扩展点
    status: completed
    dependencies:
      - verify-rule-files
  - id: assemble-file
    content: 以指定前缀组装并写入 /Users/logenswolf/IdeaProjects/MaxKB/CODEBUDDY.md
    status: completed
    dependencies:
      - write-commands
      - write-architecture
---

## 用户需求

为 MaxKB 当前后端代码库生成 `CODEBUDDY.md` 引导文件，供未来 CodeBuddy Agent 实例在本仓库中快速上手并高效开发。

## 前置校验（已完成）

已搜索仓库根：`AGENTS.md`、`CODEBUDDY.md`、`CLAUDE.md`、`.cursorrules`、`.github/copilot-instructions.md` 均不存在。依据规则，直接新建 `CODEBUDDY.md`（不新建 `AGENTS.md`）。文件必须以 `# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.` 开头。

## 核心内容

- **命令章节**：依赖安装（uv）、数据库迁移、开发服务器、Celery worker、本地模型服务、lint（ruff，line-length=120）、运行测试（单 app / 单测试类）、Docker 镜像构建。每条命令描述 ≤100 词。
- **架构章节（≤1600 词）**：聚焦需跨文件理解的整体架构——Django 单体（业务按领域拆成多个 app）、`models_provider` 多厂商 LLM 适配层、知识库 RAG 数据流（解析→拆分→嵌入→pgvector→召回→生成）、对话/工作流/工具与 MCP 调用链路、`chat_pipeline` 与 `flow` 引擎、Celery/apscheduler 异步与定时、配置与前后端一体部署形态、扩展点（新增模型供应商、新增解析器）。
- 不重复显而易见的内容，不罗列易发现的文件结构，不编造未经验证的章节。