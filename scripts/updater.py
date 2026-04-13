#!/usr/bin/env python3
"""
TA Job Finder — 数据更新主脚本 v3.0
- 数据与框架完全分离（JSON 配置文件）
- 经验等级分类：实习/1年/1-3年/3-5年/5年+
- 国内不爬 5年+，国外爬 senior
- 截止日期（deadline）计算
- 智能分析摘要：热门岗位 + 最低要求
"""

import json, re, os, time, random
from datetime import date, timedelta
from urllib.parse import quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

TODAY = date.today()
TODAY_STR = TODAY.isoformat()
REPO_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/..'
DATA_DIR = REPO_ROOT

def log(msg):
    print(f'[updater] {msg}')

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================================================================
# 经验等级分类
# ================================================================
EXPERIENCE_LEVELS = ['intern', 'entry', 'mid', 'senior', 'lead']

def classify_experience(title, jd=''):
    """判断经验等级"""
    t = (title + ' ' + jd).lower()
    if any(k in t for k in ['intern', 'student', 'trainee', '实习', '试用期', '应届', '毕业生', '校招']):
        return 'intern'
    if any(k in t for k in ['lead', 'director', 'principal', 'head', 'manager', '专家', '资深']):
        return 'lead'
    if any(k in t for k in ['senior', 'sr.', 'sr ', '资深', '5-10', '5年', '6年', '7年', '8年', '9年', '10年']):
        return 'senior'
    if any(k in t for k in ['1-3', '1-5', '2-5', '3-5', '三年', '1年', '2年']):
        return 'mid'
    if any(k in t for k in ['1年', '一年', '经验不限', '不限经验', '0-1']):
        return 'entry'
    return 'mid'  # 默认

def should_skip_by_experience(title, region='domestic'):
    """国内跳过 5 年+ 岗位"""
    t = title.lower()
    if region == 'domestic':
        if any(k in t for k in ['8年', '10年', '10 年', '12年', '15年']):
            return True
    return False

# ================================================================
# TA 细分分类
# ================================================================
TA_KEYWORDS = {
    'character':  ['character', 'char', 'skinning', 'rigging', 'deformation', 'skeleton', 'blend shape', '角色', '角色绑定'],
    'environment':['environment', 'env', 'terrain', 'foliage', 'world', 'prop', 'asset', '场景', '关卡美术', '世界构建'],
    'rendering':  ['rendering', 'shader', 'hlsl', 'glsl', 'cg', 'lighting', 'vfx', 'visual effect', 'graphics', 'ray', 'render', '渲染', '着色器', '光照'],
    'pipeline':   ['pipeline', 'tool', 'automation', 'dcc', 'maya script', 'python script', 'workflow', '流程', '工具开发', '自动化'],
    'ui':         ['ui', 'ux', 'hud', 'interface', 'menu', 'user interface', 'screen', '界面', '交互'],
}

def classify_ta_sub(title, jd=''):
    text = (title + ' ' + jd).lower()
    best, best_score = 'general', 0
    for cat, keywords in TA_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best, best_score = cat, score
    return best

# ================================================================
# 截止日期（模拟：LinkedIn 通常 14-30 天关闭）
# ================================================================
def guess_deadline(title, posted_date_str, region='domestic'):
    base = TODAY
    if posted_date_str:
        try:
            from datetime import datetime
            base = datetime.strptime(posted_date_str[:10], '%Y-%m-%d').date()
        except:
            base = TODAY

    # LinkedIn/Boss 通常岗位存活 14-30 天
    if region == 'overseas':
        days_left = random.randint(7, 30)
    else:
        days_left = random.randint(5, 21)

    deadline = base + timedelta(days=days_left)
    return {
        'deadline': deadline.isoformat(),
        'daysLeft': (deadline - TODAY).days,
    }

def rate_priority(title, company=''):
    t, c = title.lower(), company.lower()
    score = 3
    if any(k in t for k in ['lead', 'principal', 'director', 'head', 'manager']): score += 2
    if any(k in t for k in ['senior', 'sr.', 'advanced']): score += 1
    if any(k in t for k in ['intern', 'student', '实习']): score -= 2
    if any(k in c for k in ['activision', 'ea', 'ubisoft', 'rockstar', 'naughty dog', 'riot', 'blizzard',
                              'epic', 'tencent games', 'miHoYo', 'netease games', 'miHoYo', 'tencent']): score += 1
    return max(1, min(5, score))

def make_id(*args):
    return abs(hash('|'.join(str(a) for a in args))) % 10000000

def build_job(title, company, detail_url, region, city_or_address,
              salary='—', posted=TODAY_STR, job_type='Full-time',
              level='mid', priority=3, jd='', source='', lat=None, lng=None):
    """统一岗位数据结构"""
    exp = classify_experience(title, jd)
    sub = classify_ta_sub(title, jd)
    deadline_info = guess_deadline(title, posted, region)

    if should_skip_by_experience(title, region):
        return None

    job = {
        'id': make_id(detail_url or title),
        'name': title,
        'company': company,
        'region': region,
        'source': source,
        'url': detail_url,
        'postedDate': posted,
        'type': job_type,
        'level': exp,
        'levelLabel': {
            'intern':'实习', 'entry':'1年以下', 'mid':'1-3年',
            'senior':'3-5年', 'lead':'5年+'
        }.get(exp, '1-3年'),
        'priority': priority,
        'salary': salary,
        'taSubCategory': sub,
        'taSubLabel': {
            'character':'角色 TA', 'environment':'环境 TA',
            'rendering':'渲染 TA', 'pipeline':'流程 TA', 'ui':'UI TA', 'general':'综合 TA'
        }.get(sub, '综合 TA'),
        'jd': jd,
        'excluded': False,
        'deadline': deadline_info['deadline'],
        'daysLeft': deadline_info['daysLeft'],
    }

    if region == 'domestic':
        job['city'] = city_or_address
    else:
        job['address'] = city_or_address
        if lat is not None and lng is not None:
            job['lat'] = lat
            job['lng'] = lng

    return job

# ================================================================
# 国内爬虫
# ================================================================
def scrape_51job():
    log('爬取 51job...')
    jobs = []
    if not HAS_DEPS:
        return jobs
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    keywords = ['技术美术 TA', 'TA 技术美术']
    cities = ['深圳', '上海', '北京', '广州', '杭州']

    for keyword in keywords:
        for city in cities[:2]:
            try:
                url = f'https://search.51job.com/list/{quote_plus(city)},000000,0000,00,9,99,{quote_plus(keyword)},2,1.html'
                resp = requests.get(url, headers=headers, timeout=15)
                resp.encoding = 'gbk'
                soup = BeautifulSoup(resp.text, 'lxml')
                cards = soup.select('.j_joblist .jlb, .j_joblist .e')
                for card in cards[:8]:
                    link = card.select_one('.jti a, .e a, a[href*="jobs"]')
                    if not link:
                        continue
                    title = link.get_text(strip=True)
                    detail_url = link.get('href', '')
                    company = card.select_one('.t, .c a, .jcn .c a')
                    company_name = company.get_text(strip=True) if company else ''
                    salary_el = card.select_one('.sal, .es, .jcn span')
                    salary = salary_el.get_text(strip=True) if salary_el else '—'

                    if title and company_name and ('TA' in title or '技术美术' in title):
                        job = build_job(title, company_name, detail_url, 'domestic', city,
                                        salary=salary, source='51Job',
                                        job_type='实习' if '实习' in title else 'Full-time')
                        if job:
                            jobs.append(job)
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                log(f'  51job 失败: {e}')
    log(f'  51job → {len(jobs)} 个岗位')
    return jobs

def scrape_game_companies():
    log('爬取游戏公司官网...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    companies = [
        {'name': '腾讯游戏', 'url': 'https://careers.tencent.com/search.html?query=TA',
         'city': '深圳', 'source': '腾讯招聘'},
        {'name': '网易游戏', 'url': 'https://game.163.com/hr/positions',
         'city': '杭州', 'source': '网易游戏'},
        {'name': '米哈游', 'url': 'https://jobs.mihoyo.com',
         'city': '上海', 'source': '米哈游'},
        {'name': '字节跳动游戏', 'url': 'https://job.bytedance.com/technology',
         'city': '上海', 'source': '字节跳动'},
        {'name': '莉莉丝游戏', 'url': 'https://www.lilith.com/careers/',
         'city': '上海', 'source': '莉莉丝'},
        {'name': '鹰角网络', 'url': 'https://www.yostar.com/careers/',
         'city': '上海', 'source': '鹰角网络'},
        {'name': '完美世界', 'url': 'https://www.wanmei.com/hr/',
         'city': '北京', 'source': '完美世界'},
        {'name': '盛趣游戏', 'url': 'https://www.sqgame.com/about/join',
         'city': '上海', 'source': '盛趣游戏'},
        {'name': '37互娱', 'url': 'https://www.37.com/hr/',
         'city': '广州', 'source': '37互娱'},
        {'name': 'FunPlus', 'url': 'https://www.funplus.com/careers/',
         'city': '北京', 'source': 'FunPlus'},
        {'name': '叠纸游戏', 'url': 'https://www.papergames.cn/careers',
         'city': '苏州', 'source': '叠纸'},
        {'name': 'IGG', 'url': 'https://www.igg.com/jobs',
         'city': '福州', 'source': 'IGG'},
        {'name': '朝夕光年', 'url': 'https://careers.bytedance.com/chinese',
         'city': '北京', 'source': '朝夕光年'},
        {'name': '英雄游戏', 'url': 'https://www.herogame.com/careers',
         'city': '北京', 'source': '英雄游戏'},
        {'name': '游族网络', 'url': 'https://www.youzu.com/about.html',
         'city': '上海', 'source': '游族网络'},
        {'name': '吉比特', 'url': 'https://www.catbird.com.cn/careers',
         'city': '深圳', 'source': '吉比特'},
        {'name': '西山居', 'url': 'https://www.xishanju.com.cn/about/join',
         'city': '珠海', 'source': '西山居'},
        {'name': '多益网络', 'url': 'https://www.duoyi.com/about/recruit',
         'city': '广州', 'source': '多益网络'},
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    ta_keywords = ['技术美术', 'TA', 'Technical Artist', 'Shader', '渲染', '工具', '流程']

    for company in companies:
        try:
            resp = requests.get(company['url'], headers=headers, timeout=15)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')

            for link in soup.select('a[href]')[:60]:
                try:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    if not any(kw in text for kw in ta_keywords):
                        continue
                    if len(text) < 5 or len(text) > 80:
                        continue

                    detail_url = href
                    if href.startswith('/'):
                        base = '/'.join(company['url'].split('/')[:3])
                        detail_url = base + href
                    elif not href.startswith('http'):
                        detail_url = company['url'].rstrip('/') + '/' + href

                    job_type = '实习' if '实习' in text else 'Full-time'
                    priority = rate_priority(text, company['name'])

                    job = build_job(text, company['name'], detail_url, 'domestic', company['city'],
                                    source=company['source'], job_type=job_type, priority=priority)
                    if job:
                        jobs.append(job)
                except Exception:
                    continue

            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            log(f'  {company["name"]} 失败: {e}')

    log(f'  游戏公司官网 → {len(jobs)} 个岗位')
    return jobs

def scrape_bilibili_portfolios():
    log('爬取 B站 TA 作品集...')
    portfolios = []
    if not HAS_DEPS:
        return portfolios

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://search.bilibili.com',
    }

    keywords = [
        '技术美术 TA 作品集 2025',
        '技术美术 TA 个人作品集',
        '游戏 TA 作品集 求职',
        '2627 技术美术 作品集',
        'Technical Artist portfolio showreel',
    ]

    for keyword in keywords[:4]:
        try:
            url = 'https://api.bilibili.com/x/web-interface/search/type'
            params = {'search_type': 'video', 'keyword': keyword, 'page': 1, 'pagesize': 20}
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            data = resp.json()

            if data.get('code') == 0:
                results = data.get('data', {}).get('result', [])
                for item in results:
                    bvid = item.get('bvid', '')
                    title = item.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
                    author = item.get('author', '')
                    description = item.get('description', '')[:300]
                    play = item.get('play', 0)
                    like = item.get('like', 0)
                    pubdate = item.get('pubdate', 0)

                    import time as time_module
                    pub_date = time_module.strftime('%Y-%m-%d', time_module.localtime(pubdate)) if pubdate else TODAY_STR

                    if bvid and title:
                        portfolios.append({
                            'id': make_id('bilibili', bvid),
                            'bvid': bvid,
                            'title': title,
                            'author': author,
                            'description': description,
                            'playCount': play,
                            'likeCount': like,
                            'publishDate': pub_date,
                            'url': f'https://www.bilibili.com/video/{bvid}',
                            'platform': 'bilibili',
                        })
            time.sleep(random.uniform(0.3, 0.8))
        except Exception as e:
            log(f'  B站 {keyword[:15]} 失败: {e}')

    seen = set()
    unique = [p for p in portfolios if p['bvid'] not in seen and not seen.add(p['bvid'])]
    log(f'  B站 → {len(unique)} 个作品集')
    return unique

# ================================================================
# 海外爬虫
# ================================================================
def scrape_linkedin():
    log('爬取 LinkedIn...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    locations = [
        ('Salt Lake City, UT', 40.7608, -111.8910),
        ('Los Angeles, CA', 34.0522, -118.2437),
        ('San Francisco, CA', 37.7749, -122.4194),
        ('Seattle, WA', 47.6062, -122.3321),
        ('Austin, TX', 30.2672, -97.7431),
        ('Denver, CO', 39.7392, -104.9903),
        ('Vancouver, BC', 49.2827, -123.1207),
        ('New York, NY', 40.7128, -74.0060),
        ('London, UK', 51.5074, -0.1278),
        ('Singapore', 1.3521, 103.8198),
    ]

    keywords = ['Technical Artist', 'Technical Artist Character', 'Technical Artist Rendering',
                'Shader Artist', 'Pipeline Technical Artist']

    for keyword in keywords[:2]:
        for loc_name, lat, lng in locations[:5]:
            try:
                url = (f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
                       f'?keywords={quote_plus(keyword)}&location={quote_plus(loc_name)}&f_TPR=r2592000&start=0')
                resp = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(resp.text, 'lxml')

                cards = soup.select('.job-card-container, .occludable-update')
                for card in cards[:6]:
                    try:
                        link = card.select_one('a[href*="/jobs/"]') or card.select_one('a')
                        if not link:
                            continue
                        href = link.get('href', '')
                        title_el = card.select_one('.job-card-list__title--link, h3, h2')
                        title = title_el.get_text(strip=True) if title_el else ''
                        company_el = card.select_one('.artdeco-entity-lockup__subtitle, .job-card-container__company-name')
                        company = company_el.get_text(strip=True) if company_el else ''
                        meta_el = card.select_one('.job-card-container__listed-time, time')

                        if title and company and '/jobs/' in href:
                            detail_url = href if 'linkedin.com' in href else f'https://www.linkedin.com{href}'
                            posted = meta_el.get_text(strip=True) if meta_el else ''
                            exp = classify_experience(title)
                            priority = rate_priority(title, company)

                            job = build_job(title, company, detail_url, 'overseas', loc_name,
                                            posted=posted, job_type='Intern' if 'intern' in title.lower() else 'Full-time',
                                            priority=priority, source='LinkedIn',
                                            lat=lat + random.uniform(-0.3, 0.3),
                                            lng=lng + random.uniform(-0.3, 0.3))
                            if job:
                                jobs.append(job)
                    except Exception:
                        continue

                time.sleep(random.uniform(1, 2))
            except Exception as e:
                log(f'  LinkedIn {loc_name[:20]} 失败: {e}')

    log(f'  LinkedIn → {len(jobs)} 个岗位')
    return jobs

def scrape_indeed():
    log('爬取 Indeed...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    locations = [
        ('Salt Lake City, UT', 40.7608, -111.8910),
        ('Los Angeles, CA', 34.0522, -118.2437),
        ('Seattle, WA', 47.6062, -122.3321),
        ('San Francisco, CA', 37.7749, -122.4194),
        ('Vancouver, BC', 49.2827, -123.1207),
        ('Austin, TX', 30.2672, -97.7431),
    ]

    for loc_name, lat, lng in locations:
        try:
            url = f'https://www.indeed.com/jobs?q={quote_plus("Technical Artist")}&l={quote_plus(loc_name)}&sort=date'
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')

            cards = soup.select('a[id^="job_"], .job-card')
            for card in cards[:8]:
                link = card.select_one('a[href]')
                if not link:
                    continue
                href = link.get('href', '')
                title = link.get('title', '') or link.get_text(strip=True)
                company_el = card.select_one('.companyName, .company')
                company = company_el.get_text(strip=True) if company_el else ''

                if title and company:
                    detail_url = 'https://www.indeed.com' + href if href.startswith('/') else href
                    job = build_job(title, company, detail_url, 'overseas', loc_name,
                                    source='Indeed', priority=rate_priority(title, company),
                                    lat=lat + random.uniform(-0.2, 0.2),
                                    lng=lng + random.uniform(-0.2, 0.2))
                    if job:
                        jobs.append(job)

            time.sleep(random.uniform(1, 2))
        except Exception as e:
            log(f'  Indeed {loc_name[:20]} 失败: {e}')

    log(f'  Indeed → {len(jobs)} 个岗位')
    return jobs

def scrape_gaming_studios():
    log('爬取海外游戏工作室...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    studios = [
        {'name': 'Riot Games', 'url': 'https://www.riotgames.com/en/work-with-us', 'lat': 33.9425, 'lng': -118.4081},
        {'name': 'Epic Games', 'url': 'https://www.epicgames.com/site/en-US/careers', 'lat': 35.9102, 'lng': -78.9382},
        {'name': 'Bungie', 'url': 'https://careers.bungie.com/', 'lat': 47.6062, 'lng': -122.3321},
        {'name': 'Rockstar Games', 'url': 'https://www.rockstargames.com/careers', 'lat': 40.7580, 'lng': -73.9855},
        {'name': 'Activision', 'url': 'https://www.activision.com/careers', 'lat': 34.0205, 'lng': -118.3941},
        {'name': 'Naughty Dog', 'url': 'https://www.naughtydog.com/careers', 'lat': 34.0205, 'lng': -118.3941},
        {'name': 'PlayStation Studios', 'url': 'https://careers.playstation.com/', 'lat': 37.4030, 'lng': -122.1084},
        {'name': 'Santa Monica Studio', 'url': 'https://www.sms.playstation.com/careers', 'lat': 34.0205, 'lng': -118.3941},
        {'name': 'Insomniac Games', 'url': 'https://careers.insomniac.games/', 'lat': 34.1503, 'lng': -118.4526},
        {'name': 'Ubisoft', 'url': 'https://www.ubisoft.com/en-us/careers', 'lat': 34.0205, 'lng': -118.3941},
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    ta_terms = ['technical artist', 'ta', 'shader', 'rendering', 'pipeline']

    for studio in studios:
        try:
            resp = requests.get(studio['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')

            for link in soup.select('a[href]')[:80]:
                try:
                    text = link.get_text().lower()
                    href = link.get('href', '')
                    if not any(term in text for term in ta_terms):
                        continue
                    title = link.get_text(strip=True)
                    if len(title) < 5 or len(title) > 100:
                        continue

                    if href.startswith('/'):
                        base = '/'.join(studio['url'].split('/')[:3])
                        href = base + href
                    elif not href.startswith('http'):
                        href = studio['url'].rstrip('/') + '/' + href

                    job = build_job(title, studio['name'], href, 'overseas', studio['name'],
                                    source=studio['name'],
                                    priority=rate_priority(title, studio['name']),
                                    lat=studio['lat'] + random.uniform(-0.2, 0.2),
                                    lng=studio['lng'] + random.uniform(-0.2, 0.2))
                    if job:
                        jobs.append(job)
                except Exception:
                    continue

            time.sleep(random.uniform(1, 2))
        except Exception as e:
            log(f'  {studio["name"]} 失败: {e}')

    log(f'  游戏工作室 → {len(jobs)} 个岗位')
    return jobs

# ================================================================
# 智能分析摘要
# ================================================================
def generate_summary(domestic_jobs, overseas_jobs):
    """生成岗位分析摘要"""
    all_jobs = domestic_jobs + overseas_jobs

    # 按 TA 细分统计
    sub_counts = {}
    for j in all_jobs:
        cat = j.get('taSubCategory', 'general')
        sub_counts[cat] = sub_counts.get(cat, 0) + 1

    # 按经验等级统计
    exp_counts = {'intern': 0, 'entry': 0, 'mid': 0, 'senior': 0, 'lead': 0}
    for j in all_jobs:
        exp = j.get('level', 'mid')
        if exp in exp_counts:
            exp_counts[exp] += 1

    # 按公司统计
    company_counts = {}
    for j in all_jobs:
        c = j.get('company', '')
        if c:
            company_counts[c] = company_counts.get(c, 0) + 1
    top_companies = sorted(company_counts.items(), key=lambda x: -x[1])[:5]

    # 热门细分（最多招聘的细分）
    if sub_counts:
        hottest_sub = max(sub_counts, key=sub_counts.get)
    else:
        hottest_sub = 'general'

    # 招人最多的公司
    top_company = top_companies[0][0] if top_companies else ''

    # 找出一个代表性岗位（priority 最高的）
    top_jobs = sorted(all_jobs, key=lambda x: -x.get('priority', 3))[:3]

    summary = {
        'totalJobs': len(all_jobs),
        'domesticJobs': len(domestic_jobs),
        'overseasJobs': len(overseas_jobs),
        'hotTestCategory': {
            'category': hottest_sub,
            'label': {
                'character':'角色 TA', 'environment':'环境 TA',
                'rendering':'渲染/Shader TA', 'pipeline':'流程/工具 TA',
                'ui':'UI TA', 'general':'综合 TA'
            }.get(hottest_sub, '综合 TA'),
            'count': sub_counts.get(hottest_sub, 0),
        },
        'topCompanies': [{'name': c, 'count': n} for c, n in top_companies],
        'experienceBreakdown': {
            'intern': exp_counts['intern'],
            'entry': exp_counts['entry'],
            'mid': exp_counts['mid'],
            'senior': exp_counts['senior'],
            'lead': exp_counts['lead'],
        },
        'topJobs': [{
            'name': j['name'],
            'company': j['company'],
            'salary': j.get('salary', '—'),
            'level': j.get('levelLabel', ''),
            'taSub': j.get('taSubLabel', ''),
            'requirements': extract_min_requirements(j.get('jd', '')),
        } for j in top_jobs if j.get('jd')],
        'updated': TODAY_STR,
    }

    return summary

def extract_min_requirements(jd):
    """从 JD 中提取最低要求（摘要）"""
    if not jd:
        return '详见 JD'
    # 提取前 100 字
    text = re.sub(r'<[^>]+>', '', jd)
    text = re.sub(r'\s+', ' ', text).strip()
    # 找关键技能
    skills = []
    skill_keywords = ['Unity', 'Unreal', 'Maya', 'Python', 'HLSL', 'GLSL', 'Shader',
                       'Photoshop', 'Substance', 'Blender', 'Animation', 'Rigging',
                       '渲染', '图形', '美术', 'C#', 'C++']
    for sk in skill_keywords:
        if sk.lower() in text.lower():
            skills.append(sk)
    if skills:
        return '、'.join(skills[:6])
    return text[:80] if text else '详见 JD'

# ================================================================
# 主流程
# ================================================================
def dedup(jobs):
    seen, result = set(), []
    for j in jobs:
        url = j.get('url', '')
        if url and url not in seen:
            seen.add(url)
            result.append(j)
    return result

def merge_with_existing(new_jobs, existing_jobs, max_total=400):
    existing_map = {j.get('url', j.get('id', '')): j for j in existing_jobs}
    existing_map.update({j.get('url', j.get('id', '')): j for j in new_jobs})
    merged = list(existing_map.values())
    merged.sort(key=lambda x: (-x.get('priority', 3), x.get('postedDate', '')))
    return merged[:max_total]

def main():
    log(f'===== TA Job Finder v3.0 — {TODAY_STR} =====')

    target = os.environ.get('SCRAPE_TARGET', 'all')

    # 加载现有数据
    existing_domestic = load_json(f'{DATA_DIR}/jobs-domestic.json') or []
    existing_overseas = load_json(f'{DATA_DIR}/jobs-overseas.json') or []
    existing_portfolios = load_json(f'{DATA_DIR}/portfolios.json') or []

    all_domestic, all_overseas, all_portfolios = [], [], []

    if target in ('all', 'domestic'):
        domestic_new = dedup(scrape_51job() + scrape_game_companies())
        all_domestic = merge_with_existing(domestic_new, existing_domestic, max_total=400)
        save_json(f'{DATA_DIR}/jobs-domestic.json', all_domestic)
        log(f'国内岗位已保存: {len(all_domestic)} 条')

    if target in ('all', 'overseas'):
        overseas_new = dedup(scrape_linkedin() + scrape_indeed() + scrape_gaming_studios())
        all_overseas = merge_with_existing(overseas_new, existing_overseas, max_total=400)
        save_json(f'{DATA_DIR}/jobs-overseas.json', all_overseas)
        log(f'海外岗位已保存: {len(all_overseas)} 条')

    if target in ('all', 'portfolios'):
        portfolios_new = scrape_bilibili_portfolios()
        existing_map = {p.get('bvid', p.get('id', '')): p for p in existing_portfolios}
        existing_map.update({p.get('bvid', p.get('id', '')): p for p in portfolios_new})
        all_portfolios = list(existing_map.values())[:200]
        save_json(f'{DATA_DIR}/portfolios.json', all_portfolios)
        log(f'作品集已保存: {len(all_portfolios)} 条')

    # 生成智能摘要
    summary = generate_summary(all_domestic, all_overseas)
    save_json(f'{DATA_DIR}/summary.json', summary)

    # 统一导出
    combined = {
        'updated': TODAY_STR,
        'domesticJobs': all_domestic,
        'overseasJobs': all_overseas,
        'portfolios': all_portfolios,
        'summary': summary,
    }
    save_json(f'{DATA_DIR}/github_contents.json', combined)

    log('===== 数据更新完成 =====')
    log(f'国内 {len(all_domestic)} | 海外 {len(all_overseas)} | 作品集 {len(all_portfolios)}')
    log(f'热门方向: {summary["hotTestCategory"]["label"]} ({summary["hotTestCategory"]["count"]} 个岗位)')
    for c in summary['topCompanies']:
        log(f'  {c["name"]}: {c["count"]} 个岗位')

if __name__ == '__main__':
    main()
