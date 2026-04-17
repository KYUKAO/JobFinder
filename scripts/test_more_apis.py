#!/usr/bin/env python3
"""使用B站多个API端点获取更多视频"""
import requests
import json
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

def test_different_apis():
    """测试不同的API"""
    results = []

    # API 1: 全站排行榜
    print("\n=== 全站排行榜 ===")
    url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            videos = data.get('data', {}).get('list', [])
            print(f"获取到 {len(videos)} 个视频")
            results.extend([(v.get('bvid'), v.get('title'), v.get('owner', {}).get('name')) for v in videos])
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)

    # API 2: 热门视频流
    print("\n=== 热门视频流 ===")
    url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            videos = data.get('data', {}).get('list', [])
            print(f"获取到 {len(videos)} 个视频")
            for v in videos:
                results.append((v.get('bvid'), v.get('title'), v.get('owner', {}).get('name')))
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)

    # API 3: 全站分区
    print("\n=== 全站分区排行榜 ===")
    for rid in [1, 3, 4, 5, 11, 13, 23, 36, 119]:
        url = f'https://api.bilibili.com/x/web-interface/ranking/v2?rid={rid}&type=all'
        try:
            resp = session.get(url, timeout=10)
            data = resp.json()
            if data.get('code') == 0:
                videos = data.get('data', {}).get('list', [])
                print(f"rid={rid}: {len(videos)} 个视频")
                for v in videos:
                    results.append((v.get('bvid'), v.get('title'), v.get('owner', {}).get('name')))
            time.sleep(0.5)
        except Exception as e:
            print(f"rid={rid} Error: {e}")

    # 去重
    seen = set()
    unique = []
    for bvid, title, author in results:
        if bvid and bvid not in seen:
            seen.add(bvid)
            unique.append({'bvid': bvid, 'title': title, 'author': author})

    print(f"\n总共获取 {len(unique)} 个视频")

    # TA相关关键词
    TA_KEYWORDS = ['shader', '渲染', '特效', 'vfx', 'unity', 'ue', 'unreal',
                   'houdini', 'substance', '技术美术', 'ta', '图形', 'hlsl',
                   'particle', '粒子', '蓝图', 'blueprint', 'material', '材质']

    ta_videos = [v for v in unique if any(kw.lower() in v['title'].lower() for kw in TA_KEYWORDS)]

    print(f"TA相关视频: {len(ta_videos)} 个")
    for v in ta_videos[:10]:
        print(f"  - {v['title']}")

    return ta_videos

if __name__ == '__main__':
    results = test_different_apis()
