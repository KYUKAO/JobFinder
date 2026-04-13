#!/usr/bin/env python3
"""
TA Job Finder 数据更新主脚本 v3.0
- 数据与框架完全分离（JSON 配置文件驱动）
- 经验等级分类：实习/1年以下/1-3年/3-5年/5年+
- 国内不爬 5+ 岗，国外爬 senior
- 截止日期（deadline）计算
- 智能分析摘要：热门岗位+最低要求
- 修复版本：解决 SSL 错误、连接被拒、XML 解析等问题
"""

import json, re, os, time, random
from datetime import date, timedelta
from urllib.parse import quote_plus

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
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

def create_session():
    """创建带重试机制的 requests session"""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    return session

def create_bilibili_session():
    """创建B站专用session，添加更多请求头"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cookie': 'SESSDATA=; bili_jct=;',  # 空cookie避免被识别为爬虫
    })
    return session

# ================================================================
# 经验等级分类
# ================================================================
EXPERIENCE_LEVELS = ['intern', 'entry', 'mid', 'senior', 'lead']

def classify_experience(title, jd=''):
    """判断经验等级"""
    t = (title + ' ' + jd).lower()
    if any(k in t for k in ['intern', 'student', 'trainee', '实习', '试用期', '应届', '毕业', '校招']):
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
    """国内跳过 5+ 年 岗位"""
    t = title.lower()
    if region == 'domestic':
        if any(k in t for k in ['8年', '10年', '10+', '12年', '15年']):
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
              salary='面议', posted=TODAY_STR, job_type='Full-time',
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

    session = create_session()
    keywords = ['技术美术TA', 'TA 技术美术']
    cities = ['深圳', '上海', '北京', '广州', '杭州']

    for keyword in keywords:
        for city in cities[:2]:
            for page in range(1, 3):  # 每城市爬2页
                try:
                    # 使用 51job 的 API 端点，绕过直接访问
                    params = {
                        'jobArea': city,
                        'keyword': keyword,
                        'pageNum': page,
                        'workYear': '99',  # 不限工作年限
                        'compact': 'true',
                    }
                    url = 'https://we.51job.com/api/job/search-pc'
                    resp = session.get(url, params=params, timeout=20)
                    data = resp.json()

                    job_list = data.get('resultbody', {}).get('job', [])
                    for item in job_list[:10]:
                        title = item.get('jobname', '')
                        if not title or ('TA' not in title and '技术美术' not in title):
                            continue
                        job = build_job(
                            title,
                            item.get('companyname', ''),
                            item.get('job_href', ''),
                            'domestic',
                            item.get('workarea_text', city),
                            salary=item.get('providesalary_text', '面议'),
                            source='51Job',
                            job_type='实习' if '实习' in title else 'Full-time',
                            posted=item.get('updatedate', TODAY_STR),
                            jd=item.get('jobwelf', '')
                        )
                        if job:
                            jobs.append(job)

                    time.sleep(random.uniform(1, 2))
                except Exception as e:
                    log(f'  51job {city} 第{page}页 失败: {e}')
                    time.sleep(2)

    log(f'  51job → {len(jobs)} 个岗位')
    return jobs

def scrape_game_companies():
    log('爬取游戏公司官网...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    session = create_session()

    companies = [
        # 使用 HTTP 的公司（修复 SSL 问题）
        {'name': '盛趣游戏', 'url': 'http://www.sqgame.com/about/join', 'city': '上海', 'source': '盛趣游戏'},
        {'name': '朝夕光年', 'url': 'http://careers.bytedance.com/chinese', 'city': '北京', 'source': '朝夕光年'},
        {'name': '吉比特', 'url': 'http://www.lilith.com/careers/', 'city': '深圳', 'source': '吉比特'},
        # 使用正确 HTTPS 的公司
        {'name': '腾讯游戏', 'url': 'https://careers.tencent.com/search.html?query=TA', 'city': '深圳', 'source': '腾讯招聘'},
        {'name': '网易游戏', 'url': 'https://game.163.com/hr/positions', 'city': '杭州', 'source': '网易游戏'},
        {'name': '米哈游', 'url': 'https://jobs.mihoyo.com', 'city': '上海', 'source': '米哈游'},
        {'name': '字节跳动游戏', 'url': 'https://job.bytedance.com/technology', 'city': '上海', 'source': '字节跳动'},
        {'name': '莉莉丝游戏', 'url': 'https://www.lilith.com/careers/', 'city': '上海', 'source': '莉莉丝'},
        {'name': '鹰角网络', 'url': 'https://www.yostar.com/careers/', 'city': '上海', 'source': '鹰角网络'},
        {'name': '完美世界', 'url': 'https://www.wanmei.com/hr/', 'city': '北京', 'source': '完美世界'},
        {'name': '37互娱', 'url': 'https://www.37.com/hr/', 'city': '广州', 'source': '37互娱'},
        {'name': 'FunPlus', 'url': 'https://www.funplus.com/careers/', 'city': '北京', 'source': 'FunPlus'},
        {'name': '叠纸游戏', 'url': 'https://www.papergames.cn/careers', 'city': '苏州', 'source': '叠纸'},
        {'name': 'IGG', 'url': 'https://www.igg.com/jobs', 'city': '福州', 'source': 'IGG'},
    ]

    ta_terms = ['技术美术', 'TA', 'TA工程师', '美术程序', '图形', 'shader', 'rendering', 'technical artist']

    for company in companies:
        try:
            resp = session.get(company['url'], timeout=15)
            # 检测内容类型，选择合适的解析器
            content_type = resp.headers.get('Content-Type', '')
            if 'xml' in content_type or resp.text.strip().startswith('<?xml'):
                soup = BeautifulSoup(resp.text, 'xml')
            else:
                soup = BeautifulSoup(resp.text, 'lxml')

            for link in soup.find_all('a', href=True)[:60]:
                try:
                    text = (link.get_text() + ' ' + str(link.get('title', ''))).lower()
                    href = link.get('href', '')

                    if not any(term in text for term in ta_terms):
                        continue

                    title = link.get_text(strip=True)
                    if len(title) < 3 or len(title) > 80:
                        continue

                    # 跳过邮箱等非职位链接
                    if '@' in href or 'mailto' in href:
                        continue

                    # 处理相对 URL
                    if href.startswith('/'):
                        base = '/'.join(company['url'].split('/')[:3])
                        href = base + href
                    elif not href.startswith('http'):
                        href = company['url'].rstrip('/') + '/' + href.lstrip('/')

                    job = build_job(
                        title, company['name'], href, 'domestic', company['city'],
                        source=company['source'],
                        priority=rate_priority(title, company['name'])
                    )
                    if job:
                        jobs.append(job)
                except Exception:
                    continue

            time.sleep(random.uniform(1.5, 3))
        except Exception as e:
            log(f'  {company["name"]} 失败: {e}')

    log(f'  游戏公司 → {len(jobs)} 个岗位')
    return jobs

# ================================================================
# B站作品集
# ================================================================
def scrape_bilibili_portfolios():
    log('爬取 B站 TA 作品集...')
    portfolios = []
    if not HAS_DEPS:
        return portfolios

    session = create_bilibili_session()

    # B站 TA 相关标签视频 - 经过测试的可用的关键字
    search_keywords = [
        # 渲染/Shader类
        'UE渲染', '渲染引擎',
        # 特效类
        '游戏特效', 'UE特效', 'VFX', '粒子特效',
        # TA相关
        '技术美术', '图形程序', 'TA教程',
        # 程序化
        'houdini教程', '程序化生成',
        # 综合
        '游戏美术', 'Unity shader', 'game vfx', 'unity教程',
        '场景美术', '动画特效',
    ]

    for keyword in search_keywords:
        try:
            url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={quote_plus(keyword)}&page=1'
            resp = session.get(url, timeout=15)

            # 如果被封，跳过
            if resp.status_code == 412 or (resp.text and '"code":-412' in resp.text):
                log(f'  B站 [{keyword}] 请求被封，跳过')
                time.sleep(2)
                continue

            data = resp.json()

            # 检查 API 返回
            if data.get('code') != 0:
                log(f'  B站 [{keyword}] API错误: {data.get("message")}')
                continue

            # B站API返回结构可能变化，尝试多种路径
            result = data.get('data', {})
            videos = result.get('result', []) if isinstance(result, dict) else result

            if not videos:
                continue

            for v in videos[:10]:
                if not isinstance(v, dict):
                    continue
                bvid = v.get('bvid', '')
                if not bvid or any(p.get('bvid') == bvid for p in portfolios):
                    continue

                # 处理标题中的HTML标签
                title = v.get('title', '')
                if isinstance(title, str):
                    title = title.replace('<em class="keyword">', '').replace('</em>', '').replace('<em>', '').replace('</em>', '')

                portfolios.append({
                    'bvid': bvid,
                    'title': title,
                    'author': v.get('author', ''),
                    'description': v.get('description', ''),
                    'duration': v.get('duration', ''),
                    'views': v.get('play', 0),
                    'category': 'TA',
                    'platform': 'bilibili',
                    'url': f'https://www.bilibili.com/video/{bvid}',
                    'addedDate': TODAY_STR,
                })

            time.sleep(random.uniform(1, 2))

        except Exception as e:
            log(f'  B站 [{keyword}] 失败: {e}')

    log(f'  B站作品集 → {len(portfolios)} 个')
    return portfolios

# ================================================================
# LinkedIn 爬虫
# ================================================================
def scrape_linkedin():
    log('爬取 LinkedIn...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    session = create_session()

    locations = ['Shanghai', 'Beijing', 'Shenzhen', 'Hangzhou', 'Singapore', 'Los Angeles']
    terms = ['technical artist', 'shader', 'rendering engineer']

    for loc in locations:
        for term in terms:
            try:
                url = f'https://www.linkedin.com/jobs/search/?keywords={quote_plus(term)}&location={quote_plus(loc)}'
                resp = session.get(url, timeout=20)

                soup = BeautifulSoup(resp.text, 'lxml')

                for card in soup.select('.job-search-card')[:10]:
                    try:
                        link = card.select_one('a')
                        if not link:
                            continue
                        title = link.get_text(strip=True)
                        detail_url = link.get('href', '').split('?')[0]

                        company = card.select_one('.company-name, .base-search-card__subtitle')
                        company_name = company.get_text(strip=True) if company else ''

                        meta = card.select_one('.job-search-card__metadata, .search-result-meta')
                        location = meta.get_text(strip=True) if meta else loc

                        if title and company_name:
                            job = build_job(title, company_name, detail_url, 'overseas', location,
                                          source='LinkedIn', priority=rate_priority(title, company_name))
                            if job:
                                jobs.append(job)
                    except Exception:
                        continue

                time.sleep(random.uniform(2, 4))
            except Exception as e:
                log(f'  LinkedIn {loc[:15]} 失败: {e}')

    log(f'  LinkedIn → {len(jobs)} 个岗位')
    return jobs

# ================================================================
# Indeed 爬虫
# ================================================================
def scrape_indeed():
    log('爬取 Indeed...')
    jobs = []
    if not HAS_DEPS:
        return jobs

    session = create_session()

    locations = ['Shanghai,Shanghai (CHN)', 'Beijing (CHN)', 'Singapore',
                 'Los Angeles, CA', 'Seattle, WA', 'San Francisco, CA']
    terms = ['technical artist', 'shader developer', 'rendering engineer']

    for loc_name in locations:
        for term in terms:
            try:
                params = {
                    'q': term,
                    'l': loc_name,
                    'sort': 'date',
                    'limit': 20,
                }
                url = 'https://www.indeed.com/jobs'
                resp = session.get(url, params=params, timeout=20)

                soup = BeautifulSoup(resp.text, 'lxml')

                for card in soup.select('.job_seen_beacon')[:10]:
                    try:
                        link = card.select_one('a.jcs-JobTitle')
                        if not link:
                            continue
                        title = link.get_text(strip=True)
                        detail_url = 'https://www.indeed.com' + link.get('href', '')

                        company = card.select_one('.company-name')
                        company_name = company.get_text(strip=True) if company else ''

                        salary_el = card.select_one('.salary-snippet')
                        salary = salary_el.get_text(strip=True) if salary_el else '面议'

                        lat, lng = 31.2304, 121.4737  # 默认上海

                        job = build_job(title, company_name, detail_url, 'overseas', loc_name,
                                    source='Indeed', priority=rate_priority(title, company_name),
                                    salary=salary,
                                    lat=lat + random.uniform(-0.2, 0.2),
                                    lng=lng + random.uniform(-0.2, 0.2))
                        if job:
                            jobs.append(job)
                    except Exception:
                        continue

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

    session = create_session()

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

    ta_terms = ['technical artist', 'ta', 'shader', 'rendering', 'pipeline']

    for studio in studios:
        try:
            resp = session.get(studio['url'], timeout=15)
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

    # TA 细分统计
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

    # 热门细分（最多招聘的细分领域）
    if sub_counts:
        hottest_sub = max(sub_counts, key=sub_counts.get)
    else:
        hottest_sub = 'general'

    # 招人最多的公司
    top_company = top_companies[0][0] if top_companies else ''

    # 找出一个代表性岗位（priority 最高的岗位）
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
            'salary': j.get('salary', '面议'),
            'level': j.get('levelLabel', ''),
            'taSub': j.get('taSubLabel', ''),
            'requirements': extract_min_requirements(j.get('jd', '')),
        } for j in top_jobs if j.get('jd')],
        'updated': TODAY_STR,
    }

    return summary

def extract_min_requirements(jd):
    """从 JD 中提取最低要求（摘要用）"""
    if not jd:
        return '详见 JD'
    # 提取纯文本
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
# 主流方法
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
        log(f'国内岗位已保存: {len(all_domestic)} 个')

    if target in ('all', 'overseas'):
        overseas_new = dedup(scrape_linkedin() + scrape_indeed() + scrape_gaming_studios())
        all_overseas = merge_with_existing(overseas_new, existing_overseas, max_total=400)
        save_json(f'{DATA_DIR}/jobs-overseas.json', all_overseas)
        log(f'海外岗位已保存: {len(all_overseas)} 个')

    if target in ('all', 'portfolios'):
        portfolios_new = scrape_bilibili_portfolios()
        existing_map = {p.get('bvid', p.get('id', '')): p for p in existing_portfolios}
        existing_map.update({p.get('bvid', p.get('id', '')): p for p in portfolios_new})
        all_portfolios = list(existing_map.values())[:200]
        save_json(f'{DATA_DIR}/portfolios.json', all_portfolios)
        log(f'作品集已保存: {len(all_portfolios)} 个')

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
