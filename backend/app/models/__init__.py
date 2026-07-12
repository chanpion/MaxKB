# SQLModel table registry.
#
# Every model module is imported here so that tables register on
# `SQLModel.metadata`, which Alembic's env.py uses as `target_metadata`.
# Populated in stage 2 (table alignment with the legacy Django models).

from app.models.application import (
    Application,
    ApplicationAccessToken,
    ApplicationApiKey,
    ApplicationChatUserStats,
    ApplicationFolder,
    ApplicationKnowledgeMapping,
    ApplicationLongTermMemory,
    ApplicationVersion,
    Chat,
    ChatRecord,
    ChatShareLink,
)
from app.models.knowledge import (
    Document,
    DocumentTag,
    Embedding,
    File,
    Knowledge,
    KnowledgeFolder,
    KnowledgeWorkflow,
    KnowledgeWorkflowVersion,
    Paragraph,
    Problem,
    ProblemParagraphMapping,
    Tag,
    Termbase,
)
from app.models.model import Model
from app.models.system import (
    ChatUser,
    Log,
    ResourceChatUserAuthorize,
    ResourceChatUserGroupAuthorize,
    ResourceMapping,
    SystemSetting,
    UserGroup,
    UserGroupRelation,
    WorkspaceUserResourcePermission,
)
from app.models.tool import (
    Tool,
    ToolFolder,
    ToolRecord,
    ToolWorkflow,
    ToolWorkflowVersion,
)
from app.models.trigger import TaskRecord, Trigger, TriggerTask
from app.models.user import User

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
