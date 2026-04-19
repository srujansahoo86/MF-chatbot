"""
generator.py — LLM Generation Layer

Enforces the strict architecture constraints:
- Facts only (based exclusively on context)
- Maximum 3 sentences
- Prepend citation link
- Append "Last updated on" timestamp
"""

import json
import logging
import os
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

TIMESTAMP_FILE = Path("data/last_updated.json")

def get_last_updated() -> str:
    """Reads the pipeline timestamp from the data directory."""
    try:
        if TIMESTAMP_FILE.exists():
            with open(TIMESTAMP_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_updated", "Unknown Date")
    except Exception as e:
        logger.error(f"Could not read timestamp file: {e}")
    return "Unknown Date"


class Generator:
    def __init__(self):
        # Requires OPENAI_API_KEY environment variable to be set
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY is not set. Generation will fail or return mock data.")

    def generate_response(self, query: str, context_chunks: list[dict]) -> str:
        """
        Synthesizes the retrieved chunks into a strict, 3-sentence factual response.
        Adds the necessary citation and date footers.
        """
        # If no context is retrieved, reject immediately without calling LLM
        if not context_chunks:
            return "I do not have factual data regarding this query within my authorized corpus."

        # Flatten context into a single string
        context_string = ""
        source_url = ""
        for idx, chunk in enumerate(context_chunks):
            context_string += f"--- Chunk {idx+1} ---\n{chunk['text']}\n\n"
            # We take the source URL from the mathematically closest chunk (Chunk 1)
            if idx == 0:
                source_url = chunk['source_url']

        if not self.client:
            return (
                "(MOCK RESPONSE - NO API KEY)\n"
                f"The minimum SIP amount is based on context.\n\n"
                f"Source: {source_url}\n"
                f"Last updated on {get_last_updated()}"
            )

        system_message = (
            "You are a strict, factual Mutual Fund Assistant.\n"
            "Rules:\n"
            "1. You must answer the user's question USING ONLY the provided context.\n"
            "2. If the context does not contain the answer, reply EXACTLY with: 'I do not have factual data regarding this query.'\n"
            "3. Your answer MUST NOT exceed 3 sentences under any circumstances.\n"
            "4. Do NOT provide investment advice or comparisons."
        )

        user_message = (
            f"Context:\n{context_string}\n\n"
            f"User Query: {query}"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast, economical, great instruction following
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0, # Complete deterministic facts
                max_tokens=150
            )
            
            raw_answer = response.choices[0].message.content.strip()

            # Post-processing: Apply constraints
            final_response = (
                f"{raw_answer}\n\n"
                f"Source: {source_url}\n"
                f"Last updated on {get_last_updated()}"
            )
            return final_response

        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return "I am currently experiencing a system error and cannot generate a response."
