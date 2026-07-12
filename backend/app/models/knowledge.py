"""knowledge app tables (RAG).

FK columns are stored as plain ids (legacy models used db_constraint=False ->
no DB-level foreign keys). `embedding` uses pgvector; MPTT folder columns are
retained for schema compatibility and queried via parent_id + PG WITH RECURSIVE.
"""

from datetime import datetime
from uuid import UUID

import uuid_utils.compat as uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlmodel import Field

from app.models.base import AppTableBase


class KnowledgeFolder(AppTableBase, table=True):
    __tablename__ = "knowledge_folder"
    id: str = Field(default_factory=lambda: str(uuid.uuid7()), max_length=64, primary_key=True)
    name: str = Field(default="", max_length=64, index=True)
    desc: str | None = Field(default=None, max_length=200)
    user_id: UUID | None = Field(default=None)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    parent_id: str | None = Field(default=None, max_length=64)
    # MPTT columns retained for compatibility.
    tree_id: int = Field(default=0)
    level: int = Field(default=0)
    lft: int = Field(default=0)
    rght: int = Field(default=0)


class Knowledge(AppTableBase, table=True):
    __tablename__ = "knowledge"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    name: str = Field(default="", max_length=150, index=True)
    workspace_id: str = Field(default="default", max_length=64, index=True)
    desc: str = Field(default="", max_length=256)
    user_id: UUID | None = Field(default=None)
    type: int = Field(default=0, index=True)
    scope: str = Field(default="WORKSPACE", max_length=20, index=True)
    folder_id: str = Field(default="default", max_length=64)
    embedding_model_id: UUID | None = Field(default=None)
    file_size_limit: int = Field(default=100)
    file_count_limit: int = Field(default=50)
    meta: dict = Field(default={}, sa_column=Column(JSONB))


class KnowledgeWorkflow(AppTableBase, table=True):
    __tablename__ = "knowledge_workflow"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    workspace_id: str = Field(default="default", max_length=64, index=True)
    work_flow: dict = Field(default={}, sa_column=Column(JSONB))
    is_publish: bool = Field(default=False, index=True)
    publish_time: datetime | None = Field(default=None)


class KnowledgeWorkflowVersion(AppTableBase, table=True):
    __tablename__ = "knowledge_workflow_version"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    workspace_id: str = Field(default="default", max_length=64, index=True)
    name: str = Field(default="", max_length=128)
    work_flow: dict = Field(default={}, sa_column=Column(JSONB))
    publish_user_id: UUID | None = Field(default=None)
    publish_user_name: str = Field(default="", max_length=128)


class Document(AppTableBase, table=True):
    __tablename__ = "document"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    name: str = Field(default="", max_length=150, index=True)
    char_length: int = Field(default=0)
    status: str = Field(default="", max_length=20, index=True)
    status_meta: dict = Field(default={}, sa_column=Column(JSONB))
    user_id: UUID | None = Field(default=None)
    is_active: bool = Field(default=True, index=True)
    type: int = Field(default=0, index=True)
    hit_handling_method: str = Field(default="optimization", max_length=20)
    directly_return_similarity: float = Field(default=0.9)
    meta: dict = Field(default={}, sa_column=Column(JSONB))


class Tag(AppTableBase, table=True):
    __tablename__ = "tag"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    key: str = Field(default="", max_length=64, index=True)
    value: str = Field(default="", max_length=128, index=True)


class DocumentTag(AppTableBase, table=True):
    __tablename__ = "document_tag"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    document_id: UUID
    tag_id: UUID


class Paragraph(AppTableBase, table=True):
    __tablename__ = "paragraph"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    document_id: UUID
    knowledge_id: UUID
    content: str = Field(default="", max_length=102400)
    title: str = Field(default="", max_length=256, index=True)
    status: str = Field(default="", max_length=20, index=True)
    status_meta: dict = Field(default={}, sa_column=Column(JSONB))
    hit_num: int = Field(default=0)
    is_active: bool = Field(default=True, index=True)
    position: int = Field(default=0, index=True)
    chunks: list = Field(default=[], sa_column=Column(ARRAY(String)))


class Problem(AppTableBase, table=True):
    __tablename__ = "problem"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    content: str = Field(default="", max_length=256, index=True)
    hit_num: int = Field(default=0)


class ProblemParagraphMapping(AppTableBase, table=True):
    __tablename__ = "problem_paragraph_mapping"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    document_id: UUID
    problem_id: UUID
    paragraph_id: UUID


class Termbase(AppTableBase, table=True):
    __tablename__ = "termbase"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    knowledge_id: UUID
    content: str = Field(default="", max_length=256, index=True)


class Embedding(AppTableBase, table=True):
    __tablename__ = "embedding"
    id: str = Field(max_length=128, primary_key=True)
    source_id: str = Field(default="", max_length=128, index=True)
    source_type: str = Field(default="0", max_length=5, index=True)
    is_active: bool = Field(default=True)
    knowledge_id: UUID = Field()
    document_id: UUID = Field()
    paragraph_id: UUID = Field()
    embedding: list = Field(sa_column=Column(Vector(1536)))
    search_vector: str = Field(sa_column=Column(TSVECTOR))
    meta: dict = Field(default={}, sa_column=Column(JSONB))


class File(AppTableBase, table=True):
    __tablename__ = "file"
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    file_name: str = Field(default="", max_length=256)
    file_size: int = Field(default=0)
    sha256_hash: str = Field(default="")
    source_type: str = Field(default="TEMPORARY_120_MINUTE", max_length=256, index=True)
    source_id: str = Field(default="TEMPORARY_120_MINUTE", max_length=256, index=True)
    loid: int = Field(default=0)
    meta: dict = Field(default={}, sa_column=Column(JSONB))
