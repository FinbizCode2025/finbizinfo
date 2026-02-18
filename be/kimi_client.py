
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Moonshot (Kimi) Configuration
MOONSHOT_API_KEY = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
BASE_URL = "https://api.moonshot.cn/v1"

class KimiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or MOONSHOT_API_KEY
        if not self.api_key:
            # Fallback or error - for now we might let it fail if used
            pass
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=BASE_URL,
        )

    def chat_complete(self, messages, model="moonshot-v1-32k", temperature=0.3):
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error calling Kimi API: {e}")
            return None

def extract_financials_with_kimi(text_content):
    """
    Extracts balance sheet details using Kimi LLM.
    Expects text content of the balance sheet page(s).
    Returns a JSON object.
    """
    if not text_content:
        return None

    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("KIMI_API_KEY not found. Skipping Kimi extraction.")
        return None

    client = KimiClient(api_key)

    system_prompt = """
    You are an expert financial analyst. Your task is to extract the Balance Sheet and Profit & Loss statement from the provided text.
    
    The text may contain data for multiple years. ALWAYS ignore previous years and extract data ONLY for the LATEST financial year.
    
    Output the data in EXACTLY this JSON format:
    {
      "year": "YYYY",
      "assets": {
        "total_assets": null,
        "current_assets": null,
        "cash_and_equivalents": null,
        "inventories": null,
        "trade_receivables": null,
        "property_plant_equipment": null
      },
      "liabilities": {
        "total_liabilities": null,
        "current_liabilities": null,
        "trade_payables": null,
        "short_term_borrowings": null,
        "long_term_borrowings": null
      },
      "equity": {
        "total_equity": null
      },
      "p_and_l": {
        "revenue": null,
        "net_profit": null,
        "ebitda": null,
        "interest_expense": null
      }
    }
    
    Rules:
    1. Extract the latest year's data.
    2. Use absolute numbers (e.g. 100.50). Remove commas and currency symbols.
    3. If a value is not found, return null.
    4. Do not halluncinate numbers.
    """

    user_message = f"Here is the text from the financial report:\n\n{text_content}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    print("🤖 Sending text to Kimi LLM for extraction...")
    response_text = client.chat_complete(messages)

    if response_text:
        try:
            # Clean up response to get pure JSON
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            print(f"Failed to parse Kimi response as JSON: {e}")
            print(f"Raw Response: {response_text}")
            return None
    
    return None
