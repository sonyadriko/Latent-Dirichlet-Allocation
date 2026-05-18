"""
Quick Debug Script for Manual Input KDD Pipeline
Run this to check database state and API endpoints
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import get_session, init_database
from repositories.document_repository import DocumentRepository
from repositories.project_repository import ProjectRepository


async def check_database():
    """Check database state"""
    print("=" * 60)
    print("DATABASE CHECK")
    print("=" * 60)

    try:
        async for session in get_session():
            # Check if tables exist
            result = await session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [row[0] for row in result.fetchall()]
            print(f"\n✓ Tables found: {', '.join(tables)}")

            # Check projects
            result = await session.execute(text("SELECT COUNT(*) FROM projects"))
            project_count = result.scalar()
            print(f"✓ Total projects: {project_count}")

            if project_count > 0:
                result = await session.execute(text(
                    "SELECT id, name, num_topics, document_count FROM projects ORDER BY id DESC LIMIT 5"
                ))
                print("\n  Recent projects:")
                for row in result.fetchall():
                    print(f"    - ID {row[0]}: {row[1]} ({row[3]} docs, {row[2]} topics)")

            # Check documents
            result = await session.execute(text("SELECT COUNT(*) FROM documents"))
            doc_count = result.scalar()
            print(f"\n✓ Total documents: {doc_count}")

            if doc_count > 0:
                result = await session.execute(text(
                    """SELECT d.id, d.title, d.project_id, LENGTH(d.content) as content_len
                       FROM documents d
                       ORDER BY d.id DESC
                       LIMIT 5"""
                ))
                print("\n  Recent documents:")
                for row in result.fetchall():
                    print(f"    - ID {row[0]}: {row[1][:50]}... (Project: {row[2]}, Content: {row[3]} chars)")

            # Check documents per project
            result = await session.execute(text(
                """SELECT project_id, COUNT(*) as doc_count
                   FROM documents
                   GROUP BY project_id
                   ORDER BY project_id"""
            ))
            print("\n  Documents per project:")
            for row in result.fetchall():
                print(f"    - Project {row[0]}: {row[1]} documents")

            print("\n" + "=" * 60)
            print("✓ Database check completed successfully")
            print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error checking database: {e}")
        import traceback
        traceback.print_exc()


async def test_document_operations(project_id=None):
    """Test document save and load operations"""
    print("\n" + "=" * 60)
    print("DOCUMENT OPERATIONS TEST")
    print("=" * 60)

    try:
        async for session in get_session():
            # Create test project if needed
            if project_id is None:
                print("\n→ Creating test project...")
                project = await ProjectRepository.create(
                    session=session,
                    name="Debug Test Project",
                    description="Auto-created for debugging",
                    num_topics=5,
                    document_count=0,
                    coherence_score=0.0,
                    created_by="debug_script"
                )
                await session.commit()
                await session.refresh(project)
                project_id = project.id
                print(f"✓ Test project created: ID {project_id}")
            else:
                print(f"\n→ Using existing project: ID {project_id}")

            # Create test documents
            print("\n→ Creating test documents...")
            test_docs = [
                {
                    "title": f"Debug Test Document {i}",
                    "content": f"This is test content for document {i}. " * 10
                }
                for i in range(1, 4)
            ]

            documents = await DocumentRepository.create_bulk(
                session=session,
                documents=test_docs,
                project_id=project_id
            )
            await session.commit()

            for doc in documents:
                await session.refresh(doc)

            print(f"✓ Created {len(documents)} test documents")
            for doc in documents:
                print(f"    - ID {doc.id}: {doc.title}")

            # Load documents back
            print(f"\n→ Loading documents for project {project_id}...")
            loaded_docs = await DocumentRepository.list_documents(
                session=session,
                project_id=project_id,
                limit=100,
                offset=0
            )

            print(f"✓ Loaded {len(loaded_docs)} documents")
            for doc in loaded_docs:
                print(f"    - ID {doc.id}: {doc.title} ({len(doc.content)} chars)")

            print("\n" + "=" * 60)
            print("✓ Document operations test completed successfully")
            print("=" * 60)

            return project_id

    except Exception as e:
        print(f"\n✗ Error testing document operations: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main debug function"""
    print("\n" + "=" * 60)
    print("MANUAL INPUT KDD PIPELINE - DEBUG SCRIPT")
    print("=" * 60)
    print(f"Time: 2026-05-18 16:00:51")
    print("=" * 60)

    # Initialize database
    print("\n→ Initializing database...")
    try:
        await init_database()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return

    # Check database state
    await check_database()

    # Ask user if they want to test operations
    print("\n" + "=" * 60)
    response = input("\nDo you want to test document operations? (y/n): ").strip().lower()

    if response == 'y':
        project_id_input = input("Enter project ID (or press Enter to create new): ").strip()
        project_id = int(project_id_input) if project_id_input else None

        test_project_id = await test_document_operations(project_id)

        if test_project_id:
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            print(f"✓ Test project ID: {test_project_id}")
            print(f"✓ You can now test the manual input page with this project")
            print(f"✓ URL: http://localhost:3030/manual-input")
            print("=" * 60)

    print("\n✓ Debug script completed\n")


if __name__ == "__main__":
    asyncio.run(main())
