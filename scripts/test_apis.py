#!/usr/bin/env python3
"""测试B站不同的API接口"""
import requests
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

# 方法1: 话题标签 API
def test_tag_api():
    print("\n=== 测试话题标签API ===")
    url = 'https://api.bilibili.com/x/tag/archive/tags?rid=0&type=arc&pn=1&ps=20&tag_name=shader'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        print(f"code: {data.get('code')}")
        if data.get('code') == 0:
            print(f"成功: {len(data.get('data', []))} 条")
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

# 方法2: 热门视频
def test_rank_api():
    print("\n=== 测试排行榜API ===")
    url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        print(f"code: {data.get('code')}")
        if data.get('code') == 0:
            video_list = data.get('data', {}).get('list', [])
            print(f"成功: {len(video_list)} 个视频")
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

# 方法3: 直接搜索 (带延迟测试)
def test_search_with_delay():
    print("\n=== 测试搜索API(带延迟) ===")
    keywords = ['UE渲染', 'VFX']
    for kw in keywords:
        url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={kw}'
        try:
            resp = session.get(url, timeout=10)
            data = resp.json()
            code = data.get('code')
            if code == 0:
                videos = data.get('data', {}).get('result', [])
                print(f"[{kw}] 成功: {len(videos)} 个视频")
            else:
                print(f"[{kw}] code={code}: {data.get('message')}")
        except Exception as e:
            print(f"[{kw}] Error: {e}")
        time.sleep(3)  # 3秒延迟

# 运行测试
test_tag_api()
test_rank_api()
test_search_with_delay()
