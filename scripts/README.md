# scripts/ 爬虫脚本说明

## 目录结构

```
scripts/
├── updater.py          # 主爬虫脚本（唯一活跃脚本）
├── requirements.txt     # Python 依赖
├── README.md           # 本文档
└── archive/            # 历史脚本归档
    ├── test_*.py      # 各 API 测试脚本
    ├── scrape_*.py    # 阶段性爬虫脚本
    ├── run_*.py       # 定向运行脚本
    ├── find_working_keywords.py  # 关键词探索
    └── save_portfolios.py       # 作品集保存
```

## updater.py — 主爬虫

唯一的活跃爬虫脚本，调用链如下：

```
main()
├── scrape_51job()              # 51job 国内岗位
│   └── _scrape_51job_page()   # 单页解析
├── scrape_game_companies()      # 游戏公司官网
├── scrape_bilibili_portfolios() # B站 TA 作品集
│   ├── scrape_bilibili_by_search()    # 搜索 API（优先）
│   └── scrape_bilibili_by_related()   # 相关推荐（备选）
├── merge_with_existing()       # 合并新旧数据
└── generate_summary()          # 生成市场摘要
```

### 核心函数

| 函数 | 说明 | 返回 |
|------|------|------|
| `scrape_51job()` | 爬取 51job 国内 TA 岗位 | `List[Job]` |
| `scrape_game_companies()` | 爬取游戏公司官网招聘页 | `List[Job]` |
| `scrape_bilibili_portfolios()` | 爬取 B站 TA 作品集 | `List[Portfolio]` |
| `merge_with_existing(new, existing)` | 合并新旧数据，按优先级排序 | `List` |
| `generate_summary(dom, over)` | 生成市场分析摘要 | `Summary` |

### 优先级排序

```python
LEVEL_ORDER = {'intern': 0, 'entry': 1, 'mid': 2, 'senior': 3, 'lead': 4}
# 同级别按 daysLeft 升序（deadline 近的排前面）
```

## 依赖安装

```bash
pip install -r requirements.txt
```

## 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 51job 返回空 JSON | API 被反爬 | 更换 User-Agent，延长 timeout |
| 游戏公司 404 | 招聘页 URL 变更 | 更新 companies 列表中的 URL |
| B站 412 | 请求频率过高 | 增加 sleep 间隔，更换 User-Agent |
| 合并后数据丢失 | 加载时格式不统一 | 使用 `data.get('domesticJobs', data if isinstance(data, list) else [])` |
