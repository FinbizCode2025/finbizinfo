import re
from typing import Optional, Dict


def _find_amount(text: str, keywords: list[str]) -> Optional[float]:
    norm_text = text.replace('\u00A0', ' ')
    for kw in keywords:
        pattern = rf"{re.escape(kw)}[^\n\r\d\-\(\)]*([\(\-]?[\$₹Rs\.\s]*[\d,]+(?:\.\d+)?[\)]?)"
        m = re.search(pattern, norm_text, flags=re.IGNORECASE)
        if m:
            raw = m.group(1)
            cleaned = re.sub(r"[\$₹Rs\.\s]", '', raw)
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            cleaned = cleaned.replace(',', '')
            try:
                return float(cleaned)
            except Exception:
                continue

    lines = norm_text.splitlines()
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw.lower() in line.lower():
                m = re.search(r"([\(\-]?[\$₹Rs\.\s]*[\d,]+(?:\.\d+)?[\)]?)", line)
                if m:
                    raw = m.group(1)
                    cleaned = re.sub(r"[\$₹Rs\.\s]", '', raw)
                    if cleaned.startswith('(') and cleaned.endswith(')'):
                        cleaned = '-' + cleaned[1:-1]
                    try:
                        return float(cleaned.replace(',', ''))
                    except Exception:
                        pass
                if i + 1 < len(lines):
                    m2 = re.search(r"([\(\-]?[\$₹Rs\.\s]*[\d,]+(?:\.\d+)?[\)]?)", lines[i+1])
                    if m2:
                        raw2 = m2.group(1)
                        cleaned2 = re.sub(r"[\$₹Rs\.\s]", '', raw2)
                        if cleaned2.startswith('(') and cleaned2.endswith(')'):
                            cleaned2 = '-' + cleaned2[1:-1]
                        try:
                            return float(cleaned2.replace(',', ''))
                        except Exception:
                            pass
    return None


def _extract_financial_numbers(text: str) -> Dict[str, Optional[float]]:
    t = text
    values: Dict[str, Optional[float]] = {}

    values['current_assets'] = _find_amount(t, [
        'total current assets', 'current assets', 'total current assets and loans', 'currents assets'
    ])

    values['inventory'] = _find_amount(t, [
        'inventory', 'stock', 'inventories'
    ])

    values['cash_and_cash_equivalents'] = _find_amount(t, [
        'cash and cash equivalents', 'cash & cash equivalents', 'cash and bank balances', 'cash in hand'
    ])

    values['current_liabilities'] = _find_amount(t, [
        'total current liabilities', 'current liabilities', 'liabilities- current', 'current portion of'
    ])

    values['total_assets'] = _find_amount(t, [
        'total assets', 'assets total', 'total non-current and current assets'
    ])

    values['total_equity'] = _find_amount(t, [
        'total equity', 'shareholders funds', "total equity and liabilities", 'equity and liabilities', 'total shareholders\' funds'
    ])

    values['total_liabilities'] = _find_amount(t, [
        'total liabilities', 'liabilities total'
    ])

    values['revenue'] = _find_amount(t, [
        'total revenue', 'revenue', 'net sales', 'sales', 'turnover'
    ])

    values['cogs'] = _find_amount(t, [
        'cost of goods sold', 'cost of sales', 'cost of materials', 'direct expenses', 'cost of revenue'
    ])

    values['gross_profit'] = _find_amount(t, [
        'gross profit', 'gross margin'
    ])

    values['operating_income'] = _find_amount(t, [
        'operating profit', 'operating income', 'profit from operations'
    ])

    values['ebit'] = _find_amount(t, [
        'profit before finance costs and tax', 'ebit', 'earnings before interest and tax', 'profit before interest and tax'
    ])

    values['interest_expense'] = _find_amount(t, [
        'finance costs', 'interest expense', 'interest paid'
    ])

    values['net_income'] = _find_amount(t, [
        'profit for the year', 'net profit', 'profit after tax', 'net income'
    ])

    values['receivables'] = _find_amount(t, [
        'trade receivables', 'receivables', 'accounts receivable', 'debtors'
    ])

    values['payables'] = _find_amount(t, [
        'trade payables', 'payables', 'accounts payable', 'creditors'
    ])

    return values


def calculate_financial_ratios_from_text(text: str) -> Dict[str, Optional[float]]:
    nums = _extract_financial_numbers(text)

    def safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
        try:
            if a is None or b is None:
                return None
            if b == 0:
                return None
            return a / b
        except Exception:
            return None

    ratios: Dict[str, Optional[float]] = {}

    # Liquidity
    ratios['current_ratio'] = safe_div(nums.get('current_assets'), nums.get('current_liabilities'))
    quick_assets = None
    if nums.get('current_assets') is not None and nums.get('inventory') is not None:
        quick_assets = nums['current_assets'] - nums['inventory']
    ratios['quick_ratio'] = safe_div(quick_assets, nums.get('current_liabilities'))
    ratios['cash_ratio'] = safe_div(nums.get('cash_and_cash_equivalents'), nums.get('current_liabilities'))

    # Profitability
    if nums.get('gross_profit') is not None:
        ratios['gross_profit'] = nums.get('gross_profit')
    elif nums.get('revenue') is not None and nums.get('cogs') is not None:
        ratios['gross_profit'] = nums['revenue'] - nums['cogs']
    else:
        ratios['gross_profit'] = None

    if nums.get('operating_income') is not None:
        ratios['operating_profit'] = nums.get('operating_income')
    else:
        ratios['operating_profit'] = None

    ratios['gross_margin'] = None
    if nums.get('revenue') is not None and nums.get('revenue') != 0:
        if ratios.get('gross_profit') is not None:
            ratios['gross_margin'] = ratios['gross_profit'] / nums['revenue']

    ratios['operating_margin'] = safe_div(ratios.get('operating_profit'), nums.get('revenue'))
    ratios['net_margin'] = safe_div(nums.get('net_income'), nums.get('revenue'))

    # Returns
    ratios['roa'] = safe_div(nums.get('net_income'), nums.get('total_assets'))
    ratios['roe'] = safe_div(nums.get('net_income'), nums.get('total_equity'))

    # Leverage
    ratios['debt_ratio'] = safe_div(nums.get('total_liabilities'), nums.get('total_assets'))
    ratios['debt_to_equity'] = safe_div(nums.get('total_liabilities'), nums.get('total_equity'))
    ratios['interest_coverage'] = safe_div(nums.get('ebit') or nums.get('operating_income'), nums.get('interest_expense'))

    # Efficiency
    ratios['asset_turnover'] = safe_div(nums.get('revenue'), nums.get('total_assets'))
    ratios['inventory_turnover'] = safe_div(nums.get('cogs'), nums.get('inventory'))
    ratios['receivables_turnover'] = safe_div(nums.get('revenue'), nums.get('receivables'))
    ratios['payables_turnover'] = safe_div(nums.get('cogs'), nums.get('payables'))

    # Round ratios to sensible precision where present
    for k, v in list(ratios.items()):
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)) and '_profit' in k or k in ['gross_profit', 'operating_profit']:
                ratios[k] = v
            else:
                ratios[k] = round(v, 4)
        except Exception:
            ratios[k] = v

    ratios['_extracted_numbers'] = nums
    return ratios


if __name__ == '__main__':
    sample_text = '''
Total current assets 1,000,000
Inventory 200,000
Cash and cash equivalents: (50,000)
Total current liabilities 400,000
Total assets 2,000,000
Total equity 800,000
Total liabilities 1,200,000
Revenue 1,500,000
Cost of goods sold 900,000
Operating profit 200,000
Interest expense 50,000
Net profit 120,000
Trade receivables 100,000
Trade payables 80,000
'''
    print(calculate_financial_ratios_from_text(sample_text))
