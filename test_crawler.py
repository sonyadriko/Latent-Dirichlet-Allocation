from services.crawler import CrawlerService
import json

# Test crawler on one URL
url = "https://www.gramedia.com/products/eternal-love-1"
crawler = CrawlerService()

print("Testing crawler on:", url)
print("="*50)

result, error = crawler.crawl_url(url)

if error:
    print(f"Error: {error}")
else:
    print(f"Title: {result['title']}")
    print(f"Content Length: {len(result['content'])} characters")
    print(f"\nContent (first 500 chars):\n{result['content'][:500]}")
    print("\n" + "="*50)
    print("Expected to start with:")
    print('"Waktu tidak menyembuhkan apa pun. Lukanya masih ada, dan kenangannya masih sama."')

    # Save to file for inspection
    with open('test_crawl_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("\nFull result saved to: test_crawl_result.json")
