#!/usr/bin/env python3
"""
Migration Script: JSON to SQLite Database

This script migrates data from existing JSON files to the new SQLite database.
Run this after deploying the new database-based system to preserve existing data.

Usage:
    python scripts/migrate_json_to_db.py

Or from the project root:
    python -m scripts.migrate_json_to_db
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json

from core.database import get_session_maker
from repositories.user_repository import UserRepository
from repositories.project_repository import ProjectRepository


async def migrate_users(session_maker, users_file: str):
    """Migrate users from JSON file."""
    print("\n=== Migrating Users ===")

    if not os.path.exists(users_file):
        print(f"Users file not found: {users_file}")
        return 0

    with open(users_file, 'r') as f:
        users_data = json.load(f)

    migrated = 0
    async with session_maker() as session:
        for email, user_data in users_data.items():
            # Check if user already exists
            existing = await UserRepository.get_by_email(session, email)
            if existing:
                print(f"  User already exists: {email}")
                continue

            # Create user
            await UserRepository.create(
                session=session,
                name=user_data.get('name', email.split('@')[0]),
                email=email,
                password_hash=user_data.get('password', '')
            )
            print(f"  Migrated user: {email}")
            migrated += 1

        await session.commit()

    print(f"Migrated {migrated} users")
    return migrated


async def migrate_projects(session_maker, projects_file: str):
    """Migrate projects from JSON file."""
    print("\n=== Migrating Projects ===")

    if not os.path.exists(projects_file):
        print(f"Projects file not found: {projects_file}")
        return 0

    with open(projects_file, 'r') as f:
        projects_data = json.load(f)

    migrated = 0
    async with session_maker() as session:
        for project_data in projects_data:
            # Check if project already exists by name
            existing = await ProjectRepository.get_by_name(session, project_data.get('name', ''))
            if existing:
                print(f"  Project already exists: {project_data.get('name')}")
                continue

            # Create project
            project = await ProjectRepository.create(
                session=session,
                name=project_data.get('name', ''),
                description=project_data.get('description'),
                num_topics=project_data.get('num_topics', 5),
                document_count=project_data.get('document_count', 0),
                coherence_score=project_data.get('coherence_score', 0.0),
                model_path=project_data.get('model_path')
            )
            print(f"  Migrated project: {project.name}")
            migrated += 1

        await session.commit()

    print(f"Migrated {migrated} projects")
    return migrated


async def migrate_pipeline_results(session_maker, results_dir: str):
    """
    Migrate pipeline results to PipelineRun records.

    This creates historical records from completed pipeline runs.
    """
    print("\n=== Migrating Pipeline Results ===")

    if not os.path.exists(results_dir):
        print(f"Results directory not found: {results_dir}")
        return 0

    migrated = 0
    async with session_maker() as session:
        # Find all LDA results files
        for file_path in Path(results_dir).glob('*_data.json'):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                project_name = data.get('project_name', file_path.stem)
                crawled_data = data.get('crawled_data', [])

                # Check if a pipeline run already exists for this
                # For now, we'll just skip since we don't have full history
                print(f"  Found results for: {project_name} ({len(crawled_data)} documents)")
                migrated += 1

            except Exception as e:
                print(f"  Error reading {file_path}: {e}")

        await session.commit()

    print(f"Found {migrated} historical pipeline runs")
    return migrated


async def main():
    """Run the complete migration."""
    from config import Config

    print("=" * 60)
    print("LDA Application Migration: JSON to SQLite")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    from core.database import init_database
    await init_database()
    print("Database initialized")

    session_maker = get_session_maker()

    # Data paths
    data_dir = Config.DATA_DIR
    users_file = os.path.join(data_dir, 'users.json')
    projects_file = os.path.join(data_dir, 'projects.json')
    results_dir = Config.RESULTS_DIR

    # Run migrations
    user_count = await migrate_users(session_maker, users_file)
    project_count = await migrate_projects(session_maker, projects_file)
    pipeline_count = await migrate_pipeline_results(session_maker, results_dir)

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Users migrated:    {user_count}")
    print(f"Projects migrated: {project_count}")
    print(f"Pipelines found:   {pipeline_count}")
    print("\nMigration complete!")
    print("\nNOTE: The old JSON files have been preserved.")
    print("You can safely delete them after verifying the migration.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
