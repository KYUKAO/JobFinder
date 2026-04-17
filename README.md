# TA Job Finder

技术美术（Technical Artist）岗位聚合与竞争分析系统。自动爬取国内外 TA 岗位、TA 作品集（B站），并提供可视化浏览、数据分析和投递建议。

## 目录结构

```
JobFinder/
├── pages/              # 所有 HTML 页面
│   ├── index.html     # 首页 — 入口与概览
│   ├── boss.html      # 国内岗位 — 城市地图 + 筛选
│   ├── overseas.html   # 海外岗位 — 北美地图 + 筛选
│   ├── portfolios.html # TA 作品集 — B站视频
│   ├── analysis.html  # 竞争力分析 & 投递建议
│   └── resumes.html   # 竞争者简历库
│
├── data/              # 所有数据文件（由爬虫自动生成）
│   ├── jobs-domestic.json   # 国内岗位原始数据
│   ├── jobs-overseas.json   # 海外岗位原始数据
│   ├── portfolios.json       # B站 TA 作品集
│   ├── summary.json         # 市场分析摘要
│   └── github_contents.json  # GitHub Pages 合并导出
│
├── scripts/            # 爬虫脚本
│   ├── updater.py      # 主爬虫：爬取岗位 + 作品集
│   ├── requirements.txt
│   ├── README.md
│   └── archive/        # 历史脚本归档（废弃/测试）
│
├── docs/               # 项目文档
│   ├── 爬取方式.md     # 各数据源爬取方式详解
│   └── README.md       # 文档目录
│
└── .github/
    └── workflows/
        └── scheduled-scrape.yml  # GitHub Actions 定时任务
```

## 功能模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 首页入口 | `pages/index.html` | 概览统计、优先投递列表、岗位方向分布 |
| 国内岗位 | `pages/boss.html` | 城市地图、经验筛选、JD 详情 |
| 海外岗位 | `pages/overseas.html` | 北美地图、Entry/Mid/Senior 筛选 |
| TA 作品集 | `pages/portfolios.html` | B站视频收录、UP主信息 |
| 竞争力分析 | `pages/analysis.html` | 能力雷达图、投递建议 |
| 简历库 | `pages/resumes.html` | 竞争者简历参考 |

## 岗位优先级

系统按以下优先级展示岗位：

1. **实习 / Intern** — 最优先
2. **1年以下 / Entry** — 应届生友好
3. **1-3年 / Mid** — 社招主力
4. **3-5年 / Senior**
5. **5年+ / Lead**

TA 细分方向：`渲染 TA` · `角色 TA` · `流程 TA` · `环境 TA` · `UI TA` · `综合 TA`

## 爬虫使用

### 本地运行

```bash
cd scripts
pip install -r requirements.txt
python updater.py
```

### GitHub Actions 自动爬取

每天北京时间 8:00（UTC 0:00）自动运行。也可手动触发：

> GitHub 仓库 → Actions → Daily Scrape → Run workflow

### 定向爬取

在 `scripts/updater.py` 中修改 `SCRAPE_TARGET` 环境变量：

| 值 | 爬取内容 |
|----|---------|
| `all` | 国内岗位 + 海外岗位 + 作品集（默认） |
| `domestic` | 仅国内岗位 |
| `overseas` | 仅海外岗位 |
| `portfolios` | 仅作品集 |

## 数据更新流程

```
.github/workflows/scheduled-scrape.yml
    ↓ 定时触发（北京时间 8:00）
scripts/updater.py
    ├─ scrape_51job()          # 国内岗位（51job）
    ├─ scrape_game_companies() # 国内岗位（游戏公司官网）
    ├─ scrape_bilibili_portfolios()  # B站作品集
    └─ generate_summary()      # 生成市场分析摘要
    ↓ 更新数据文件
data/*.json
    ↓ GitHub Actions 自动提交推送
GitHub Pages → taotao.cc/jobfinder/
```

## 数据源

| 数据类型 | 来源 | 稳定性 |
|---------|------|--------|
| 国内岗位 | 51job API + 游戏公司官网 | 一般（API 可能被封） |
| 海外岗位 | LinkedIn + Indeed + 游戏公司官网 | 一般（需要 Playwright） |
| TA 作品集 | B站 搜索 API | 较好（需控制请求频率） |

详见 [docs/爬取方式.md](docs/爬取方式.md)。

## 开发说明

### HTML 页面路径引用

所有 HTML 页面在 `pages/` 目录下，页面间通过相对路径互相引用：

```html
<a href="boss.html">国内求职</a>
<!-- 无需添加 pages/ 前缀 -->
```

JSON 数据文件在 `data/` 目录下，引用方式：

```html
<script>
  fetch('../data/jobs-domestic.json')
</script>
```

### 添加新数据源

在 `scripts/updater.py` 中新增函数：

```python
def scrape_xxx():
    # 爬取逻辑
    return jobs  # 返回岗位列表
```

然后在 `main()` 中调用并合并数据：

```python
all_domestic = merge_with_existing(scrape_xxx(), existing_domestic)
```

### 岗位字段规范

```json
{
  "id": 1001,
  "name": "技术美术（TA）- 渲染方向",
  "company": "腾讯游戏",
  "city": "深圳",
  "level": "mid",
  "levelLabel": "1-3年",
  "taSubCategory": "rendering",
  "taSubLabel": "渲染 TA",
  "salary": "25K-45K·16薪",
  "url": "https://...",
  "postedDate": "2026-04-18",
  "deadline": "2026-04-30",
  "daysLeft": 12,
  "jd": "岗位职责...",
  "excluded": false
}
```

## 常见问题

详见 [docs/爬取方式.md](docs/爬取方式.md) 第 6 节。

---

*TA Job Finder · 数据仅供参考 · 请以官方信息为准*
