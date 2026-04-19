# Mutual Fund Chatbot - Process Flow Summary

This diagram explains how the automated "Set and Forget" update system works.

```mermaid
graph TD
    subgraph "Automation Layer (Daily at 9:15 AM)"
        Task[Windows Task Scheduler] -->|Triggers| VBS[silent_refresh.vbs]
        VBS -->|Runs Invisibly| Runner[refresh_data.py]
    end

    subgraph "Data Acquisition"
        Runner -->|Execute| Scraper[Playwright Scraper]
        Scraper -->|Fetch Factual Data| Groww[Groww Website]
        Groww -->|Return NAV/AUM| Scraper
        Scraper -->|Update| JSON[JSON Data Store<br/>/data/scraped/]
    end

    subgraph "AI Chatbot Layer"
        JSON -->|New Timestamp| Server[FastAPI Server]
        Server -->|Auto-Reload| Memory[In-Memory Cache]
        User[User Query] --> Server
        Server -->|Latest Factual Info| Answer[User Receives Answer]
    end

    style Task fill:#f9f,stroke:#333,stroke-width:2px
    style JSON fill:#bbf,stroke:#333,stroke-width:2px
    style Server fill:#dfd,stroke:#333,stroke-width:2px
```

### Key Components:
1.  **The Trigger**: Windows Task Scheduler starts the process every morning at 9:15 AM.
2.  **The Ghost**: `silent_refresh.vbs` ensures the update happens in the background without disturbing your work.
3.  **The Collector**: `scraper.py` (via Playwright) visits the mutual fund pages and extracts the latest prices.
4.  **The Self-Healer**: Your Chatbot API automatically "notices" the new data and refreshes itself on the fly.
