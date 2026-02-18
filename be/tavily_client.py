import os
import requests
import json

TAVILY_API_URL = os.getenv('TAVILY_API_URL')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')


def search_company(query: str, top_k: int = 5):
    """Search the web (Tavily) for company info, focusing on negative feedback, fraud, and crimes.

    This is a thin adapter — set `TAVILY_API_KEY` and `TAVILY_API_URL` in env.
    The actual Tavily API may differ; update headers/params accordingly.
    """
    if not query:
        return {"error": "Empty query"}

    # Modify query to focus on detecting negative aspects
    negative_query = f"{query} negative feedback fraud crime scandals lawsuits investigations regulatory actions"

    headers = {"Content-Type": "application/json"}
    if TAVILY_API_KEY:
        headers["Authorization"] = f"Bearer {TAVILY_API_KEY}"

    payload = {
        "query": negative_query,
        "top_k": top_k
    }

    try:
        resp = requests.post(TAVILY_API_URL, headers=headers, json=payload, timeout=30)
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "text": resp.text}
    except Exception as e:
        return {"error": str(e)}
