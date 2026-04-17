#!/usr/bin/env python3
"""使用B站各分区排行榜获取TA相关视频 - 改进版"""
import requests
import json
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

# 更宽松的TA相关关键词
TA_KEYWORDS = [
    'shader', '渲染', '特效', 'vfx', 'unity', 'ue4', 'ue5', 'unreal',
    'houdini', 'substance', '技术美术', 'ta', '图形', 'hlsl', 'glsl',
    'particle', '粒子', '蓝图', 'blueprint', 'material', '材质',
    'lighting', '光照', 'rendering', 'render pipeline',
    '游戏', '特效', '程序化', '美术', 'animation', 'anim',
]

def get_category_rank(category_id, category_name):
    """获取分区排行榜"""
    url = f'https://api.bilibili.com/x/web-interface/ranking/v2?rid={category_id}&type=all'
    try:
        resp = session.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            videos = data.get('data', {}).get('list', [])
            return videos
        return []
    except Exception as e:
        return []

def is_ta_related(title):
    """检查标题是否与TA相关"""
    title_lower = title.lower()
    # 降低匹配要求
    for kw in TA_KEYWORDS:
        if kw.lower() in title_lower:
            return True
    return False

def main():
    # 游戏区相关分类
    categories = [
        (36, '游戏综合'),
        (47, '射击游戏'),
        (59, '单机游戏'),
        (65, '视频攻略'),
    ]

    all_portfolios = []

    print('开始获取B站各分区排行榜...')

    for cat_id, cat_name in categories:
        print(f'正在获取 {cat_name} 分区...')
        videos = get_category_rank(cat_id, cat_name)
        print(f'  该分区共 {len(videos)} 个视频')

        for v in videos:
            title = v.get('title', '')
            bvid = v.get('bvid', '')

            if is_ta_related(title):
                stat = v.get('stat', {})
                all_portfolios.append({
                    'bvid': bvid,
                    'title': title,
                    'author': v.get('owner', {}).get('name', ''),
                    'description': v.get('desc', ''),
                    'duration': str(v.get('duration', 0)),
                    'views': stat.get('view', 0),
                    'category': 'TA',
                    'platform': 'bilibili',
                    'url': f'https://www.bilibili.com/video/{bvid}',
                    'addedDate': '2026-04-13',
                })

        print(f'  {cat_name}: 发现 {len([v for v in videos if is_ta_related(v.get("title", ""))])} 个TA相关视频')
        time.sleep(1)

    # 去重
    seen = set()
    unique_portfolios = []
    for p in all_portfolios:
        if p['bvid'] not in seen:
            seen.add(p['bvid'])
            unique_portfolios.append(p)

    print(f'\n总共获取 {len(unique_portfolios)} 个TA相关作品集')

    # 保存
    if unique_portfolios:
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
    else:
        print('\n没有找到TA相关视频，保存空数据...')
        with open('portfolios.json', 'w', encoding='utf-8') as f:
            json.dump({
                'updated': '2026-04-13',
                'portfolios': []
            }, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
