#!/usr/bin/env python
"""Test expanded financial ratio calculations."""

from financial_analyzer import FinancialAnalyzer

# Sample balance sheet text with various financial items
sample_text = """
BALANCE SHEET - ABC COMPANY LIMITED
As of December 31, 2023

ASSETS
Current Assets:
  Cash and Cash Equivalents: 50,00,000
  Accounts Receivable: 75,00,000
  Inventory: 60,00,000
Total Current Assets: 185,00,000

Non-Current Assets:
  Property, Plant & Equipment: 250,00,000
  Goodwill: 30,00,000
Total Non-Current Assets: 280,00,000
TOTAL ASSETS: 465,00,000

LIABILITIES
Current Liabilities:
  Accounts Payable: 40,00,000
  Short-term Debt: 20,00,000
Total Current Liabilities: 60,00,000

Non-Current Liabilities:
  Long-term Debt: 80,00,000
Total Non-Current Liabilities: 80,00,000
TOTAL LIABILITIES: 140,00,000

EQUITY:
  Common Stock: 200,00,000
  Retained Earnings: 125,00,000
TOTAL EQUITY: 325,00,000

TOTAL LIABILITIES AND EQUITY: 465,00,000

PROFIT AND LOSS STATEMENT
Year ended December 31, 2023

Revenue: 500,00,000
Cost of Goods Sold: 300,00,000
Gross Profit: 200,00,000
Operating Expenses: 80,00,000
Operating Income: 120,00,000
Interest Expense: 5,00,000
Earnings Before Tax: 115,00,000
Income Tax: 25,00,000
Net Income: 90,00,000
"""

if __name__ == "__main__":
    analyzer = FinancialAnalyzer()
    
    print("=" * 80)
    print("TESTING EXPANDED FINANCIAL RATIO CALCULATIONS")
    print("=" * 80)
    print()
    
    # Calculate ratios
    ratios = analyzer.calculate_financial_ratios_from_text(sample_text)
    
    print("Ratio categories found:")
    for key in ratios.keys():
        if not key.startswith('_'):
            print(f"  - {key}")
    print()
    
    # Display organized ratios
    print("DETAILED BREAKDOWN:")
    print()
    
    # Liquidity Ratios
    print("LIQUIDITY RATIOS:")
    print("-" * 40)
    for metric, value in ratios.get('liquidity_ratios', {}).items():
        if value is not None:
            print(f"  {metric:<30} = {value:.4f}" if isinstance(value, float) else f"  {metric:<30} = {value:,.2f}")
    print()
    
    # Profitability Ratios
    print("PROFITABILITY RATIOS:")
    print("-" * 40)
    for metric, value in ratios.get('profitability_ratios', {}).items():
        if value is not None:
            if metric.endswith('_margin'):
                print(f"  {metric:<30} = {value*100:.2f}%")
            elif metric.startswith('return_'):
                print(f"  {metric:<30} = {value*100:.2f}%")
            else:
                print(f"  {metric:<30} = {value:,.2f}" if value > 1 else f"  {metric:<30} = {value:.4f}")
    print()
    
    # Solvency/Leverage Ratios
    print("SOLVENCY/LEVERAGE RATIOS:")
    print("-" * 40)
    for metric, value in ratios.get('solvency_ratios', {}).items():
        if value is not None:
            print(f"  {metric:<30} = {value:.4f}")
    print()
    
    # Efficiency Ratios
    print("EFFICIENCY RATIOS:")
    print("-" * 40)
    for metric, value in ratios.get('efficiency_ratios', {}).items():
        if value is not None:
            if metric.endswith('_period') or metric.startswith('days_'):
                print(f"  {metric:<30} = {value:.2f} days")
            else:
                print(f"  {metric:<30} = {value:.4f}")
    print()
    
    # Format as table
    print("=" * 80)
    print("FORMATTED TABLE OUTPUT:")
    print("=" * 80)
    print()
    formatted_output = analyzer._format_ratios_as_table(ratios)
    print(formatted_output)
    
    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
