#!/usr/bin/env python3
"""
TA Job Finder — 数据更新主脚本
每天 GitHub Actions 定时运行，更新 HTML 中的岗位数据。
"""

import json
import re
import sys
import os
from datetime import date

# 尝试导入依赖
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

TODAY = date.today().isoformat()
REPO_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/..'

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
# 1. LinkedIn 海外岗位
# ================================================================
def scrape_linkedin():
    log('开始爬取 LinkedIn 海外 TA 岗位...')
    jobs = []

    if not HAS_DEPS:
        log('缺少依赖（requests/beautifulsoup4），跳过 LinkedIn 爬取')
        return jobs

    # 搜索关键词
    keywords = 'technical artist'
    location = 'Salt Lake City, Utah, United States'
    search_url = (
        f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?'
        f'keywords={requests.utils.quote(keywords)}'
        f'&location={requests.utils.quote(location)}'
        f'&f_TPR=r2592000'  # 过去30天
        f'&start=0'
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
        job_cards = soup.select('.job-card-container')

        for card in job_cards[:10]:  # 最多取10个
            try:
                title_el = card.select_one('.job-card-list__title')
                company_el = card.select_one('.job-card-container__linkedin-logo')
                meta_el = card.select_one('.job-card-container__metadata-item')
                link_el = card.select_one('a')

                title = title_el.get_text(strip=True) if title_el else ''
                company = company_el.get('alt', '').replace('logo', '').strip() if company_el else ''
                url = 'https://www.linkedin.com' + link_el.get('href', '') if link_el else ''
                posted_text = meta_el.get_text(strip=True) if meta_el else ''

                # 提取 posted date
                posted_date = extract_posted_date(posted_text)

                if title and company:
                    jobs.append({
                        'name': title,
                        'company': company,
                        'region': 'overseas',
                        'url': url,
                        'postedDate': posted_date,
                        'category': classify_job(title),
                        'priority': rate_priority(title),
                        'salary': '—',
                        'type': 'Full-time' if 'intern' not in title.lower() else 'Intern',
                        'distance': '~ — mi',
                        'lat': 40.7000,
                        'lng': -111.9022,
                        'address': 'Salt Lake City, UT',
                        'jd': '',
                        'excluded': False,
                        'id': abs(hash(title + company)) % 10000
                    })
            except Exception as e:
                log(f'  解析单条岗位失败: {e}')
                continue

        log(f'LinkedIn 爬取完成，获取 {len(jobs)} 个岗位')
    except Exception as e:
        log(f'LinkedIn 爬取失败: {e}，使用备用数据')

    # 如果什么都没爬到，返回一个示例占位数据（实际部署时可留空）
    if not jobs:
        log('LinkedIn 无新数据或被拦截，返回空列表')
    return jobs


def extract_posted_date(meta_text):
    """从 LinkedIn 的 meta 文本中提取日期"""
    text = meta_text.lower()
    if 'today' in text:
        return TODAY
    if 'yesterday' in text:
        from datetime import timedelta
        return (date.today() - timedelta(days=1)).isoformat()
    # "3 days ago", "1 week ago" 等
    m = re.search(r'(\d+)\s*day', text)
    if m:
        from datetime import timedelta
        return (date.today() - timedelta(days=int(m.group(1)))).isoformat()
    return TODAY  # 默认今天


def classify_job(title):
    """根据标题分类"""
    t = title.lower()
    if 'intern' in t or 'student' in t:
        return 'intern'
    if any(k in t for k in ['meta', 'google', 'apple', 'amazon', 'microsoft', 'facebook']):
        return 'fang'
    if any(k in t for k in ['indie', 'small studio']):
        return 'indie'
    return 'aaa'


def rate_priority(title):
    """根据标题评估优先级"""
    t = title.lower()
    if 'lead' in t or 'senior' in t or 'principal' in t:
        return 3
    if 'intern' in t or 'student' in t:
        return 1
    return 2


# ================================================================
# 2. Boss 直聘国内岗位
# ================================================================
def scrape_boss():
    log('开始爬取 Boss 直聘国内 TA 岗位...')
    jobs = []

    if not HAS_DEPS:
        log('缺少依赖，跳过 Boss 爬取')
        return jobs

    # Boss 直聘的岗位搜索 API（示例 URL）
    # 实际需要 Cookies，建议通过 Puppeteer 渲染
    api_url = 'https://www.zhipin.com/web/job/recommend'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.zhipin.com/web/geek/job',
    }

    # Boss 直聘 有强反爬，通常需要登录 Cookies
    # 这里提供框架，实际运行时可以通过 playwright+stealth 模式绕过
    try:
        # 示例：搜索 "技术美术" 关键词
        search_params = {
            'query': '技术美术',
            'city': '101280600',  # 广州示例
            'page': 1,
        }
        resp = requests.get(
            'https://www.zhipin.com/web/geek/job',
            params=search_params,
            headers=headers,
            timeout=15
        )
        log(f'Boss 直聘响应状态: {resp.status_code}')

        if resp.status_code == 200 and len(resp.text) > 100:
            soup = BeautifulSoup(resp.text, 'lxml')
            job_list = soup.select('.job-card-box')

            for card in job_list[:10]:
                try:
                    title_el = card.select_one('.job-title')
                    company_el = card.select_one('.company-name')
                    salary_el = card.select_one('.salary')
                    link_el = card.select_one('a')

                    title = title_el.get_text(strip=True) if title_el else ''
                    company = company_el.get_text(strip=True) if company_el else ''
                    salary = salary_el.get_text(strip=True) if salary_el else ''
                    url = 'https://www.zhipin.com' + link_el.get('href', '') if link_el else ''

                    if title and company:
                        city = guess_city(url)
                        jobs.append({
                            'name': title,
                            'company': company,
                            'region': 'domestic',
                            'city': city,
                            'cityCode': get_city_code(city),
                            'url': url,
                            'postedDate': TODAY,
                            'type': 'Intern' if '实习' in title else 'Full-time',
                            'level': guess_level(title),
                            'priority': rate_priority_zh(title),
                            'salary': salary,
                            'jd': '',
                            'excluded': False,
                            'id': abs(hash(title + company)) % 100000
                        })
                except Exception as e:
                    continue

        log(f'Boss 爬取完成，获取 {len(jobs)} 个岗位')
    except Exception as e:
        log(f'Boss 爬取失败: {e}，使用空列表')

    return jobs


def guess_city(url):
    if 'shanghai' in url or '101020100' in url: return '上海'
    if 'beijing' in url or '101010100' in url: return '北京'
    if 'guangzhou' in url or '101280100' in url: return '广州'
    if 'hangzhou' in url or '101210100' in url: return '杭州'
    if 'shenzhen' in url or '101280600' in url: return '深圳'
    return '深圳'


def get_city_code(city):
    return {'上海':'sh','北京':'bj','广州':'gz','杭州':'hz','深圳':'sz'}.get(city, 'sz')


def guess_level(title):
    if '实习' in title: return '实习'
    if '校招' in title or '应届' in title: return '校招'
    if '1-3' in title or '1-5' in title: return '1-3年'
    return '1-3年'


def rate_priority_zh(title):
    if '实习' in title: return 1
    if 'lead' in title.lower() or '资深' in title: return 3
    return 2


# ================================================================
# 3. B 站作品集
# ================================================================
def scrape_bilibili():
    log('开始爬取 B 站 TA 作品集...')
    portfolios = []

    if not HAS_DEPS:
        log('缺少依赖，跳过 B 站爬取')
        return portfolios

    # B 站 API（无需登录）
    # 搜索 "技术美术 作品集" 相关的 UP 主/视频
    search_url = 'https://api.bilibili.com/x/web-interface/search/type'
    params = {
        'search_type': 'video',
        'keyword': '技术美术 TA 作品集',
        'page': 1,
        'pagesize': 20,
        'order': 'totalrank',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://search.bilibili.com',
    }

    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        data = resp.json()

        if data.get('code') == 0:
            results = data.get('data', {}).get('result', [])
            for item in results[:15]:
                try:
                    bvid = item.get('bvid', '')
                    title = item.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
                    author = item.get('author', '')
                    duration = item.get('duration', '')
                    description = item.get('description', '')[:200]
                    play_count = item.get('play', 0)
                    like_count = item.get('like', 0)
                    pubdate = item.get('pubdate', '')
                    import time
                    publish_date = time.strftime('%Y-%m-%d', time.localtime(pubdate)) if pubdate else TODAY

                    # 过滤掉明显不是 TA 作品集的
                    if not any(k in title.lower() for k in ['ta', 'tech art', '技术美术', '作品集']):
                        if not any(k in description.lower() for k in ['技术美术', 'ta', 'tech art']):
                            continue

                    portfolios.append({
                        'bvid': bvid,
                        'title': title,
                        'author': author,
                        'duration': duration,
                        'description': description,
                        'playCount': play_count,
                        'likeCount': like_count,
                        'publishDate': publish_date,
                        'url': f'https://www.bilibili.com/video/{bvid}',
                        'id': abs(hash(bvid)) % 100000
                    })
                except Exception as e:
                    continue

            log(f'B 站爬取完成，获取 {len(portfolios)} 个作品集')
        else:
            log(f'B 站 API 返回错误: {data.get("message")}')
    except Exception as e:
        log(f'B 站爬取失败: {e}')

    return portfolios


# ================================================================
# 更新 HTML 文件中的数据
# ================================================================
def update_html_file(filepath, var_name, new_data, date_field='postedDate'):
    """在 HTML 文件中更新 JS 数组数据"""
    log(f'更新 {filepath} 中的 {var_name}...')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到数组的起始和结束
    pattern = rf'(var {re.escape(var_name)} = \[)[\s\S]*?(\];)'
    m = re.search(pattern, content)
    if not m:
        log(f'  未找到 {var_name}，跳过')
        return False

    # 构建新数组文本
    import json
    items_str = json.dumps(new_data, ensure_ascii=False, indent=2)
    # 将双引号转成单引号（适配 JS 风格）
    items_str = items_str.replace('"', "'").replace("'", '"')
    # 修正：再把 key/value 的引号换回来
    # 更简单：直接用 repr 风格生成
    items_str = json.dumps(new_data, ensure_ascii=False, indent=2)

    new_array = f'var {var_name} = {items_str};'
    new_content = content[:m.start()] + new_array + content[m.end():]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    log(f'  更新了 {len(new_data)} 条数据')
    return True


# ================================================================
# 主流程
# ================================================================
def main():
    log(f'===== TA Job Finder 数据更新开始 — {TODAY} =====')

    target = os.environ.get('SCRAPE_TARGET', 'all')
    log(f'目标: {target}')

    if target in ('all', 'overseas'):
        # LinkedIn
        overseas_jobs = scrape_linkedin()
        if overseas_jobs:
            update_html_file(f'{REPO_ROOT}/overseas.html', 'overseasJobs', overseas_jobs)
            update_html_file(f'{REPO_ROOT}/index.html', 'allJobs', overseas_jobs, 'postedDate')

    if target in ('all', 'domestic'):
        # Boss
        domestic_jobs = scrape_boss()
        if domestic_jobs:
            update_html_file(f'{REPO_ROOT}/boss.html', 'domesticJobs', domestic_jobs)
            update_html_file(f'{REPO_ROOT}/index.html', 'allJobs', domestic_jobs, 'postedDate')

    if target in ('all', 'portfolios'):
        # B 站
        portfolios = scrape_bilibili()
        if portfolios:
            update_html_file(f'{REPO_ROOT}/portfolios.html', 'portfolios', portfolios, 'publishDate')

    log(f'===== 数据更新完成 — {TODAY} =====')


if __name__ == '__main__':
    main()
