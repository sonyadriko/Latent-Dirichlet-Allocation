"""
Re-crawl semua URL sumber sebuah project untuk memperbarui konten dokumen.
Data lama diganti dengan hasil crawl terbaru.

Usage (dari project root):
    python scripts/recrawl_project.py <project_id>
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crawler import CrawlerService
from core.database import get_session_maker, init_database, close_database
from repositories.project_repository import ProjectRepository
from repositories.document_repository import DocumentRepository


async def recrawl_project(project_id: int) -> bool:
    await init_database()
    session_maker = get_session_maker()
    crawler = CrawlerService()

    async with session_maker() as session:
        # Load project from MySQL
        project = await ProjectRepository.get_by_id(session, project_id)
        if not project:
            print(f"Project dengan ID {project_id} tidak ditemukan")
            return False

        print(f"Re-crawling project: {project.name} (id={project.id})")

        # Source URLs are stored in the on-disk source_urls.txt
        from config import Config
        urls_file = os.path.join(
            Config.RESULTS_DIR,
            project.name.replace(' ', '_').lower(),
            'source_urls.txt'
        )

        if not os.path.exists(urls_file):
            print(f"source_urls.txt tidak ditemukan: {urls_file}")
            print("Project ini mungkin belum pernah di-crawl dari file TXT.")
            return False

        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            print("Tidak ada URL dalam source_urls.txt")
            return False

        print(f"Jumlah URL: {len(urls)}")

        # Re-crawl
        print("Mulai crawling...")
        results = crawler.crawl_urls(urls, delay=1)

        print(f"\nHasil crawling:")
        print(f"  Success: {results['success_count']}")
        print(f"  Failed:  {results['failed_count']}")

        if results['success_count'] == 0:
            print("Gagal: tidak ada URL yang berhasil di-crawl")
            return False

        # Replace documents in MySQL
        old_count = await DocumentRepository.count(session, project_id=project.id)
        await DocumentRepository.delete_by_project(session, project.id)

        new_docs = [
            {
                'title': doc['title'],
                'content': doc['content'],
                'url': doc['url'],
                'tokens_count': 0,
            }
            for doc in results['success']
        ]
        await DocumentRepository.create_bulk(session, documents=new_docs, project_id=project.id)

        # Keep document_count in sync
        new_count = len(new_docs)
        await ProjectRepository.update(session, project.id, document_count=new_count)
        await session.commit()

        # Also update the on-disk documents.json (used by lda_service corpus rebuild)
        project_folder = os.path.join(
            Config.RESULTS_DIR,
            project.name.replace(' ', '_').lower()
        )
        if os.path.exists(project_folder):
            import json
            docs_file = os.path.join(project_folder, 'documents.json')
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [{'title': d['title'], 'content': d['content'], 'url': d['url']} for d in new_docs],
                    f, indent=2, ensure_ascii=False
                )
            print(f"[OK] {docs_file} diperbarui")

        print(f"\n[OK] Project berhasil di-update!")
        print(f"   Dokumen lama: {old_count}")
        print(f"   Dokumen baru: {new_count}")

    await close_database()
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/recrawl_project.py <project_id>")
        print("Example: python scripts/recrawl_project.py 4")
        sys.exit(1)

    asyncio.run(recrawl_project(int(sys.argv[1])))
