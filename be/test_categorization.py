
import sys
import os
import json
from dotenv import load_dotenv

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app import calculate_financial_ratios

def test_categorization():
    # Simulated Mistral data (based on Dabur 2024 results)
    mistral_data = {
      "year": "2024",
      "assets": {
        "total_assets": 10532.81,
        "current_assets": 3432.37,
        "cash_and_equivalents": 10.77,
        "inventories": 1200.0,
        "trade_receivables": 800.0,
        "property_plant_equipment": 6000.0
      },
      "liabilities": {
        "total_liabilities": 3617.44,
        "current_liabilities": 2891.03,
        "trade_payables": 1500.0,
        "short_term_borrowings": 500.0,
        "long_term_borrowings": 400.0
      },
      "equity": {
        "total_equity": 6915.37
      },
      "p_and_l": {
        "revenue": 9135.6,
        "net_profit": 1509.21,
        "ebitda": 2256.7,
        "interest_expense": 81.14
      }
    }
    
    print("Testing Unified Ratio Categorization (app.py)...")
    resp = calculate_financial_ratios(mistral_financials=mistral_data)
    ratios = resp.get("ratios", {})
    
    print("\nCategorized Ratios Structure:")
    for cat in ratios:
        if isinstance(ratios[cat], dict):
            print(f"- {cat}: {len(ratios[cat])} ratios")
    
    # Check specific categories
    if "liquidity_ratios" in ratios and ratios["liquidity_ratios"].get("current_ratio"):
        print(f"\n✅ Liquidity Ratios Found (CR: {ratios['liquidity_ratios']['current_ratio']})")
    else:
        print("\n❌ Liquidity Ratios Missing")
        
    if "solvency_ratios" in ratios and ratios["solvency_ratios"].get("debt_to_equity"):
        print(f"✅ Solvency Ratios Found (D/E: {ratios['solvency_ratios']['debt_to_equity']})")
    else:
        print("❌ Solvency Ratios Missing")

    if "summary" in resp.get("ratios", {}) and resp["ratios"]["summary"].get("total_components_calculated") > 0:
        print(f"✅ Summary Stats Found: {resp['ratios']['summary']['total_components_calculated']} ratios total")
    else:
        print("❌ Summary Stats missing or 0")

if __name__ == "__main__":
    test_categorization()
