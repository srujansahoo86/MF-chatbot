# Scheduler — Phase 2a

This folder contains the configuration and documentation for the **GitHub Actions Scheduler**.

> The actual GitHub Actions workflow file **must** live at:
> `.github/workflows/data_refresh.yml`
> (This is a GitHub requirement — workflows are only recognized from this path.)

## What the Scheduler Does

- Triggers automatically every day at **9:15 AM IST** (`3:45 AM UTC`)
- Cron expression: `45 3 * * *`
- Also supports **manual trigger** from the GitHub Actions UI (`workflow_dispatch`)
- Runs the full pipeline: **Scrape → Chunk → Embed → Update Vector Store**
- Commits `data/last_updated.json` back to the repository after each successful run

## Workflow File

| File | Path |
|------|------|
| GitHub Actions Workflow | [`.github/workflows/data_refresh.yml`](../.github/workflows/data_refresh.yml) |

## Pipeline Steps Triggered

```
1. Checkout repo
2. Set up Python 3.11
3. Cache pip dependencies
4. pip install -r scraper/requirements.txt
5. playwright install chromium
6. python scraper/scraper.py         ← runs Scraping Service
7. git commit data/last_updated.json ← commits timestamp back to repo
```

## How to Activate

1. Push this project to a **GitHub repository**
2. Go to **Settings → Secrets and variables → Actions**
3. Add secret: `OPENAI_API_KEY` = your OpenAI API key
4. The schedule will activate automatically on the next cron trigger

## Manual Trigger

Go to: `GitHub Repo → Actions → Daily Data Refresh → Run workflow`

## Schedule Reference

| Timezone | Time |
|----------|------|
| IST (UTC+5:30) | 9:15 AM |
| UTC | 3:45 AM |
| Cron (UTC) | `45 3 * * *` |
