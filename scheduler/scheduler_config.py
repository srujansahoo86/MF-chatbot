"""
scheduler_config.py — Scheduler Configuration
Mutual Fund FAQ Chatbot | Phase 2a: Scheduler

Centralizes all scheduling-related configuration values.
The actual trigger is defined in .github/workflows/data_refresh.yml
"""

# ── Schedule Configuration ────────────────────────────────────────────────────

# 9:15 AM IST = 3:45 AM UTC
CRON_EXPRESSION = "45 3 * * *"      # UTC cron for GitHub Actions
TRIGGER_TIME_IST = "09:15"
TRIGGER_TIMEZONE = "Asia/Kolkata"

# ── Pipeline Steps (in order) ─────────────────────────────────────────────────
PIPELINE_STEPS = [
    "scraper/scraper.py",           # Step 1: Scraping Service
    "chunker/chunker_embedder.py",  # Step 2 & 3: Chunking & Embedding into ChromaDB
]

# ── Output ────────────────────────────────────────────────────────────────────
TIMESTAMP_FILE = "data/last_updated.json"

# ── GitHub Actions Runner ─────────────────────────────────────────────────────
RUNNER = "ubuntu-latest"
PYTHON_VERSION = "3.11"
WORKFLOW_FILE = ".github/workflows/data_refresh.yml"
