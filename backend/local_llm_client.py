
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
