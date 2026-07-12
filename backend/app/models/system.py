"""system_manage app tables + shared `system_setting` (also used by local_model)."""

from uuid import UUID

import uuid_utils.compat as uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, String

from app.models.base import AppTableBase


class SystemSetting(AppTableBase, table=True):
    __tablename__ = "system_setting"
    type: int = Field(default=0, primary_key=True)
    meta: dict = Field(default={}, sa_column=Column(JSONB))


class ChatUser(AppTableBase, table=True):
    __tablename__ = "chat_user"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    email: str | None = Field(default=None, index=True, max_length=254)
    phone: str = Field(default="", max_length=20, index=True)
    nick_name: str = Field(default="", max_length=150, unique=True, index=True)
    username: str = Field(default="", max_length=150, unique=True, index=True)
    password: str = Field(default="", max_length=150)
    source: str = Field(default="LOCAL", max_length=10, index=True)
    is_active: bool = Field(default=True, index=True)


class UserGroup(AppTableBase, table=True):
    __tablename__ = "user_group"
    id: str = Field(default_factory=lambda: str(uuid.uuid7()), max_length=128, primary_key=True)
    name: str = Field(default="", max_length=150, unique=True, index=True)


class UserGroupRelation(AppTableBase, table=True):
    __tablename__ = "user_group_relation"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    user_id: UUID
    group_id: str = Field(max_length=128)


class ResourceChatUserAuthorize(AppTableBase, table=True):
    __tablename__ = "resource_chat_user_authorize"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    workspace_id: str | None = Field(default=None, max_length=64, index=True)
    user_group_id: str = Field(max_length=128)
    user_id: UUID
    resource_id: UUID = Field(index=True)
    resource_type: str = Field(index=True)
    is_auth: bool


class ResourceChatUserGroupAuthorize(AppTableBase, table=True):
    __tablename__ = "resource_chat_user_group_authorize"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    workspace_id: str | None = Field(default=None, max_length=64, index=True)
    user_group_id: str = Field(max_length=128)
    resource_id: UUID = Field(index=True)
    resource_type: str = Field(index=True)
    is_auth: bool


class Log(AppTableBase, table=True):
    __tablename__ = "log"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    menu: str = Field(default="", max_length=128)
    operate: str = Field(default="", max_length=128, index=True)
    operation_object: dict = Field(default={}, sa_column=Column(JSONB))
    user: dict = Field(default={}, sa_column=Column(JSONB))
    status: int = Field(default=0, index=True)
    ip_address: str = Field(default="", max_length=128)
    details: dict = Field(default={}, sa_column=Column(JSONB))
    workspace_id: str = Field(default="default", max_length=64, index=True)


class ResourceMapping(AppTableBase, table=True):
    __tablename__ = "resource_mapping"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    source_type: str = Field(index=True)
    target_type: str = Field(index=True)
    source_id: str = Field(default="", max_length=128, index=True)
    target_id: str = Field(default="", max_length=128, index=True)


class WorkspaceUserResourcePermission(AppTableBase, table=True):
    __tablename__ = "workspace_user_resource_permission"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    workspace_id: str = Field(default="default", max_length=128, index=True)
    user_id: UUID
    auth_target_type: str = Field(default="", max_length=128, index=True)
    target: str = Field(default="", max_length=128, index=True)
    auth_type: str = Field(default="ROLE", max_length=128, index=True)
    permission_list: list = Field(default=[], sa_column=Column(ARRAY(String(256))))
