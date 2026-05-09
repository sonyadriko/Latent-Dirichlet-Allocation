from services.crawler import CrawlerService
import json

# Test crawler on one URL
url = "https://www.gramedia.com/products/eternal-love-1"
crawler = CrawlerService()

result, error = crawler.crawl_url(url)

# Save to file
with open('crawl_output.txt', 'w', encoding='utf-8') as f:
    if error:
        f.write(f"Error: {error}\n")
    else:
        f.write(f"Title: {result['title']}\n")
        f.write(f"Content Length: {len(result['content'])} characters\n")
        f.write(f"\nContent:\n{result['content']}\n")
        f.write(f"\n\nExpected to start with:\n")
        f.write('"Waktu tidak menyembuhkan apa pun. Lukanya masih ada, dan kenangannya masih sama."\n')

print("Result saved to: crawl_output.txt")
