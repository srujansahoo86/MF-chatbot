"""
chunker_embedder.py — Phase 3: Chunking & Embedding
Mutual Fund FAQ Chatbot

Reads scraped JSON scheme data, breaks them into perfectly formatted
atomic chunks (for precise factual retrieval) and contextual text chunks,
generates embeddings using HuggingFace 'all-MiniLM-L6-v2', and upserts
them into a local ChromaDB instance.
"""

import json
import logging
import uuid
from pathlib import Path
from datetime import datetime

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions

# ── Configuration ─────────────────────────────────────────────────────────────
SCRAPED_DATA_DIR = Path("data/scraped")
CHROMA_DB_DIR = Path("data/chroma")
COLLECTION_NAME = "mutual_funds"

# Using a lightweight, fast, local embedding model
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Using ChromaDB's default ONNX embedding model (bypasses Torch DLL issues)
logger.info("Initializing ONNX embedding model...")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

logger.info(f"Connecting to ChromaDB at '{CHROMA_DB_DIR}'...")
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

# Get or create the vector collection
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " "],
)

# ── Helper Functions ──────────────────────────────────────────────────────────

def create_atomic_fact_chunk(data: dict) -> list[dict]:
    """
    Creates a single dense factual chunk containing all exact numbers from the JSON fields.
    This guarantees that exact answers to FAQs (like expense ratio) are retrieved perfectly.
    """
    scheme_name = data["scheme_name"]
    fields = data["fields"]
    
    # 1. Structure the atomic text rigorously
    atomic_text = (
        f"FACT SHEET: {scheme_name}\n"
        f"AMC: {data['amc']} | Category: {data['category']}\n"
        f"Expense Ratio: {fields.get('expense_ratio', 'N/A')} | "
        f"Exit Load: {fields.get('exit_load', 'N/A')}\n"
        f"Minimum SIP: {fields.get('minimum_sip_amount', 'N/A')} | "
        f"Minimum Lumpsum: {fields.get('minimum_lumpsum_amount', 'N/A')}\n"
        f"Benchmark: {fields.get('benchmark_index', 'N/A')} | "
        f"Riskometer: {fields.get('riskometer', 'N/A')}\n"
        f"ELSS Lock-in: {fields.get('elss_lock_in_period', 'N/A')} | "
        f"Fund Manager: {fields.get('fund_manager', 'N/A')}\n"
        f"AUM (Assets Under Management): {fields.get('aum', 'N/A')}"
    )

    # 2. Build metadata
    chunk_id = f"{scheme_name.replace(' ', '_').lower()}_atomic_facts"
    metadata = {
        "chunk_type": "atomic_facts",
        "scheme_name": scheme_name,
        "amc": data["amc"],
        "category": data["category"],
        "source_url": data["source_url"],
        "scraped_at": data["scraped_at"],
    }
    
    return [{"chunk_id": chunk_id, "text": atomic_text, "metadata": metadata}]


def create_contextual_chunks(data: dict) -> list[dict]:
    """
    Splits the raw scraped text into chunks for broader questions (e.g. investment objective).
    """
    chunks_output = []
    raw_text = data.get("raw_text", "")
    scheme_name = data["scheme_name"]
    
    if not raw_text or raw_text == "N/A":
        return chunks_output

    text_chunks = text_splitter.split_text(raw_text)
    
    for i, chunk in enumerate(text_chunks):
        # Prefix the chunk with the scheme name so the LLM always knows what scheme it's reading
        prefixed_text = f"Context for {scheme_name}:\n{chunk}"
        chunk_id = f"{scheme_name.replace(' ', '_').lower()}_context_{i}"
        
        metadata = {
            "chunk_type": "context",
            "scheme_name": scheme_name,
            "amc": data["amc"],
            "category": data["category"],
            "source_url": data["source_url"],
            "scraped_at": data["scraped_at"],
            "chunk_index": i,
        }
        
        chunks_output.append({"chunk_id": chunk_id, "text": prefixed_text, "metadata": metadata})
        
    return chunks_output


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def process_and_embed():
    if not SCRAPED_DATA_DIR.exists():
        logger.error(f"Directory {SCRAPED_DATA_DIR} does not exist. Run scraper first.")
        return

    json_files = list(SCRAPED_DATA_DIR.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {SCRAPED_DATA_DIR}.")
        return

    logger.info(f"Found {len(json_files)} scraped scheme files.")

    all_texts = []
    all_metadatas = []
    all_ids = []

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Skip failed scrapes marked as N/A all around
            if data["fields"].get("expense_ratio") == "N/A" and data["fields"].get("riskometer") == "N/A":
                logger.warning(f"Skipping {data['scheme_name']}: appears to be empty or 404.")
                continue

            # 1. Create Atomic Fact Chunk
            atomic = create_atomic_fact_chunk(data)[0]
            all_texts.append(atomic["text"])
            all_metadatas.append(atomic["metadata"])
            all_ids.append(atomic["chunk_id"])

            # 2. Create Contextual Chunks
            context_chunks = create_contextual_chunks(data)
            for c in context_chunks:
                all_texts.append(c["text"])
                all_metadatas.append(c["metadata"])
                all_ids.append(c["chunk_id"])

            logger.info(f"Prepared chunks for: {data['scheme_name']} (1 atomic, {len(context_chunks)} context)")

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")

    if not all_texts:
        logger.warning("No valid chunks generated.")
        return

    logger.info("Upserting into ChromaDB...")
    collection.upsert(
        ids=all_ids,
        metadatas=all_metadatas,
        documents=all_texts
    )
    
    logger.info("✓ Successfully upserted all chunks into ChromaDB (embeddings handled by Chroma).")

if __name__ == "__main__":
    logger.info("============================================================")
    logger.info("Chunking & Embedding Service Started")
    logger.info("============================================================")
    process_and_embed()
    logger.info("============================================================")
    logger.info("Finished.")
