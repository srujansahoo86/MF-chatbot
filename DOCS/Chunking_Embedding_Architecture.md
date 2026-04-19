# Chunking & Embedding Architecture

This document details how scraped Groww scheme page content is processed into vector-searchable chunks and stored in the Vector Store. This pipeline is triggered automatically by the **GitHub Actions Scheduler** (daily at 9:15 AM IST) after the Scraping Service completes successfully.

---

## Overview

```
Scraped Raw HTML Text
        |
        v
  [ Text Cleaning ]
        |
        v
  [ Chunking Layer ]
        |
        v
  [ Metadata Tagging ]
        |
        v
  [ Embedding Model ]
        |
        v
  [ Vector Store Upsert ]
```

---

## Step 1: Text Cleaning

Before chunking, raw scraped HTML text is cleaned to remove noise.

| Task | Detail |
|------|--------|
| **HTML Tag Stripping** | Remove all HTML tags using BeautifulSoup `.get_text()` |
| **Whitespace Normalization** | Collapse multiple spaces, tabs, and newlines |
| **Boilerplate Removal** | Strip navigation bars, cookie banners, footer links, and disclaimers unrelated to fund facts |
| **Unicode Normalization** | Normalize special characters (e.g., `₹`, `%`, `–`) to standard forms |
| **Output** | Clean plain text string per scheme URL, ready for chunking |

---

## Step 2: Chunking Strategy

The cleaned text is split into overlapping chunks to ensure no factual information is lost across boundaries.

### Chunking Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Chunk Size** | 500 tokens | Optimal for embedding models; small enough for precise retrieval |
| **Chunk Overlap** | 100 tokens | Prevents loss of context at chunk boundaries |
| **Chunking Method** | Recursive Character Text Splitter | Splits on natural boundaries: `\n\n`, `\n`, `.`, ` ` in priority order |

### Chunking Rules

*   **Preserve Atomic Facts**: Numeric values like expense ratios, exit loads, and lock-in periods must **not** be split across chunks.
*   **Scheme Isolation**: Chunks from different scheme pages are **never merged** — each chunk always belongs to exactly one scheme.
*   **Section-Aware Splitting**: Key sections (e.g., *Fund Details*, *Returns*, *Risk*) are identified and kept as self-contained chunks wherever possible.

### Example

**Raw cleaned text snippet:**
```
SBI ELSS Tax Saver Fund - Direct Plan - Growth
Exit Load: Nil
Expense Ratio: 0.97%
ELSS Lock-in Period: 3 years (mandatory)
Minimum SIP: ₹500/month
Benchmark: BSE 500 TRI
Riskometer: Very High
```

**Chunk output (single chunk — atomic, intact):**
```
Scheme: SBI ELSS Tax Saver Fund (Direct Growth)
Exit Load: Nil | Expense Ratio: 0.97% | ELSS Lock-in: 3 years
Min SIP: ₹500/month | Benchmark: BSE 500 TRI | Risk: Very High
```

---

## Step 3: Metadata Tagging

Every chunk is enriched with metadata **before** being sent to the embedding model. This metadata is stored alongside the vector in the Vector Store and is used for:
- Citation generation (Source URL)
- Response footer generation (Last Updated date)
- Scheme-level filtering during retrieval

### Metadata Schema per Chunk

```json
{
  "chunk_id": "sbi_elss_chunk_003",
  "scheme_name": "SBI ELSS Tax Saver Fund (Direct Growth)",
  "amc": "SBI Mutual Fund",
  "category": "ELSS / Tax Saving",
  "source_url": "https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
  "scraped_at": "2026-04-14T03:45:00Z",
  "last_updated": "2026-04-14",
  "chunk_index": 3,
  "total_chunks": 8
}
```

---

## Step 4: Embedding Model

Each chunk's text is converted into a dense vector representation using an embedding model.

| Property | Detail |
|----------|--------|
| **Model** | `text-embedding-3-small` (OpenAI) or `all-MiniLM-L6-v2` (open-source via HuggingFace) |
| **Embedding Dimensions** | 1536 (OpenAI) / 384 (MiniLM) |
| **Input** | Chunk text (plain string, max 500 tokens) |
| **Output** | Dense float vector representing semantic meaning |
| **Batch Processing** | Chunks are embedded in batches of 50 to optimise API cost and speed |
| **Retry Logic** | On API timeout or rate limit, retry up to 3 times with exponential backoff |

> **Chosen Model**: `text-embedding-3-small` is recommended for production due to superior multilingual and financial-domain understanding. Switch to `all-MiniLM-L6-v2` for a fully offline/open-source setup.

---

## Step 5: Vector Store Upsert

Embedded chunks are written (upserted) into the Vector Store, replacing any previously stored vectors for the same `chunk_id`.

| Property | Detail |
|----------|--------|
| **Vector Store** | ChromaDB (local) or Pinecone (hosted) |
| **Upsert Strategy** | Upsert by `chunk_id` — updates existing vectors if re-scraped, inserts new ones |
| **Index Namespace** | Separate namespace per scheme (e.g., `sbi_elss`, `sbi_contra`) for clean retrieval scoping |
| **Similarity Metric** | Cosine Similarity |
| **Post-Upsert** | Write updated `last_updated.json` to repository and trigger GitHub Actions success notification |

---

## Full Pipeline Flow Summary

```
GitHub Actions (9:15 AM IST)
        |
        v
  Scraping Service
  (fetches 5 Groww URLs)
        |
        v
  Text Cleaning
  (strip HTML, normalize whitespace)
        |
        v
  Chunking
  (500 tokens, 100 overlap, recursive splitter)
        |
        v
  Metadata Tagging
  (scheme name, source URL, scraped_at, chunk_id)
        |
        v
  Embedding
  (text-embedding-3-small, batch=50)
        |
        v
  Vector Store Upsert
  (ChromaDB / Pinecone, upsert by chunk_id)
        |
        v
  last_updated.json committed to repo
  (used in chatbot response footer)
```

---

## Error Handling

| Stage | Failure Scenario | Handling |
|-------|-----------------|----------|
| Scraping | URL unreachable / bot-blocked | Log error, skip scheme, continue with remaining URLs |
| Chunking | Empty text after cleaning | Skip chunk, log warning |
| Embedding | API timeout / rate limit | Retry 3x with exponential backoff; fail job if exceeded |
| Vector Upsert | Connection error | Retry 3x; roll back to previous snapshot if all retries fail |
| Overall Job | Any unhandled exception | GitHub Actions marks workflow as FAILED; Slack/email alert sent |

---

## Related Documents

*   [RAG Architecture](RAG_Architecture.md) — Overall system architecture
*   [Problem Statement](problemstatement.md) — Project requirements and constraints
