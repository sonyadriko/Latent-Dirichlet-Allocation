"""
Script untuk re-crawl project yang sudah ada untuk mendapatkan konten lengkap
Gunakan dengan hati-hati - akan menimpa data yang ada
"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crawler import CrawlerService

def recrawl_project(project_id):
    """Re-crawl semua URL dalam project untuk mendapatkan konten lengkap"""

    # Load projects
    projects_file = 'data/projects.json'
    with open(projects_file, 'r', encoding='utf-8') as f:
        projects = json.load(f)

    # Find project
    project = None
    project_index = -1
    for i, p in enumerate(projects):
        if p['id'] == project_id and p.get('status') == 'active':
            project = p
            project_index = i
            break

    if not project:
        print(f"Project dengan ID {project_id} tidak ditemukan atau sudah dihapus")
        return False

    print(f"Re-crawling project: {project['name']}")
    print(f"Jumlah URL: {len(project['source_urls'])}")

    # Initialize crawler
    crawler = CrawlerService()

    # Re-crawl semua URL
    print("Mulai crawling...")
    results = crawler.crawl_urls(project['source_urls'], delay=1)

    print(f"\nHasil crawling:")
    print(f"  Success: {results['success_count']}")
    print(f"  Failed: {results['failed_count']}")

    if results['success_count'] == 0:
        print("Gagal: Tidak ada URL yang berhasil di-crawl")
        return False

    # Update documents dengan content baru
    new_documents = []
    for doc in results['success']:
        new_documents.append({
            'id': doc['id'],
            'title': doc['title'],
            'url': doc['url'],
            'content_preview': doc['content']  # Full content
        })

    # Update project
    projects[project_index]['documents'] = new_documents
    projects[project_index]['document_count'] = len(new_documents)

    # Save projects
    with open(projects_file, 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Project berhasil di-update!")
    print(f"   Dokumen lama: {project['document_count']}")
    print(f"   Dokumen baru: {len(new_documents)}")

    # Update juga file di results folder
    project_folder = f"data/results/{project['name'].replace(' ', '_').lower()}"
    if os.path.exists(project_folder):
        docs_file = os.path.join(project_folder, 'documents.json')
        with open(docs_file, 'w', encoding='utf-8') as f:
            json.dump(new_documents, f, indent=2, ensure_ascii=False)
        print(f"[OK] File {docs_file} juga di-update")

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python recrawl_project.py <project_id>")
        print("Example: python recrawl_project.py 2")
        sys.exit(1)

    project_id = int(sys.argv[1])
    recrawl_project(project_id)
