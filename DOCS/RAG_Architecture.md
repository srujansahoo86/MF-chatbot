# Mutual Fund FAQ Assistant: RAG Architecture

This document details the RAG (Retrieval-Augmented Generation) architecture for the Mutual Fund FAQ Assistant, aligned with the rules and constraints outlined in the project's [problem statement](problemstatement.md).

## 1. System Overview
The architecture is designed to prioritize **accuracy over intelligence**. It operates as a strict, facts-only assistant drawing context exclusively from a curated corpus of 15-25 official documents and rejecting advisory, comparison, or speculative intents.

### High-Level Block Diagram
1. **Scheduler** -> Triggers daily at 9:15 AM IST
2. **Scraping Service** -> Fetches latest content from 5 Groww scheme URLs
3. **User Input** -> UI (Minimal Interface)
4. **Intent Guardrail** -> Classifier (Checks for PII or Advisory intents)
5. **Retrieval Layer** -> Vector Database (Knowledge Base)
6. **Generation Layer** -> LLM generation strictly bounded by context.
7. **Post-Processing Guardrail** -> Truncation to 3 sentences, citation appending.

---

## 2. Ingestion & Data Pipeline

The pipeline transforms official AMC, AMFI, and SEBI documents into accurately retrievable chunks.

*   **Corpus Selection**: **AMC: SBI Mutual Fund** | 5 schemes selected with category diversity. The Groww scheme pages below are the **direct data sources** used for ingestion. No PDFs are used at this stage — content is scraped from these live web pages.

    | # | Scheme Name | Category | Data Source URL |
    |---|-------------|----------|-----------------|
    | 1 | SBI Children's Fund – Investment Plan (Direct Growth) | Children's Fund | [groww.in](https://groww.in/mutual-funds/sbi-children's-fund-investment-plan-direct-growth) |
    | 2 | SBI ELSS Tax Saver Fund (Direct Growth) | ELSS / Tax Saving | [groww.in](https://groww.in/mutual-funds/sbi-elss-tax-saver-fund-direct-growth) |
    | 3 | SBI Contra Fund (Direct Growth) | Contra / Value | [groww.in](https://groww.in/mutual-funds/sbi-contra-fund-direct-growth) |
    | 4 | SBI Balanced Advantage Fund (Direct Growth) | Balanced Advantage / Dynamic Asset Allocation | [groww.in](https://groww.in/mutual-funds/sbi-balanced-advantage-fund-direct-growth) |
    | 5 | SBI Children's Fund – Savings Plan (Direct Growth) | Children's Fund | [groww.in](https://groww.in/mutual-funds/sbi-children's-fund-savings-plan-direct-growth) |

### 2a. Scheduler — GitHub Actions

The Scheduler is implemented using a **GitHub Actions workflow** (`schedule` trigger) that kicks off the full data refresh pipeline automatically every day.

| Property | Detail |
|----------|--------|
| **Platform** | GitHub Actions (`on: schedule`) |
| **Trigger Time** | Every day at **9:15 AM IST** = `3:45 AM UTC` |
| **Cron Expression** | `45 3 * * *` (UTC) |
| **Runner** | `ubuntu-latest` |
| **Action** | Runs the Scraping Service → Chunking → Embedding pipeline in sequence |
| **On Success** | Refreshes Vector Store index; commits updated `last_updated.json` timestamp to repo |
| **On Failure** | GitHub Actions marks the run as failed; retains last successful data snapshot; no stale data served without a timestamp warning |
| **Timestamp Update** | Sets the `Last Updated` metadata field used in every chatbot response footer |

**GitHub Actions Workflow Trigger (`.github/workflows/data_refresh.yml`)**:
```yaml
on:
  schedule:
    - cron: '45 3 * * *'   # 9:15 AM IST daily
  workflow_dispatch:         # Allow manual trigger from GitHub UI
```

> See **[Chunking & Embedding Architecture](Chunking_Embedding_Architecture.md)** for the detailed pipeline that runs after scraping completes.

### 2b. Scraping Service

The Scraping Service is responsible for fetching and extracting the latest factual content from the 5 defined Groww scheme URLs.

*   **Input**: The 5 Groww scheme URLs defined in the Corpus Selection table above.
*   **Method**: HTTP GET request to each URL followed by HTML parsing (e.g., via BeautifulSoup / Playwright for JS-rendered pages).
*   **Fields Extracted per Scheme**:
    *   Expense Ratio
    *   Exit Load (amount & period)
    *   Minimum SIP / Lump Sum Amount
    *   Benchmark Index
    *   Riskometer classification
    *   ELSS lock-in period (if applicable)
    *   Fund Manager name
    *   AUM (Assets Under Management)
*   **Output**: Clean, structured text per scheme page, passed to the Chunking & Embedding stage.
*   **Source URL Retention**: The exact scraped URL is attached as metadata to every chunk for downstream citation.

---

*   **Parsing Layer**: 
    *   **Web scraping only** (no PDFs). Each Groww scheme page is scraped as HTML and parsed to extract structured fields such as Expense Ratio, Exit Load, Minimum SIP Amount, Benchmark Index, Riskometer classification, and ELSS lock-in period.
    *   The scraped page URL is retained as the `Source URL` metadata for citation in every response.
*   **Chunking Strategy**: 
    *   Semantic chunking (around 500-1000 tokens).
    *   Overlap ensures no loss of context across document pages.
    *   *Crucial Metadata Mapping*: Each chunk is stored with metadata including the **Source URL**, **Creation/Last Updated Date**, and **Scheme Name**.
*   **Embedding & Vector Store**: 
    *   An embedding model assigns vector representations to each chunk. 
    *   Stored in a persistent Vector Database index.

---

## 3. Query & Retrieval Architecture (RAG)

*   **Intent Router & Pre-Guardrail**:
    *   *Refusal Check*: Detects if the query is asking for investment advice ("Which fund is better?", "Should I invest?") or performance comparisons. If triggered, it immediately short-circuits the retrieval and outputs a polite refusal template routing them to an AMFI/SEBI resource.
    *   *PII Filter*: Rejects inputs containing PAN, Aadhaar, phone numbers, or emails.
*   **Vector Search**:
    *   The validated query is embedded and an exact or cosine similarity search is run against the Vector Store.
    *   Only top-K exact semantic factual matches are returned as context.

---

## 4. Generation Layer & LLM Prompting

The LLM is prompted with heavy constraints prioritizing safety and exact extraction.

### System Prompt Constraints
1.  **Fact Extraction Only**: Extract facts strictly from the provided context. If the answer is not in the context, explicitly state "I don't have this information."
2.  **Length Bound**: Limit the response to a maximum of **3 sentences**.
3.  **Citation Guarantee**: Extract the `Source URL` from the retrieved chunk metadata and insert it at the end of the response.

### Footer Post-Processing
After the LLM generates the response, the backend pipeline appends the required text dynamically:
> `"Last updated from sources: <date>"` 

---

## 5. System Components & UI

*   **Frontend (Minimal UI)**:
    *   Displays a Welcome message.
    *   Presents 3 quick-start example questions (e.g., *"What is the exit load for [Scheme]?"*).
    *   Persistent Disclaimer overlay: **"Facts-only. No investment advice."**
*   **Backend (Thread Management)**:
    *   Provides **Multiple Chat Thread Support**.
    *   Maintains thread histories independently using an Ephemeral Session Store (like Redis) keyed by an anonymized Session ID. 
    *   *Data Policy*: Drops session histories immediately upon session close; zero storage of User PII.
