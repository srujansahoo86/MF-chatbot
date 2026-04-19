# Hosting Manual: Mutual Fund Chatbot (Production)

This manual explains how to host your chatbot on **Render.com** and set up the **GitHub Actions** automation for daily 9:15 AM data updates.

---

## 1. Prerequisites
1.  **GitHub Repository**: Your code must be pushed to a public or private GitHub repository.
2.  **Render Account**: Sign up for a free account at [Render.com](https://render.com).
3.  **API Keys**: Have your **GROQ_API_KEY** and **OPENAI_API_KEY** ready.

---

## 2. Setting Up the Web Service (FastAPI)
1.  Log in to the Render Dashboard and click **New > Web Service**.
2.  Connect your GitHub repository.
3.  **Basic Settings**:
    -   **Name**: `mf-chatbot-api`
    -   **Environment**: `Python 3`
    -   **Build Command**: `pip install -r scraper/requirements.txt -r api/requirements.txt -r rag_engine/requirements.txt`
    -   **Start Command**: `uvicorn api.server:app --host 0.0.0.0 --port $PORT`
4.  **Advanced > Environment Variables**:
    -   Add `GROQ_API_KEY` = `your_value`
    -   Add `OPENAI_API_KEY` = `your_value`
    -   *Note*: The `PORT` is handled automatically by Render.

---

## 3. How the Daily Update Logic Works (GitOps)
Your chatbot is configured as a **"Set and Forget"** system using a GitOps workflow:

1.  **The Alarm Clock (GitHub Actions)**:
    -   Every day at **9:15 AM IST**, GitHub wakes up a small runner.
    -   This runner executes `python scraper/scraper.py`.
2.  **The Update (Git Push)**:
    -   If the scraper finds new NAV/Expense data, GitHub Actions will **Commit and Push** those new JSON files back into your repository.
3.  **The Deployment (Render Auto-Deploy)**:
    -   Render sees the new commit (the fresh data).
    -   It automatically rebuilds and restarts your chatbot with the latest facts.
    -   **No manual work is required.**

---

## 4. Local Persistence Warning
> [!WARNING]
> Because cloud hosting platforms like Render have **ephemeral storage**, any data scraped *manually* on the server will be lost when it restarts. **Always rely on the GitHub Actions workflow** to update data, as it ensures the facts are permanently stored in your repository.

---

## 5. Troubleshooting
- **Site not loading?**: Check the **Events** tab in Render to see if the build failed. Ensure all `requirements.txt` are up to date.
- **Data not refreshing?**: Check the **Actions** tab in GitHub to see if the `data_refresh` workflow ran successfully at 9:15 AM.
