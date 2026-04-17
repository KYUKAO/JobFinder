#!/usr/bin/env python3
"""测试哪些B站关键字能用"""
import requests
from urllib.parse import quote_plus

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json',
})

keywords = [
    'shader', 'HLSL', 'GLSL', 'Unity渲染', 'UE渲染', '渲染引擎',
    '游戏特效', 'Unity特效', 'UE特效', 'VFX', '粒子特效',
    '技术美术', '游戏TA', '图形程序', 'TA教程',
    'substance designer', 'houdini程序化', '程序化生成',
    '游戏美术', 'Maya脚本', 'Python脚本',
    # 英文关键字
    'Unity shader', 'Unreal shader', 'game vfx',
    # 更多中文
    'ue5教程', 'unity教程', '地编教程', '场景美术',
    '角色绑定', '动画特效', '蓝图脚本',
]

working = []
blocked = []

for kw in keywords:
    try:
        url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={quote_plus(kw)}&page=1'
        resp = session.get(url, timeout=10)
        data = resp.json()

        if data.get('code') == 0:
            videos = data.get('data', {}).get('result', [])
            working.append(kw)
            print(f"[OK] {kw}: {len(videos)} videos")
        else:
            blocked.append(kw)
            print(f"[X] {kw}: {data.get('message')}")
    except Exception as e:
        print(f"[E] {kw}: {e}")

print("\n--- 结果 ---")
print(f"能用: {working}")
print(f"被封: {blocked}")
