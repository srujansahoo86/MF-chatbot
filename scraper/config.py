"""
config.py — Scraping Service Configuration
Mutual Fund FAQ Chatbot | Phase 2b: Scraping Service

Defines all target URLs and the fields to extract per scheme.
"""

# ── Corpus: 5 SBI Mutual Fund Scheme URLs (Groww) ────────────────────────────
SCHEME_URLS = [
    {
        "scheme_name": "SBI Children's Fund – Investment Plan (Direct Growth)",
        "amc": "SBI Mutual Fund",
        "category": "Children's Fund",
        "url": "https://groww.in/mutual-funds/sbi-children's-fund-investment-plan-direct-growth",
    },
    {
        "scheme_name": "SBI ELSS Tax Saver Fund (Direct Growth)",
        "amc": "SBI Mutual Fund",
        "category": "ELSS / Tax Saving",
        "url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
    },
    {
        "scheme_name": "SBI Contra Fund (Direct Growth)",
        "amc": "SBI Mutual Fund",
        "category": "Contra / Value",
        "url": "https://groww.in/mutual-funds/sbi-contra-fund-direct-growth",
    },
    {
        "scheme_name": "SBI Gold Fund (Direct Growth)",
        "amc": "SBI Mutual Fund",
        "category": "Commodity / Gold",
        "url": "https://groww.in/mutual-funds/sbi-gold-fund-direct-growth",
    },
    {
        "scheme_name": "SBI Children's Fund – Savings Plan (Direct Growth)",
        "amc": "SBI Mutual Fund",
        "category": "Children's Fund",
        "url": "https://groww.in/mutual-funds/sbi-children's-fund-savings-plan-direct-growth",
    },
]

# ── Fields to extract from each scheme page ───────────────────────────────────
FIELDS_TO_EXTRACT = [
    "nav",
    "expense_ratio",
    "exit_load",
    "minimum_sip_amount",
    "minimum_lumpsum_amount",
    "benchmark_index",
    "riskometer",
    "elss_lock_in_period",
    "fund_manager",
    "aum",
]

# ── Output paths ──────────────────────────────────────────────────────────────
OUTPUT_DIR = "data/scraped"
TIMESTAMP_FILE = "data/last_updated.json"

# ── Playwright settings ───────────────────────────────────────────────────────
PLAYWRIGHT_TIMEOUT_MS = 30_000       # 30s per page load
PLAYWRIGHT_WAIT_AFTER_LOAD_MS = 3000 # 3s extra wait for JS to render

# ── Retry settings ────────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5
