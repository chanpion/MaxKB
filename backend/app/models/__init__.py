# SQLModel table registry.
#
# Every model module is imported here so that tables register on
# `SQLModel.metadata`, which Alembic's env.py uses as `target_metadata`.
# Populated in stage 2 (table alignment with the legacy Django models).

from app.models.user import User
from app.models.model import Model
from app.models.system import (
    SystemSetting,
    ChatUser,
    UserGroup,
    UserGroupRelation,
    ResourceChatUserAuthorize,
    ResourceChatUserGroupAuthorize,
    Log,
    ResourceMapping,
    WorkspaceUserResourcePermission,
)
from app.models.tool import (
    ToolFolder,
    Tool,
    ToolRecord,
    ToolWorkflow,
    ToolWorkflowVersion,
)
from app.models.trigger import Trigger, TriggerTask, TaskRecord
from app.models.knowledge import (
    KnowledgeFolder,
    Knowledge,
    KnowledgeWorkflow,
    KnowledgeWorkflowVersion,
    Document,
    Tag,
    DocumentTag,
    Paragraph,
    Problem,
    ProblemParagraphMapping,
    Termbase,
    Embedding,
    File,
)
from app.models.application import (
    ApplicationFolder,
    Application,
    ApplicationKnowledgeMapping,
    ApplicationVersion,
    Chat,
    ChatRecord,
    ChatShareLink,
    ApplicationChatUserStats,
    ApplicationLongTermMemory,
    ApplicationAccessToken,
    ApplicationApiKey,
)

__all__ = [
    "User",
    "Model",
    "SystemSetting",
    "ChatUser",
    "UserGroup",
    "UserGroupRelation",
    "ResourceChatUserAuthorize",
    "ResourceChatUserGroupAuthorize",
    "Log",
    "ResourceMapping",
    "WorkspaceUserResourcePermission",
    "ToolFolder",
    "Tool",
    "ToolRecord",
    "ToolWorkflow",
    "ToolWorkflowVersion",
    "Trigger",
    "TriggerTask",
    "TaskRecord",
    "KnowledgeFolder",
    "Knowledge",
    "KnowledgeWorkflow",
    "KnowledgeWorkflowVersion",
    "Document",
    "Tag",
    "DocumentTag",
    "Paragraph",
    "Problem",
    "ProblemParagraphMapping",
    "Termbase",
    "Embedding",
    "File",
    "ApplicationFolder",
    "Application",
    "ApplicationKnowledgeMapping",
    "ApplicationVersion",
    "Chat",
    "ChatRecord",
    "ChatShareLink",
    "ApplicationChatUserStats",
    "ApplicationLongTermMemory",
    "ApplicationAccessToken",
    "ApplicationApiKey",
]
