
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Local LLM Configuration
LOCAL_LLM_URL = "http://192.168.1.47:11434/api/generate"
MODEL_NAME = "phi4-mini-reasoning"

def call_local_llm(prompt):
    """
    Helper function to call local LLM (Ollama style).
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(LOCAL_LLM_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get("response")
    except Exception as e:
        print(f"Error calling local LLM: {e}")
        return None

def extract_financials(text_content):
    """
    Extracts balance sheet details using locally hosted Phi-4 model.
    """
    if not text_content:
        return None

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
          { "particular": "Share Capital", "note_no": 1, "current_year": 10000000, "previous_year": 10000000 },
          { "particular": "Reserves and Surplus", "note_no": 2, "current_year": 5000000, "previous_year": 4500000 }
        ],
        "non_current_liabilities": [
          { "particular": "Long-term Borrowings", "note_no": 3, "current_year": 2000000, "previous_year": 2500000 }
        ],
        "current_liabilities": [
          { "particular": "Trade Payables", "note_no": 4, "current_year": 1500000, "previous_year": 1000000 },
          { "particular": "Short-term Borrowings", "note_no": 5, "current_year": 500000, "previous_year": 600000 }
        ]
      },
      "assets": {
        "non_current_assets": [
          { "particular": "Property, Plant & Equipment", "note_no": 6, "current_year": 8000000, "previous_year": 8500000 }
        ],
        "current_assets": [
          { "particular": "Cash and Cash Equivalents", "note_no": 7, "current_year": 500000, "previous_year": 300000 },
          { "particular": "Trade Receivables", "note_no": 8, "current_year": 3000000, "previous_year": 2700000 },
          { "particular": "Inventory", "note_no": 9, "current_year": 2000000, "previous_year": 1800000 }
        ]
      }}
    }}
    
    Rules:
    1. Extract ALL line items from the balance sheet (at least 5-10 items per section).
    2. For EVERY item:
       - 'particular': Use the ACTUAL line item name from the document (NOT empty, NOT dates)
       - 'current_year': ONLY numeric amount (remove "Lakhs", "Crores", commas). Never include dates like "21-03-24"
       - 'previous_year': ONLY numeric amount if available
    3. If a numeric value is not found, use null (NOT dates, NOT text).
    4. Scale conversion: "1.5 Lakhs" → 150000, "2 Crores" → 20000000
    5. If balance sheet has multiple columns, map each correctly to current_year/previous_year.
    6. Return ONLY the raw JSON block (no markdown, no explanations).

    TEXT CONTENT:
    {text_content[:25000]}
    """

    print(f"🤖 Sending text to local LLM ({MODEL_NAME}) for extraction...")
    response_text = call_local_llm(prompt)

    if response_text:
        try:
            # Clean up response to get pure JSON
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = json_str[start:end]

            return json.loads(json_str)
        except Exception as e:
            print(f"Failed to parse local LLM response as JSON: {e}")
            return None
    
    return None

def redraft_json(json_data, context_text=None):
    """
    Refines and "redrafts" an existing JSON structure using local Phi-4.
    """
    if not json_data:
        return None

    prompt = f"""
    You are a senior financial data engineer. Your task is to "redraft" and refine the provided JSON data into a specific highly-structured format (demo.json style).
    
    The input JSON is a draft extraction from a financial report. Items may be missing, misplaced, or formatted incorrectly.
    
    Your goal:
    1. Cross-reference the draft JSON with any provided context text.
    2. Fill in null values if the data exists in the context.
    3. Ensure all numbers are absolute (no "Lakhs", "Crores", or commas).
    
    4. YOU MUST FOLLOW THIS EXACT JSON STRUCTURE:
    {{
      "company_details": {{
        "company_name": "...",
        "cin": "...",
        "balance_sheet_date": "DD-MM-YYYY",
        "current_financial_year": "...",
        "previous_financial_year": "...",
        "currency": "..."
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

    Return ONLY the refined JSON block.

    DRAFT JSON:
    {json.dumps(json_data, indent=2)}

    CONTEXT TEXT:
    {context_text[:15000] if context_text else "No context provided."}
    """

    print(f"🤖 Redrafting JSON with local LLM ({MODEL_NAME})...")
    response_text = call_local_llm(prompt)

    if response_text:
        try:
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = json_str[start:end]

            return json.loads(json_str)
        except Exception as e:
            print(f"Local LLM redraft failed: {e}")
            return None
    return None
