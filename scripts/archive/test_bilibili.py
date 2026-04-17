#!/usr/bin/env python3
"""测试B站API - 详细调试"""
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json',
}

urls = [
    'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=TA%E6%8A%80%E6%9C%AF%E7%BE%8E%E6%9C%AF',
    'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=shader',
]

for i, url in enumerate(urls):
    print(f"\n--- 测试URL {i+1} ---")
    print(f"URL: {url[:80]}...")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {resp.status_code}")
        print(f"Headers: {dict(resp.headers)}")
        print(f"Content (first 500 chars): {resp.text[:500]}")

        if resp.text.strip():
            data = resp.json()
            print(f"JSON code: {data.get('code')}")
    except Exception as e:
        print(f"Error: {e}")
