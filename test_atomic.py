import json
from pathlib import Path

def test_atomic_logic():
    data_dir = Path("data/scraped")
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        print("No json files found.")
        return
        
    test_file = json_files[0]
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    scheme_name = data["scheme_name"]
    fields = data["fields"]
    
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
    
    print("\nOK: ATOMIC FACT CHUNK PREVIEW:")
    print("--------------------------------------------------")
    print(atomic_text)
    print("--------------------------------------------------")

if __name__ == "__main__":
    test_atomic_logic()
