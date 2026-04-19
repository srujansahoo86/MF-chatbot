"""
server.py — Multi-Provider Robust Mode (Groq + OpenAI)
Bypasses all external module imports that might trigger DLL issues.
"""
import logging
import os
import json
import re
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from groq import Groq

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
SCRAPED_DATA_DIR = Path("data/scraped")
TIMESTAMP_FILE = Path("data/last_updated.json")
UI_DIR = Path(__file__).parent.parent / "ui"

# ── Robust Local Logic (Inlined to avoid broken imports) ─────────────────────

def check_intent(query: str) -> dict:
    query_lower = query.lower()
    
    # 1. Privacy Guardrail (PII Filter)
    # Checks for PAN, Aadhaar (12-digit), Phone Numbers (10-digit), and Email
    PII_PATTERNS = {
        "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
        "Aadhaar": r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b",
        "Phone": r"\b\d{10}\b",
        "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    }
    for label, pattern in PII_PATTERNS.items():
        if re.search(pattern, query):
            return {
                "blocked": True, 
                "reason": "pii", 
                "message": f"I detected potential sensitive information ({label}). For your security, please do not share personal details. I only provide factual fund information."
            }

    # 2. Advisory Guardrail
    ADVISORY_PATTERNS = [r"\b(should|could|would)\b.*\b(invest|buy|sell|allocate)\b", r"\brecommend\b"]
    for pattern in ADVISORY_PATTERNS:
        if re.search(pattern, query_lower):
            return {
                "blocked": True, 
                "reason": "advisory", 
                "message": "I cannot provide investment advice. Please consult a professional. For educational resources on mutual funds, visit AMFI: https://www.amfiindia.com/investor-corner/education/interest-rates.html"
            }
    return {"blocked": False}

def get_last_updated():
    try:
        if TIMESTAMP_FILE.exists():
            with open(TIMESTAMP_FILE, "r") as f:
                return json.load(f).get("last_updated", "N/A")
    except: pass
    return "N/A"

class SimpleRetriever:
    def __init__(self):
        self.data = []
        self._load_data()

    def _load_data(self):
        if SCRAPED_DATA_DIR.exists():
            for f_path in SCRAPED_DATA_DIR.glob("*.json"):
                try:
                    with open(f_path, "r", encoding="utf-8") as f:
                        self.data.append(json.load(f))
                except: pass

    def get_global_summary(self) -> str:
        """Provides a map of all available funds if no specific match is found."""
        schemes = [s['scheme_name'] for s in self.data]
        categories = set(s['category'] for s in self.data)
        return (
            "I have factual data for the following SBI Mutual Funds:\n"
            f"- {', '.join(schemes)}\n"
            f"Available Categories: {', '.join(categories)}"
        )

    def query(self, text: str) -> List[Dict]:
        query_tokens = set(re.findall(r'\w+', text.lower()))
        scored_results = []

        for s in self.data:
            score = 0
            scheme_name = s['scheme_name'].lower()
            category = s['category'].lower()
            amc = s['amc'].lower()
            
            # Weighted scoring (substring matching for better recall)
            for token in query_tokens:
                if token in scheme_name.lower() or scheme_name.lower().startswith(token): score += 5 
                if token in category.lower(): score += 3
                if token in amc.lower(): score += 1
            
            # Global search override (if user asks for 'all' or 'funds')
            if any(term in text.lower() for term in ["all", "list", "show", "funds"]):
                score += 1
            
            if score > 0:
                f = s.get('fields', {})
                content = (
                    f"FUND: {s['scheme_name']} | CATEGORY: {s['category']}\n"
                    f"NAV: {f.get('nav', 'N/A')} (as of {s.get('scraped_at', 'N/A')[:10]})\n"
                    f"Risk: {f.get('riskometer', 'N/A')} | Expense Ratio: {f.get('expense_ratio', 'N/A')}\n"
                    f"Exit Load: {f.get('exit_load', 'N/A')}\n"
                    f"AUM: {f.get('aum', 'N/A')} | Min SIP: {f.get('minimum_sip_amount', 'N/A')}\n"
                    f"Objective: {s.get('raw_text', '')[:300]}..."
                )
                scored_results.append((score, {
                    "text": content,
                    "source_url": s.get('source_url', 'N/A'),
                    "scheme": s['scheme_name']
                }))

        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_results = [item[1] for item in scored_results[:5]]

        # Fallback: Global Summary
        if not top_results:
            return [{
                "text": self.get_global_summary(),
                "source_url": "N/A",
                "scheme": "System Map"
            }]
            
        return top_results

# ── App & Globals ─────────────────────────────────────────────────────────────
app = FastAPI(title="Mutual Fund FAQ API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

retriever = None
openai_client = None
groq_client = None

@app.on_event("startup")
async def startup_event():
    global retriever, openai_client, groq_client
    logger.info("Starting multi-provider robust mode...")
    retriever = SimpleRetriever()
    
    # Init OpenAI
    oa_key = os.environ.get("OPENAI_API_KEY")
    if oa_key:
        openai_client = OpenAI(api_key=oa_key)
        logger.info("OpenAI client initialized.")

    # Init Groq
    g_key = os.environ.get("GROQ_API_KEY")
    if g_key:
        groq_client = Groq(api_key=g_key)
        logger.info("Groq client initialized.")

LAST_LOADED_TIMESTAMP = None

# ── Session Store ─────────────────────────────────────────────────────────────
SESSIONS: Dict[str, List[Dict]] = {} # Simple in-memory session store

def get_session_history(session_id: str) -> List[Dict]:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = []
    return SESSIONS[session_id]

def add_to_history(session_id: str, role: str, content: str):
    history = get_session_history(session_id)
    history.append({"role": role, "content": content})
    # Keep last 10 messages to avoid context bloat
    if len(history) > 10:
        SESSIONS[session_id] = history[-10:]

def check_for_updates():
    """Refreshes the retriever cache if the data files have been updated."""
    global retriever, LAST_LOADED_TIMESTAMP
    try:
        if TIMESTAMP_FILE.exists():
            with open(TIMESTAMP_FILE, "r") as f:
                ts_data = json.load(f)
                new_ts = ts_data.get("last_updated_iso")
                if new_ts != LAST_LOADED_TIMESTAMP:
                    logger.info(f"Detected fresh data ({new_ts}). Reloading cache...")
                    retriever = SimpleRetriever()
                    LAST_LOADED_TIMESTAMP = new_ts
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")

# ── API Models ────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default_user"

class ChatResponse(BaseModel):
    answer: str
    status: str

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Auto-reload if fresh data was scraped in the background
    check_for_updates()
    
    user_input = request.query.strip()
    
    # 1. Guardrails
    intent = check_intent(user_input)
    if intent["blocked"]:
        return ChatResponse(answer=intent["message"], status="intercepted")

    # 2. Session Management
    session_id = request.session_id
    history = get_session_history(session_id)

    # 3. Retrieval
    chunks = retriever.query(user_input)
    logger.info(f"Retrieved {len(chunks)} chunks for query: {user_input} (Session: {session_id})")
    context = "\n".join([c['text'] for c in chunks])
    source = chunks[0]['source_url'] if chunks else "N/A"

    # 4. Prompt Construction
    system_prompt = (
        "You are a factual Mutual Fund Assistant. Provide detailed, structured answers. "
        "When listing multiple funds, ensure all relevant funds from the context are mentioned. "
        "Use ONLY the provided context. If the answer is not in the context, politely say so. "
        f"\nContext: {context}"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    # 5. Generation
    answer = ""
    if groq_client:
        try:
            logger.info(f"Generating via Groq... (Session: {session_id})")
            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0
            )
            answer = chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq error: {e}")

    if not answer and openai_client:
        try:
            logger.info(f"Generating via OpenAI... (Session: {session_id})")
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0
            )
            answer = resp.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")

    if answer:
        # Save to history
        add_to_history(session_id, "user", user_input)
        add_to_history(session_id, "assistant", answer)
        
        final_answer = f"{answer}\n\nSource: {source}\n“Last updated from sources: {get_last_updated()}”"
        return ChatResponse(answer=final_answer, status="success")

    return ChatResponse(answer=f"I am currently experiencing a system error with my AI providers. (Local context preview: {context[:100]}...)", status="error")

@app.get("/")
def home():
    return FileResponse(UI_DIR / "basic_index.html")

app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    # Use dynamic port for cloud hosting (Render/Heroku/etc)
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
