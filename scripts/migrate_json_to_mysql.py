#!/usr/bin/env python3
"""
Migration Script: legacy JSON + SQLite -> MySQL

Consolidates the old dual-storage data into the single MySQL database:
  - Users      from data/users.json        (a LIST of {id,name,email,password_hash})
  - Projects   from data/projects.json      (active only) + the old SQLite projects
  - Documents  from the old SQLite documents table (remapped to the MySQL project by name)

Idempotent (skip-if-exists) and non-destructive (legacy files are left untouched).

Usage (from project root, with MySQL env vars set):
    python scripts/migrate_json_to_mysql.py
"""
import sys
import os
import json
import sqlite3
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_session_maker, init_database
from repositories.user_repository import UserRepository
from repositories.project_repository import ProjectRepository
from repositories.document_repository import DocumentRepository


async def migrate_users(session_maker, users_file: str) -> int:
    print("\n=== Migrating Users ===")
    if not os.path.exists(users_file):
        print(f"  Users file not found: {users_file}")
        return 0

    with open(users_file, 'r', encoding='utf-8') as f:
        users_data = json.load(f)

    # users.json is a LIST of dicts
    if isinstance(users_data, dict):
        users_data = list(users_data.values())

    migrated = 0
    async with session_maker() as session:
        for u in users_data:
            email = u.get('email')
            if not email:
                continue
            if await UserRepository.get_by_email(session, email):
                print(f"  Skip existing user: {email}")
                continue
            await UserRepository.create(
                session=session,
                name=u.get('name') or email.split('@')[0],
                email=email,
                password_hash=u.get('password_hash') or u.get('password') or ''
            )
            print(f"  Migrated user: {email}")
            migrated += 1
        await session.commit()

    print(f"Users migrated: {migrated}")
    return migrated


def _load_sqlite_rows(sqlite_path: str, query: str) -> list:
    """Read rows from the old SQLite DB as a list of dicts (sync stdlib)."""
    if not os.path.exists(sqlite_path):
        return []
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


async def migrate_projects(session_maker, projects_file: str, sqlite_path: str) -> dict:
    """
    Consolidate projects from JSON + old SQLite (dedupe by name).
    Returns a mapping {project_name: mysql_project_id} for document remapping.
    """
    print("\n=== Migrating Projects ===")
    name_to_id: dict = {}

    # Gather candidates: JSON (active) first, then SQLite
    candidates = []
    if os.path.exists(projects_file):
        with open(projects_file, 'r', encoding='utf-8') as f:
            for p in json.load(f):
                if p.get('status', 'active') == 'active':
                    candidates.append(p)
    for p in _load_sqlite_rows(sqlite_path, "SELECT * FROM projects"):
        candidates.append(p)

    async with session_maker() as session:
        for p in candidates:
            name = p.get('name')
            if not name:
                continue
            existing = await ProjectRepository.get_by_name(session, name)
            if existing:
                name_to_id[name] = existing.id
                continue
            project = await ProjectRepository.create(
                session=session,
                name=name,
                description=p.get('description'),
                num_topics=p.get('num_topics', 5),
                document_count=p.get('document_count', 0),
                coherence_score=p.get('coherence_score', 0.0),
                model_path=p.get('model_path')
            )
            name_to_id[name] = project.id
            print(f"  Migrated project: {name} (id={project.id})")
        await session.commit()

    print(f"Projects available: {len(name_to_id)}")
    return name_to_id


async def migrate_documents(session_maker, sqlite_path: str, name_to_id: dict) -> int:
    """Migrate documents from old SQLite, remapping project_id by project name."""
    print("\n=== Migrating Documents ===")

    sqlite_projects = _load_sqlite_rows(sqlite_path, "SELECT id, name FROM projects")
    old_id_to_name = {p['id']: p['name'] for p in sqlite_projects}

    sqlite_docs = _load_sqlite_rows(sqlite_path, "SELECT * FROM documents")
    if not sqlite_docs:
        print("  No documents found in old SQLite database.")
        return 0

    # Group documents by target MySQL project id
    by_project: dict = {}
    for d in sqlite_docs:
        old_pid = d.get('project_id')
        pname = old_id_to_name.get(old_pid)
        new_pid = name_to_id.get(pname) if pname else None
        by_project.setdefault(new_pid, []).append({
            'title': d.get('title', ''),
            'content': d.get('content', ''),
            'url': d.get('url'),
            'tokens_count': d.get('tokens_count', 0),
            'dominant_topic': d.get('dominant_topic'),
            'dominant_prob': d.get('dominant_prob'),
        })

    migrated = 0
    async with session_maker() as session:
        for new_pid, docs in by_project.items():
            # Dedupe against what's already in the project (by title)
            existing_titles = set()
            if new_pid is not None:
                existing = await DocumentRepository.list_documents(session, project_id=new_pid, limit=100000)
                existing_titles = {e.title for e in existing}
            to_insert = [d for d in docs if d['title'] not in existing_titles]
            if not to_insert:
                continue
            await DocumentRepository.create_bulk(session, documents=to_insert, project_id=new_pid)
            migrated += len(to_insert)
            print(f"  Migrated {len(to_insert)} documents into project id={new_pid}")

        # Keep document_count in sync
        for new_pid in by_project:
            if new_pid is not None:
                count = await DocumentRepository.count(session, project_id=new_pid)
                await ProjectRepository.update(session, new_pid, document_count=count)
        await session.commit()

    print(f"Documents migrated: {migrated}")
    return migrated


async def main():
    from config import Config

    print("=" * 60)
    print("LDA Migration: legacy JSON + SQLite -> MySQL")
    print("=" * 60)

    print("\nInitializing MySQL schema...")
    await init_database()
    print("Schema ready")

    session_maker = get_session_maker()

    data_dir = Config.DATA_DIR
    users_file = os.path.join(data_dir, 'users.json')
    projects_file = os.path.join(data_dir, 'projects.json')
    old_sqlite = os.path.join(data_dir, 'lda_app.db')

    user_count = await migrate_users(session_maker, users_file)
    name_to_id = await migrate_projects(session_maker, projects_file, old_sqlite)
    doc_count = await migrate_documents(session_maker, old_sqlite, name_to_id)

    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Users migrated:     {user_count}")
    print(f"Projects available: {len(name_to_id)}")
    print(f"Documents migrated: {doc_count}")
    print("\nLegacy JSON/SQLite files were left untouched (backup).")
    print("=" * 60)

    # Explicitly close the engine so aiomysql connections are released
    # before the event loop closes — prevents the harmless __del__ warning.
    from core.database import close_database
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
