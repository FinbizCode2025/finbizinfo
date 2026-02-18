
import sys
import os
import json
from dotenv import load_dotenv

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from mistral import extract_balance_sheet, Mistral, calculate_financial_ratios

def test_full_extraction():
    # Sample OCR text with both Balance Sheet and P&L data for 2024 and 2023
    ocr_text = """
    STANDALONE BALANCE SHEET as at 31 March 2024
    Particulars Note 31 March 2024 31 March 2023
    Total assets      10,532.81  9,352.44 
    Current assets    3,432.37   2,231.28 
    Cash and equivalents 15 10.77 15.35
    Total equity      6,915.37   6,286.88 
    Total liabilities 3,617.44   3,065.56 
    Current liabilities 2,891.03  2,631.52 

    STANDALONE STATEMENT OF PROFIT AND LOSS for the year ended 31 March 2024
    Particulars Note 31 March 2024 31 March 2023
    Revenue from operations 34 9,135.60 8,684.35 
    Total income      9,553.22  9,076.52 
    Finance costs     39 81.14 46.37 
    Net profit for the year 1,509.21 1,373.26
    EBITDA            2,256.70 2,058.32
    """
    
    print("Testing Mistral Initialization...")
    try:
        from mistralai import Mistral as MistralClient
        print("✅ Mistral class imported successfully from mistralai package")
    except Exception as e:
        print(f"❌ Mistral import failed: {e}")
        return

    # Mocking the client or checking if simulated mode is on
    from mistral import SIMULATE_MISTRAL
    print(f"Mistral Simulation Mode: {SIMULATE_MISTRAL}")
    
    # We'll use the heuristic simulation to verify the logic if no API key
    mistral_data = extract_balance_sheet(ocr_text, None)
    
    print("\nExtracted Data (Latest Year 2024):")
    print(json.dumps(mistral_data, indent=2))
    
    # Verify values
    assets = mistral_data.get("assets", {})
    p_and_l = mistral_data.get("p_and_l", {})
    
    success = True
    if assets.get("total_assets") != 10532.81:
        print(f"❌ Wrong total_assets: {assets.get('total_assets')} (expected 10532.81)")
        success = False
    if p_and_l.get("revenue") != 9135.60:
        print(f"❌ Wrong revenue: {p_and_l.get('revenue')} (expected 9135.60)")
        success = False
    if p_and_l.get("net_profit") != 1509.21:
        print(f"❌ Wrong net_profit: {p_and_l.get('net_profit')} (expected 1509.21)")
        success = False
        
    if success:
        print("\n✅ SUCCESS: Mistral extraction logic correctly picked 2024 data for both BS and P&L")
        
    # Test Ratios
    ratios = calculate_financial_ratios(mistral_data)
    print("\nCalculated Ratios:")
    print(json.dumps(ratios, indent=2))
    
    if ratios.get("current_ratio") == round(3432.37 / 2891.03, 2):
        print("✅ Current Ratio correct")
    else:
         print(f"❌ Current Ratio incorrect: {ratios.get('current_ratio')}")

if __name__ == "__main__":
    test_full_extraction()
