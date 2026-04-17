import updater
updater.DATA_DIR = '..'
updater.TODAY_STR = '2026-04-18'
p = updater.scrape_bilibili_by_search()
print(f'Got {len(p)} portfolios')
for x in p[:5]:
    title = x.get('title', '')[:40]
    print(f'  - {title} by {x.get("author", "")}')
