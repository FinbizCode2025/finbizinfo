
import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mistral import simulate_extract_balance_sheet

def test_latest_year_selection():
    # Sample OCR text where the first numeric column is a note index
    ocr_text = """
    BALANCE SHEET as of March 31, 2024
    Note No.   2024 (Rs.)   2023 (Rs.)
    Equity Share Capital   1   500000   500000
    Other Equity           2   1200000  1000000
    Trade Payables         3   300000   250000
    Current Assets:
    Cash & Equivalents     4   200000   150000
    Trade Receivables      5   400000   350000
    Inventory              6   600000   550000
    """
    
    # We want to make sure it picks the second numeric column (the large one) not the note index 1, 2, 3...
    result = simulate_extract_balance_sheet(ocr_text)
    
    print("Simulation Result for 2024 (Latest Year):")
    print(f"Equity: {result.get('equity', {}).get('total_equity')}")
    print(f"Trade Payables: {result.get('liabilities', {}).get('current_liabilities')}") # Simplified simulation mapping
    print(f"Cash: {result.get('assets', {}).get('cash_and_equivalents')}")
    
    # Check if Cash is 200000 (Latest) not 4 (Note)
    cash = result.get('assets', {}).get('cash_and_equivalents')
    if cash == 200000:
        print("✅ SUCCESS: Correctly picked latest year (skipped Note column)")
    elif cash == 150000:
        print("❌ FAILURE: Picked previous year instead of latest")
    elif cash == 4:
        print("❌ FAILURE: Picked Note index instead of latest year")
    else:
        print(f"❌ FAILURE: Picked unexpected value: {cash}")

if __name__ == "__main__":
    test_latest_year_selection()
