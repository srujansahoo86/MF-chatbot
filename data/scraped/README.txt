This directory stores raw scraped JSON output from the Scraping Service.

One file is created per scheme after each successful run:
  - sbi_elss_tax_saver_fund_direct_growth.json
  - sbi_contra_fund_direct_growth.json
  - sbi_balanced_advantage_fund_direct_growth.json
  - sbi_childrens_fund_investment_plan_direct_growth.json
  - sbi_childrens_fund_savings_plan_direct_growth.json

These files are consumed by the Chunking & Embedding pipeline (Phase 3).
This folder is gitignored for scraped data but tracked for structure.
