import requests
import json

url = "http://192.168.1.47:11434/api/generate"

financial_json = {
    "Current_Assets": 3491.82,
    "Current_Liabilities": 3001.32
}

prompt = f"""
You are an expert financial analyst. Your task is to extract the Balance Sheet from the provided text into a highly structured JSON format (following demo.json style).

The text may contain data for multiple years. ALWAYS extract data for BOTH the LATEST financial year AND the PREVIOUS financial year if available.

Output the data in EXACTLY this JSON format:
{{
  "company_details": {{
    "company_name": "...",
    "cin": "...",
    "balance_sheet_date": "DD-MM-YYYY",
    "current_financial_year": "2024-25",
    "previous_financial_year": "2023-24",
    "currency": "INR"
  }},
  "equity_and_liabilities": {{
    "shareholders_funds": [
      {{ "particular": "...", "note_no": X, "current_year": X, "previous_year": X }}
    ],
    "non_current_liabilities": [
      {{ "particular": "...", "note_no": X, "current_year": X, "previous_year": X }}
    ],
    "current_liabilities": [
      {{ "particular": "...", "note_no": X, "current_year": X, "previous_year": X }}
    ]
  }},
  "assets": {{
    "non_current_assets": [
      {{ "particular": "...", "note_no": X, "current_year": X, "previous_year": X }}
    ],
    "current_assets": [
      {{ "particular": "...", "note_no": X, "current_year": X, "previous_year": X }}
    ]
  }}
}}

Rules:
1. Extract all line items from the balance sheet.
2. Use absolute numbers. Remove commas, currency symbols, and handle scale (Lakhs/Crores).
3. If a value is not found, use null.
4. Ensure 'particular' names are descriptive and match the document.
5. Return ONLY the raw JSON block.

TEXT CONTENT:
[PROVIDE TEXT HERE]
"""

payload = {
    "model": "phi4-mini-reasoning",
    "prompt": prompt,
    "stream": False
}

response = requests.post(url, json=payload)
print(response.json()["response"])