import sys
sys.path.insert(0, 'scripts')
from updater import DATA_DIR, save_json, scrape_bilibili_portfolios
import json
import os

print('当前工作目录:', os.getcwd())
print('DATA_DIR:', DATA_DIR)

# 直接保存到当前目录
results = scrape_bilibili_portfolios()
print(f'爬取到 {len(results)} 个作品集')

if results:
    data = {'updated': '2026-04-13', 'portfolios': results}
    with open('portfolios.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('已保存到 portfolios.json')
else:
    print('没有数据')
