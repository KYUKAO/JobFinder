#!/usr/bin/env python3
"""通过BV号直接获取视频信息 - 测试"""
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

# 已知的TA相关视频BV号
KNOWN_BV_NUMS = [
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
    except Exception as e:
        print(f'Error: {e}')
        return None

print('测试通过BV号获取视频信息...')
for bv in KNOWN_BV_NUMS[:3]:
    info = get_video_info(bv)
    if info:
        print(f'{bv}: {info.get("title", "N/A")}')
    else:
        print(f'{bv}: 获取失败')

# 尝试通过视频详情页获取
print('\n测试视频详情API...')
url = 'https://api.bilibili.com/x/web-interface/view?bvid=BV1HSZ1YJEfW'
resp = session.get(url, timeout=10)
data = resp.json()
print(f"code: {data.get('code')}")
if data.get('code') == 0:
    info = data.get('data', {})
    print(f"title: {info.get('title')}")
    print(f"owner: {info.get('owner', {}).get('name')}")
