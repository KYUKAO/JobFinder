#!/usr/bin/env python3
"""使用B站UP主API获取TA作品集"""
import requests
import json
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
})

# TA相关的知名UP主 (待补充)
TA_UP_MASTERS = [
    # UID, UP主名
    (302476761, 'TA_元桑'),  # TA技术美术
    (497055838, '特效卡车司机'),  # 游戏特效
    (6903596, '光之守望'),  # Unity/UE
    # 可以继续添加更多
]

def get_up_videos(uid, page=1):
    """获取UP主的视频列表"""
    url = f'https://api.bilibili.com/x/space/wbi/arc/search?mid={uid}&pn={page}&jsonp=jsonp'
    try:
        resp = session.get(url, timeout=15)
        data = resp.json()
        if data.get('code') == 0:
            return data.get('data', {}).get('list', {}).get('vlist', [])
        return []
    except Exception as e:
        print(f'Error: {e}')
        return []

# 先测试一个UP主
uid = 302476761
print(f'测试UP主: {uid}')
videos = get_up_videos(uid)
print(f'获取到 {len(videos)} 个视频')
if videos:
    print(f'示例: {videos[0].get("title", "N/A")}')
