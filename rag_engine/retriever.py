"""
retriever.py — Robust JSON-based Retriever Fallback
Bypasses the broken Torch DLL by reading scraped JSON files directly.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

SCRAPED_DATA_DIR = Path("data/scraped")

class Retriever:
    def __init__(self):
        logger.info("Initializing Robust JSON-based Retrieval Engine (Bypassing Embeddings)...")
        self.data_cache = []
        self._load_data()

    def _load_data(self):
        """Loads all scraped JSONs into memory for fast lookup."""
        if not SCRAPED_DATA_DIR.exists():
            return
        
        for file_path in SCRAPED_DATA_DIR.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.data_cache.append(data)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

    def query(self, user_text: str) -> List[Dict]:
        """
        Performs a simple keyword matching retrieval across scheme names and metadata.
        Returns top matches as context chunks.
        """
        user_text_lower = user_text.lower()
        results = []

        # 1. Simple search for scheme mentions
        for scheme in self.data_cache:
            name = scheme.get("scheme_name", "").lower()
            if any(word in user_text_lower for word in name.split()):
                # Create a context chunk manually
                fields = scheme.get("fields", {})
                fact_sheet = (
                    f"FACT SHEET: {scheme['scheme_name']}\n"
                    f"AMC: {scheme['amc']} | Category: {scheme['category']}\n"
                    f"Expense Ratio: {fields.get('expense_ratio', 'N/A')} | "
                    f"Exit Load: {fields.get('exit_load', 'N/A')}\n"
                    f"Riskometer: {fields.get('riskometer', 'N/A')}\n"
                    f"Min SIP: {fields.get('minimum_sip_amount', 'N/A')}"
                )
                
                results.append({
                    "text": fact_sheet,
                    "source_url": scheme.get("source_url", "N/A"),
                    "scheme": scheme.get("scheme_name", "Unknown")
                })
                
                # Also add raw text if available
                raw_text = scheme.get("raw_text", "")
                if raw_text and raw_text != "N/A":
                    results.append({
                        "text": f"Background on {scheme['scheme_name']}: {raw_text[:500]}...",
                        "source_url": scheme.get("source_url", "N/A"),
                        "scheme": scheme.get("scheme_name", "Unknown")
                    })

        # 2. Fallback: If no scheme mentioned, return first 3 as general context
        if not results:
            for scheme in self.data_cache[:2]:
                results.append({
                    "text": f"General Data: {scheme['scheme_name']}",
                    "source_url": scheme.get("source_url", "N/A"),
                    "scheme": scheme.get("scheme_name", "Unknown")
                })

        return results[:3]
