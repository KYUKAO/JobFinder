#!/usr/bin/env python3
"""通过相关推荐扩展搜索TA作品集 - 扩展版"""
import requests
import json
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

# 更多种子视频
SEED_VIDEOS = [
    'BV1HSZ1YJEfW', 'BV1L14y1R7dK', 'BV1Ga4y1Z7Jz', 'BV1fT4y1S7i9',
    'BV1oK4y1P7FL', 'BV1fN4y1D7gP', 'BV1vT4y1P7FL', 'BV1hK4y1P7FL',
    'BV1uT4y1P7FL', 'BV1AT4y1P7FL',  # 更多种子
]

def get_video_info(bvid):
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', {})
    except:
        pass
    return None

def get_related_videos(bvid):
    url = f'https://api.bilibili.com/x/web-interface/archive/related?bvid={bvid}'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', [])
    except:
        pass
    return []

TA_KEYWORDS = ['shader', 'render', 'vfx', '特效', 'unity', 'ue', 'unreal',
               'houdini', 'substance', '技术美术', 'ta', 'hlsl', 'glsl',
               'particle', '粒子', '蓝图', 'blueprint', 'material', '材质',
               'lighting', 'rendering', 'tutorial', '教程', '特效']

def main():
    portfolios = []
    seen_bvids = set()
    queue = list(SEED_VIDEOS)

    print('开始扩展搜索TA作品集...')

    for depth in range(3):
        print(f'\n--- 深度 {depth + 1} ---')
        next_queue = []

        for bvid in queue:
            if bvid in seen_bvids:
                continue
            seen_bvids.add(bvid)

            info = get_video_info(bvid)
            if not info:
                continue

            title = info.get('title', '')
            author = info.get('owner', {}).get('name', '')

            is_ta = any(kw.lower() in title.lower() for kw in TA_KEYWORDS)

            if is_ta:
                stat = info.get('stat', {})
                if bvid not in [p['bvid'] for p in portfolios]:
                    portfolios.append({
                        'bvid': bvid,
                        'title': title,
                        'author': author,
                        'description': info.get('desc', ''),
                        'duration': str(info.get('duration', 0)),
                        'views': stat.get('view', 0),
                        'category': 'TA',
                        'platform': 'bilibili',
                        'url': f'https://www.bilibili.com/video/{bvid}',
                        'addedDate': '2026-04-13',
                    })

            # 获取相关视频
            related = get_related_videos(bvid)
            for r in related:
                rbvid = r.get('bvid', '')
                if rbvid and rbvid not in seen_bvids:
                    next_queue.append(rbvid)

            time.sleep(0.3)

        queue = next_queue[:50]
        print(f'  已获取 {len(portfolios)} 个TA视频，队列 {len(queue)} 个')

    # 保存
    with open('portfolios.json', 'w', encoding='utf-8') as f:
        json.dump({
            'updated': '2026-04-13',
            'portfolios': portfolios
        }, f, ensure_ascii=False, indent=2)

    print(f'\n=== 最终获取 {len(portfolios)} 个TA作品集 ===')
    print('已保存到 portfolios.json')

if __name__ == '__main__':
    main()
