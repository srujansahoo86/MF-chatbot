"""
scraper.py — Scraping Service
Mutual Fund FAQ Chatbot | Phase 2b: Scraping Service

Fetches the latest factual data from 5 Groww scheme pages using Playwright
(handles JS-rendered content), extracts structured fields, and saves clean
JSON output per scheme to data/scraped/.

Run:
    python scraper/scraper.py

Output:
    data/scraped/<scheme_slug>.json   — one file per scheme
    data/last_updated.json            — pipeline timestamp
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from config import (
    SCHEME_URLS,
    OUTPUT_DIR,
    TIMESTAMP_FILE,
    PLAYWRIGHT_TIMEOUT_MS,
    PLAYWRIGHT_WAIT_AFTER_LOAD_MS,
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
)

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Text extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove excess whitespace and normalize unicode characters."""
    text = text.replace("\u00a0", " ")          # non-breaking space
    text = re.sub(r"\s+", " ", text)            # collapse whitespace
    return text.strip()


def normalize_value(field_key: str, raw_value: str) -> str:
    """Uses regex and string matching to perfectly clean and normalize the extracted value."""
    # Remove common UI noise prefixes that might not have been caught by the basic replace
    noise_prefixes = ["Expense ratio", "Exit load", "Fund benchmark", "Fund size (AUM)", "Min. for SIP", "Minimum Lumpsum Investment is", "Minimum SIP Investment is set to", "Exit load of"]
    
    val = raw_value
    # Case-insensitive prefix removal
    for noise in noise_prefixes:
        val = re.sub(f"(?i){re.escape(noise)}", "", val).strip(" :\n")
        
    if field_key == "expense_ratio":
        # Extract just the percentage (e.g., "0.75%")
        match = re.search(r"(\d+\.\d+\s*%)", val)
        return match.group(1) if match else val
        
    elif field_key in ["minimum_sip_amount", "minimum_lumpsum_amount", "aum"]:
        # Extract rupees (e.g., "₹500" or "₹43,753.59 Cr")
        match = re.search(r"(₹[\d,]+(?:\.\d+)?(?:\s*Cr|\s*Lakh)?)", val)
        return match.group(1) if match else val

    return val

def extract_field(page, field_key: str, label_patterns: list[str]) -> str:
    """
    Try each CSS/text pattern to find a field value on the page.
    Returns the cleaned, normalized value.
    """
    for pattern in label_patterns:
        try:
            elements = page.locator(f"text={pattern}").all()
            for el in elements:
                parent = el.locator("xpath=..").first
                value = clean_text(parent.inner_text())
                
                # Strip the label itself first (case-insensitive)
                value = re.sub(f"(?i){re.escape(pattern)}", "", value).strip(" :\n")
                
                if value and value.lower() not in ("n/a", "-", ""):
                    return normalize_value(field_key, value)
        except Exception:
            continue
    return "N/A"

def extract_all_fields(page) -> dict:
    """
    Extract all required fields from a loaded Groww scheme page.
    Uses text-based locators to handle dynamic class names.
    """
    return {
        "nav": extract_field(page, "nav", ["NAV", "Net Asset Value"]),
        "expense_ratio": extract_field(page, "expense_ratio", ["Expense Ratio", "expense ratio"]),
        "exit_load": extract_field(page, "exit_load", ["Exit Load", "exit load"]),
        "minimum_sip_amount": extract_field(page, "minimum_sip_amount", ["Min. SIP Amount", "Min. for SIP", "Minimum SIP"]),
        "minimum_lumpsum_amount": extract_field(page, "minimum_lumpsum_amount", ["Min. Lumpsum", "Minimum Lumpsum", "Min. for 1st investment"]),
        "benchmark_index": extract_field(page, "benchmark_index", ["Benchmark", "benchmark"]),
        "riskometer": extract_field(page, "riskometer", ["Riskometer", "Risk Level", "Risk"]),
        "elss_lock_in_period": extract_field(page, "elss_lock_in_period", ["Lock-in Period", "Lock in", "ELSS Lock"]),
        "fund_manager": extract_field(page, "fund_manager", ["Fund Manager", "Managed by"]),
        "aum": extract_field(page, "aum", ["Fund Size", "AUM", "Assets Under Management"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core scraper
# ─────────────────────────────────────────────────────────────────────────────

def scrape_scheme(browser, scheme: dict) -> dict | None:
    """
    Opens the scheme URL in a new browser page, waits for JS rendering,
    extracts all fields, and returns a structured result dict.
    Retries up to MAX_RETRIES times on failure.
    """
    url = scheme["url"]
    scheme_name = scheme["scheme_name"]

    for attempt in range(1, MAX_RETRIES + 1):
        context = None
        page = None
        try:
            logger.info(f"[{scheme_name}] Attempt {attempt}/{MAX_RETRIES} → {url}")

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            # Navigate and wait for network idle
            page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS, wait_until="networkidle")

            # Extra wait for JS-rendered content to paint
            page.wait_for_timeout(PLAYWRIGHT_WAIT_AFTER_LOAD_MS)

            # Extract fields
            fields = extract_all_fields(page)

            # Get full page text as fallback raw content
            raw_text = clean_text(page.inner_text("body"))

            result = {
                "scheme_name": scheme_name,
                "amc": scheme["amc"],
                "category": scheme["category"],
                "source_url": url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "fields": fields,
                "raw_text": raw_text[:8000],  # cap at 8000 chars for storage
            }

            logger.info(f"[{scheme_name}] ✓ Scraped successfully.")
            return result

        except PlaywrightTimeout:
            logger.warning(f"[{scheme_name}] Timeout on attempt {attempt}. Retrying in {RETRY_BACKOFF_SECONDS}s...")
        except Exception as e:
            logger.warning(f"[{scheme_name}] Error on attempt {attempt}: {e}. Retrying in {RETRY_BACKOFF_SECONDS}s...")
        finally:
            if page:
                page.close()
            if context:
                context.close()

        time.sleep(RETRY_BACKOFF_SECONDS * attempt)  # exponential-ish backoff

    logger.error(f"[{scheme_name}] ✗ All {MAX_RETRIES} attempts failed. Skipping.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# File I/O helpers
# ─────────────────────────────────────────────────────────────────────────────

def slug(name: str) -> str:
    """Convert scheme name to a safe filename slug."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def save_result(result: dict) -> None:
    """Save a scraped scheme result to data/scraped/<slug>.json."""
    output_path = Path(OUTPUT_DIR) / f"{slug(result['scheme_name'])}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved → {output_path}")


def save_timestamp(successful: int, failed: int) -> None:
    """Write the pipeline run timestamp to data/last_updated.json."""
    Path(TIMESTAMP_FILE).parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "last_updated_iso": datetime.now(timezone.utc).isoformat(),
        "schemes_scraped": successful,
        "schemes_failed": failed,
    }
    with open(TIMESTAMP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Timestamp saved → {TIMESTAMP_FILE}")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Mutual Fund FAQ Chatbot — Scraping Service Starting")
    logger.info(f"Target schemes: {len(SCHEME_URLS)}")
    logger.info("=" * 60)

    successful, failed = 0, 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for scheme in SCHEME_URLS:
            result = scrape_scheme(browser, scheme)
            if result:
                save_result(result)
                successful += 1
            else:
                failed += 1

        browser.close()

    save_timestamp(successful, failed)

    logger.info("=" * 60)
    logger.info(f"Scraping complete: {successful} succeeded, {failed} failed.")
    logger.info("=" * 60)

    # Exit with error code if all schemes failed (fail the GitHub Actions job)
    if successful == 0:
        raise SystemExit("All schemes failed to scrape. Aborting pipeline.")


if __name__ == "__main__":
    main()
