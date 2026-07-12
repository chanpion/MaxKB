"""One-time script to create missing database tables for development/testing.

Run from the backend directory: python init_tables.py
"""
import asyncio
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SERVER_NAME", "web")

# Import all models to register them in SQLModel.metadata
from app.models.application import Application, ApplicationFolder, ApplicationKnowledgeMapping, ApplicationVersion, ApplicationAccessToken, ApplicationApiKey, Chat, ChatRecord, ChatShareLink, ApplicationChatUserStats, ApplicationLongTermMemory  # noqa: F401
from app.models.knowledge import Knowledge, KnowledgeFolder, KnowledgeWorkflow, KnowledgeWorkflowVersion, Document, Paragraph, Tag, DocumentTag, Problem, ProblemParagraphMapping, Termbase, Embedding, File  # noqa: F401
from app.models.tool import Tool, ToolFolder, ToolRecord, ToolWorkflow, ToolWorkflowVersion  # noqa: F401
from app.models.trigger import Trigger, TriggerTask, TaskRecord  # noqa: F401
from app.models.system import SystemSetting, ChatUser, UserGroup, UserGroupRelation, ResourceChatUserAuthorize, ResourceChatUserGroupAuthorize, Log, ResourceMapping, WorkspaceUserResourcePermission  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.models_provider import Model  # noqa: F401

from app.core.db import engine
from sqlmodel import SQLModel
from sqlalchemy import text


async def main():
    async with engine.begin() as conn:
        # Try to install pgvector extension
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("pgvector extension enabled")
        except Exception as e:
            print(f"pgvector not available: {e}")

        # Show tables before
        result = await conn.execute(text(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))
        before = set(r[0] for r in result.fetchall())

        # Create tables one by one, skip those that fail
        all_tables = list(SQLModel.metadata.sorted_tables)
        created = []
        failed = []

        for table in all_tables:
            if table.name in before:
                continue
            try:
                await conn.run_sync(table.create)
                created.append(table.name)
                print(f"  OK: {table.name}")
            except Exception as e:
                failed.append((table.name, str(e)[:120]))
                print(f"  SKIP: {table.name} — {str(e)[:100]}")

        result = await conn.execute(text(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))
        after = set(r[0] for r in result.fetchall())

        print(f"\nBefore: {len(before)} tables")
        print(f"Created: {len(created)} tables")
        print(f"Failed: {len(failed)} tables")
        print(f"After: {len(after)} tables")

        if failed:
            print("\nSkipped (need pgvector extension or have dependency issues):")
            for name, err in failed:
                print(f"  - {name}")


if __name__ == "__main__":
    asyncio.run(main())
