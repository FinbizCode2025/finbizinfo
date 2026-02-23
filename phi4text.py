import requests
import json

url = "http://192.168.1.47:11434/api/generate"

financial_json = {
    "Current_Assets": 3491.82,
    "Current_Liabilities": 3001.32
}

prompt = f"""
Calculate Current Ratio.
Data:
{json.dumps(financial_json)}

Return only number.
"""

payload = {
    "model": "phi4-mini-reasoning",
    "prompt": prompt,
    "stream": False
}

response = requests.post(url, json=payload)
print(response.json()["response"])