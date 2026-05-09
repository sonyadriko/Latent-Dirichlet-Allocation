import json
import sys

# Load data
with open('data/projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

projects = [p for p in data if p['id'] == 2]
if projects:
    doc = projects[0]['documents'][0]
    print(f"Title: {doc['title']}")
    print(f"Content Length: {len(doc['content_preview'])} characters")
    print(f"\nContent Preview (first 500 chars):\n{doc['content_preview'][:500]}")
    print("\n" + "="*50)
    print("Expected to start with:")
    print('"Waktu tidak menyembuhkan apa pun. Lukanya masih ada, dan kenangannya masih sama."')
else:
    print("Project not found")
