#!/usr/bin/env python3
"""通过已知视频扩展搜索TA相关作品集"""
import requests
import json
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

# 种子视频 - 已知的TA相关视频
SEED_VIDEOS = [
    'BV1HSZ1YJEfW',  # Unreal5 HLSL教程
    'BV1L14y1R7dK',  # Houdini教程
    'BV1Ga4y1Z7Jz',  # Shader教程
    'BV1fT4y1S7i9',  # 游戏特效教程
    'BV1oK4y1P7FL',  # UE特效教程
    'BV1fN4y1D7gP',  # Unity特效
    'BV1vT4y1P7FL',  # 技术美术
    'BV1hK4y1P7FL',  # 渲染教程
]

def get_video_info(bvid):
    """通过BV号获取视频信息"""
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', {})
        return None
    except:
        return None

def get_related_videos(bvid):
    """获取相关推荐视频"""
    url = f'https://api.bilibili.com/x/web-interface/archive/related?bvid={bvid}'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', [])
        return []
    except:
        return []

def main():
    portfolios = []
    seen_bvids = set()
    queue = list(SEED_VIDEOS)

    print('开始通过相关推荐扩展搜索TA作品集...')
    max_depth = 2  # 搜索深度

    for depth in range(max_depth):
        print(f'\n--- 深度 {depth + 1} ---')
        next_queue = []

        for bvid in queue:
            if bvid in seen_bvids:
                continue
            seen_bvids.add(bvid)

            info = get_video_info(bvid)
            if not info:
                continue

            # 检查是否是TA相关视频
            title = info.get('title', '')
            author = info.get('owner', {}).get('name', '')
            tname = info.get('tname', '')  # 分区名

            # TA相关关键词
            TA_KEYWORDS = ['shader', '渲染', '特效', 'vfx', 'unity', 'ue', 'unreal',
                          'houdini', 'substance', '技术美术', 'ta', '图形', 'hlsl',
                          'particle', '粒子', '蓝图', 'blueprint', 'material', '材质',
                          'lighting', 'rendering', '特效', 'tutorial', '教程']

            is_ta = any(kw.lower() in title.lower() for kw in TA_KEYWORDS)

            if is_ta:
                stat = info.get('stat', {})
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
                print(f'  [TA] {title[:40]}...')

            # 获取相关视频
            related = get_related_videos(bvid)
            for r in related:
                rbvid = r.get('bvid', '')
                if rbvid and rbvid not in seen_bvids:
                    next_queue.append(rbvid)

            time.sleep(0.5)

        queue = next_queue[:30]  # 限制队列大小
        print(f'  本轮发现 {len(portfolios)} 个TA相关视频')

    # 去重
    seen = set()
    unique_portfolios = []
    for p in portfolios:
        if p['bvid'] not in seen:
            seen.add(p['bvid'])
            unique_portfolios.append(p)

    print(f'\n总共获取 {len(unique_portfolios)} 个TA相关作品集')

    # 保存
    with open('portfolios.json', 'w', encoding='utf-8') as f:
        json.dump({
            'updated': '2026-04-13',
            'portfolios': unique_portfolios
        }, f, ensure_ascii=False, indent=2)
    print('已保存到 portfolios.json')

    # 显示示例
    print('\n示例视频:')
    for p in unique_portfolios[:5]:
        print(f"  - {p['title']} by {p['author']}")

if __name__ == '__main__':
    main()
