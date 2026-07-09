"""Model-provider schemas."""

from __future__ import annotations

import uuid

from sqlmodel import SQLModel


class ModelCreate(SQLModel):
    name: str
    model_type: str
    model_name: str
    provider: str
    credential: str = ""
    status: str = "SUCCESS"
    workspace_id: str = "default"
    meta: dict = {}
    model_params_form: list = []


class ModelOut(SQLModel):
    id: uuid.UUID
    name: str
    model_type: str
    model_name: str
    provider: str
    status: str = "SUCCESS"
    workspace_id: str = "default"
    user_id: uuid.UUID | None = None


class CredentialField(SQLModel):
    field: str
    label: str
    input_type: str = "password"
    required: bool = True
    default_value: str = ""
    props: dict = {}


class ProviderInfo(SQLModel):
    provider: str
    name: str
    model_types: list[str] = []
    auth_type: str = "api_key"
    base_url: str = ""
    credential_form: list[CredentialField] = []
