#!/usr/bin/env python3
"""测试所有招聘网站URL的有效性"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 国内公司招聘页面
DOMESTIC_COMPANIES = [
    {'name': '盛趣游戏', 'url': 'http://www.sqgame.com/about/join'},
    {'name': '朝夕光年', 'url': 'http://careers.bytedance.com/chinese'},
    {'name': '吉比特', 'url': 'http://www.lilith.com/careers/'},
    {'name': '腾讯游戏', 'url': 'https://careers.tencent.com/search.html?query=TA'},
    {'name': '腾讯招聘(主站)', 'url': 'https://careers.tencent.com/'},
    {'name': '网易游戏', 'url': 'https://game.163.com/hr/positions'},
    {'name': '米哈游', 'url': 'https://jobs.mihoyo.com'},
    {'name': '字节跳动游戏', 'url': 'https://job.bytedance.com/technology'},
    {'name': '莉莉丝游戏', 'url': 'https://www.lilith.com/careers/'},
    {'name': '鹰角网络', 'url': 'https://www.yostar.com/careers/'},
    {'name': '完美世界', 'url': 'https://www.wanmei.com/hr/'},
    {'name': '37互娱', 'url': 'https://www.37.com/hr/'},
    {'name': 'FunPlus', 'url': 'https://www.funplus.com/careers/'},
    {'name': '叠纸游戏', 'url': 'https://www.papergames.cn/careers'},
    {'name': 'IGG', 'url': 'https://www.igg.com/jobs'},
]

# 备选URL（如果主URL失效）
ALTERNATIVE_URLS = {
    '盛趣游戏': [
        'https://www.shengqugames.com/hr/',
        'https://www.sqgame.com/join',
    ],
    '朝夕光年': [
        'https://bytedance.jobs.com/',
    ],
    '吉比特': [
        'https://www.g-bits.com/careers/',
        'https://www.lilithgame.com/careers',
    ],
    '腾讯游戏': [
        'https://careers.tencent.com/search.html?query=Technical+Artist',
    ],
    '莉莉丝游戏': [
        'https://lilithgame.com/careers',
    ],
    '鹰角网络': [
        'https://hypergryph.com/careers',
    ],
    'IGG': [
        'https://www.igg.com/about/jobs',
    ],
}

# 海外工作室
OVERSEAS_STUDIOS = [
    {'name': 'Riot Games', 'url': 'https://www.riotgames.com/en/work-with-us'},
    {'name': 'Epic Games', 'url': 'https://www.epicgames.com/site/en-US/careers'},
    {'name': 'Bungie', 'url': 'https://careers.bungie.com/'},
    {'name': 'Rockstar Games', 'url': 'https://www.rockstargames.com/careers'},
    {'name': 'Activision', 'url': 'https://www.activision.com/careers'},
    {'name': 'Naughty Dog', 'url': 'https://www.naughtydog.com/careers'},
    {'name': 'PlayStation Studios', 'url': 'https://careers.playstation.com/'},
    {'name': 'Santa Monica Studio', 'url': 'https://www.sms.playstation.com/careers'},
    {'name': 'Insomniac Games', 'url': 'https://careers.insomniac.games/'},
    {'name': 'Ubisoft', 'url': 'https://www.ubisoft.com/en-us/careers'},
]

# LinkedIn 和 Indeed
JOB_BOARDS = [
    {'name': 'LinkedIn', 'url': 'https://www.linkedin.com/jobs/search/?keywords=technical+artist'},
    {'name': 'Indeed', 'url': 'https://www.indeed.com/jobs?q=technical+artist'},
]

def check_url(name, url, timeout=10):
    """检查单个URL"""
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True,
                          headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        status = resp.status_code
        if status == 200:
            # 检查是否真的是404页面
            if '404' in resp.text[:500] or 'not found' in resp.text[:500].lower():
                return (name, url, status, '可能是404页面')
            return (name, url, status, 'OK')
        elif status in (301, 302, 303, 307, 308):
            return (name, url, status, f'重定向到: {resp.url}')
        else:
            return (name, url, status, '失败')
    except requests.exceptions.SSLError as e:
        return (name, url, 'SSL', f'SSL错误: {str(e)[:50]}')
    except requests.exceptions.ConnectionError as e:
        return (name, url, 'CONN', f'连接错误')
    except requests.exceptions.Timeout:
        return (name, url, 'TIMEOUT', '超时')
    except Exception as e:
        return (name, url, 'ERROR', str(e)[:50])

def test_all_urls():
    print('=' * 60)
    print('测试国内游戏公司招聘页面')
    print('=' * 60)

    all_sites = DOMESTIC_COMPANIES + OVERSEAS_STUDIOS + JOB_BOARDS

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_url, site['name'], site['url']): site for site in all_sites}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # 按状态分类
    ok_results = []
    bad_results = []

    for name, url, status, msg in sorted(results, key=lambda x: str(x[1])):
        status_icon = '[OK]' if status == 200 and msg == 'OK' else '[FAIL]'
        if status == 200 and msg == 'OK':
            ok_results.append((name, url, status, msg))
            print(f'{status_icon} {name}: {status} - OK')
        else:
            bad_results.append((name, url, status, msg))
            print(f'{status_icon} {name}: {status} - {msg}')

    print()
    print('=' * 60)
    print(f'统计: {len(ok_results)} 正常, {len(bad_results)} 需要修复')
    print('=' * 60)

    if bad_results:
        print('\n需要修复的网站:')
        for name, url, status, msg in bad_results:
            print(f'  - {name}: {url}')
            if name in ALTERNATIVE_URLS:
                print(f'    备选: {ALTERNATIVE_URLS[name]}')

if __name__ == '__main__':
    test_all_urls()
