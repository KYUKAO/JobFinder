# TA Job Finder — 自动爬虫系统

## 定时任务

GitHub Actions 每天 **北京时间 8:00**（UTC 0:00）自动运行。

## 本地测试

```bash
cd scripts
pip install -r requirements.txt
python updater.py
```

## 工作流程

```
.github/workflows/scheduled-scrape.yml
    ↓ 每天 8:00 UTC 触发
scripts/updater.py
    ↓
┌─────────────────────────────────┐
│  1. scrape_linkedin()          │  爬取 LinkedIn 海外岗位
│  2. scrape_boss()              │  爬取 Boss 直聘国内岗位
│  3. scrape_bilibili()          │  爬取 B 站 TA 作品集
└─────────────────────────────────┘
    ↓ 更新 HTML 数据
overseas.html  →  更新 overseasJobs
boss.html       →  更新 domesticJobs
portfolios.html →  更新 portfolios
index.html     →  更新 allJobs
    ↓
git commit + push
```

## 注意

- LinkedIn 和 Boss 直聘有反爬机制，实测可能需要 Cookies 或 Playwright 渲染模式
- B 站 API 相对稳定，可以直接使用
- 手动触发：在 GitHub Actions 页面 → "Daily Scrape" → Run workflow
