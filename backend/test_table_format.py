#!/usr/bin/env python3
"""
Quick test to demonstrate the table formatting for financial ratios.
Shows the before (JSON) and after (table) format.
"""

import json

# Sample ratio data
sample_ratios = {
    'current_ratio': 2.5,
    'quick_ratio': 1.8,
    'cash_ratio': 0.6,
    'gross_profit': 500000.0,
    'gross_margin': 0.4,
    'operating_profit': 250000.0,
    'operating_margin': 0.20,
    'net_margin': 0.15,
    'roa': 0.12,
    'roe': 0.25,
    'debt_ratio': 0.4,
    'debt_to_equity': 0.67,
    'equity_ratio': 0.6,
    'interest_coverage': 5.5,
    'asset_turnover': 0.8,
    'inventory_turnover': 4.5,
    'receivables_turnover': 6.2,
    'payables_turnover': 3.8,
    '_extracted_numbers': {
        'current_assets': 1000000.0,
        'current_liabilities': 400000.0,
        'total_assets': 2000000.0,
        'total_equity': 1200000.0,
        'revenue': 1250000.0,
        'net_income': 187500.0,
    }
}

print("\n" + "=" * 80)
print("BEFORE: JSON Format (Old)".center(80))
print("=" * 80)
print(json.dumps({"ratios": sample_ratios}, indent=2))

print("\n\n" + "=" * 80)
print("AFTER: Table Format (New)".center(80))
print("=" * 80)

# Reproduce the _format_ratios_as_table logic here for demo
def format_ratios_as_table(ratios):
    categories = {
        "Liquidity Ratios": [
            ("Current Ratio", "current_ratio"),
            ("Quick Ratio", "quick_ratio"),
            ("Cash Ratio", "cash_ratio"),
        ],
        "Profitability Ratios": [
            ("Gross Profit", "gross_profit"),
            ("Gross Margin (%)", "gross_margin"),
            ("Operating Profit", "operating_profit"),
            ("Operating Margin (%)", "operating_margin"),
            ("Net Margin (%)", "net_margin"),
            ("Return on Assets (ROA) (%)", "roa"),
            ("Return on Equity (ROE) (%)", "roe"),
        ],
        "Leverage / Solvency Ratios": [
            ("Debt Ratio", "debt_ratio"),
            ("Debt to Equity Ratio", "debt_to_equity"),
            ("Equity Ratio", "equity_ratio"),
            ("Interest Coverage Ratio", "interest_coverage"),
        ],
        "Efficiency Ratios": [
            ("Asset Turnover", "asset_turnover"),
            ("Inventory Turnover", "inventory_turnover"),
            ("Receivables Turnover", "receivables_turnover"),
            ("Payables Turnover", "payables_turnover"),
        ],
    }

    lines = []
    lines.append("=" * 80)
    lines.append("FINANCIAL RATIOS ANALYSIS".center(80))
    lines.append("=" * 80)
    lines.append("")

    for category, ratio_list in categories.items():
        lines.append(f"\n{category}:")
        lines.append("-" * 80)
        lines.append(f"{'Metric':<40} {'Value':<30} {'Status':<10}")
        lines.append("-" * 80)

        for label, key in ratio_list:
            value = ratios.get(key)
            
            if value is None:
                value_str = "N/A"
                status = "—"
            else:
                if key in ["gross_margin", "operating_margin", "net_margin", "roa", "roe"]:
                    value_str = f"{value * 100:.2f}%"
                else:
                    value_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                
                if key == "current_ratio":
                    status = "✓ Good" if 1.5 <= value <= 3.0 else ("⚠ Warning" if value < 1.0 else "→ Review")
                elif key == "quick_ratio":
                    status = "✓ Good" if value >= 1.0 else "⚠ Warning"
                elif key == "debt_to_equity":
                    status = "✓ Good" if value <= 1.5 else "⚠ High"
                elif key == "roe":
                    status = "✓ Good" if value >= 0.15 else "→ Monitor"
                elif key == "roa":
                    status = "✓ Good" if value >= 0.05 else "→ Monitor"
                else:
                    status = "—"

            lines.append(f"{label:<40} {value_str:<30} {status:<10}")

        lines.append("")

    extracted = ratios.get("_extracted_numbers", {})
    if extracted and any(v is not None for v in extracted.values()):
        lines.append("\n" + "=" * 80)
        lines.append("BASE FINANCIAL DATA (Extracted from Document)".center(80))
        lines.append("=" * 80)
        lines.append(f"{'Item':<40} {'Amount':<40}")
        lines.append("-" * 80)

        for key, value in extracted.items():
            if value is not None and key != "_extracted_numbers":
                display_key = key.replace("_", " ").title()
                if isinstance(value, (int, float)):
                    value_str = f"{value:,.2f}"
                else:
                    value_str = str(value)
                lines.append(f"{display_key:<40} {value_str:<40}")

    lines.append("=" * 80)
    lines.append("")

    return "\n".join(lines)

print(format_ratios_as_table(sample_ratios))

print("✓ Table format test completed successfully!")
print("\nKey improvements:")
print("  • Organized by ratio category (Liquidity, Profitability, Leverage, Efficiency)")
print("  • Readable column alignment with Metric, Value, and Status")
print("  • Status indicators (✓ Good, ⚠ Warning, → Monitor) for quick interpretation")
print("  • Percentage values automatically formatted with % symbol")
print("  • Base financial data included as reference")
