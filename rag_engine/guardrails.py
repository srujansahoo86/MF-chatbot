"""
guardrails.py — Safety & Intent Interceptor

Pre-retrieval layer that strictly blocks:
1. Advisory intents ("Should I invest?", "Which is better?")
2. PII / Account queries ("What is my balance?")
"""
import re

ADVISORY_PATTERNS = [
    r"\b(should|could|would)\b.*\b(invest|buy|sell|allocate)\b",
    r"\bwhich\b.*\b(is better|is best|should I choose)\b",
    r"\b(recommend|recommendation|advice|suggest)\b",
    r"\b(my portfolio|my money|my investment)\b",
    r"\b(is this a good)\b"
]

PII_PATTERNS = [
    r"\b(my balance|my pan|my pan card|ssn|social security)\b",
    r"\b(account number|folio number|password|login)\b"
]

def check_intent(query: str) -> dict:
    """
    Checks the user query against prohibited patterns.
    Returns:
        {"blocked": True, "reason": "advisory", "message": "..."}
        or
        {"blocked": False}
    """
    query_lower = query.lower()

    # 1. Check PII
    for pattern in PII_PATTERNS:
        if re.search(pattern, query_lower):
            return {
                "blocked": True,
                "reason": "PII",
                "message": "I am a factual FAQ assistant. For your security, please do not share personal account details or PII."
            }

    # 2. Check Advisory
    for pattern in ADVISORY_PATTERNS:
        if re.search(pattern, query_lower):
            return {
                "blocked": True,
                "reason": "advisory",
                "message": "I am an automated informational assistant. I am strictly prohibited from providing investment advice, recommendations, or fund comparisons. Please consult a registered financial advisor."
            }

    return {"blocked": False}
