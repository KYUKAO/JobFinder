#!/usr/bin/env python3
"""测试完整B站爬虫"""
import sys
sys.path.insert(0, 'scripts')

from updater import scrape_bilibili_portfolios

results = scrape_bilibili_portfolios()
print(f"\n最终结果: {len(results)} 个作品集")
if results:
    print(f"示例: {results[0]}")
