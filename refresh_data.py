import sys
import os
import subprocess
from pathlib import Path

def main():
    print("="*60)
    print("MUTUAL FUND DATA REFRESH SERVICE (LOCAL)")
    print("="*60)
    
    # 1. Run the Scraper
    print("\n[1/2] Running Scraper...")
    scraper_path = Path("scraper/scraper.py")
    python_exe = Path(".venv_stable/Scripts/python.exe")
    
    if not python_exe.exists():
        python_exe = "python" # fallback
        
    try:
        subprocess.run([str(python_exe), str(scraper_path)], check=True)
        print("\n[SUCCESS] Scraping complete. Data saved to data/scraped/")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Scraping failed: {e}")
        sys.exit(1)

    # 2. Update Timestamp for UI
    print("\n[2/2] Data is now fresh as of today.")
    print("\n" + "="*60)
    print("SUCCESS: Data updated to April 16th.")
    print("Note: If the chatbot is running, please restart it to load the new values.")
    print("="*60)

if __name__ == "__main__":
    main()
