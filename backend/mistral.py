import fitz  # pip install pymupdf
# Attempt to import the Mistral client; allow missing import in dev simulation mode
try:
    from mistralai import Mistral
except Exception:
    Mistral = None
import json
import sys

# ---------------- CONFIG ----------------
import os
from dotenv import load_dotenv

load_dotenv()

# Support a dev-mode simulation when you don't have a Mistral API key.
SIMULATE_MISTRAL = os.getenv("MISTRAL_SIMULATE", "").lower() in ("1", "true", "yes")
API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    if SIMULATE_MISTRAL:
        print("Info: MISTRAL_API_KEY not set — running in simulated Mistral mode (MISTRAL_SIMULATE=1).")
    else:
        print(
            "Warning: MISTRAL_API_KEY env var not set. Mistral extraction disabled; set MISTRAL_API_KEY "
            "or set MISTRAL_SIMULATE=1 for dev-mode."
        )
DPI = 300
# ----------------------------------------

PROMPT = """
Extract the balance sheet and profit and loss statement for the latest and previous financial years.
The PDF typically contains multiple years (e.g., 2024 and 2023).
CRITICAL RULE: Extract data for BOTH the LATEST financial year AND the PREVIOUS financial year if available.

PDF Layout Warning:
In many Indian financial reports (like Dabur India Limited), the layout is:
Particulars | Note | 31 March 2024 (Latest) | 31 March 2023 (Previous)
You MUST skip the 'Note' column and pick the numbers from the relevant year columns.

Output the data in EXACTLY this JSON format (following demo.json style):
{
  "company_details": {
    "company_name": "...",
    "cin": "...",
    "balance_sheet_date": "DD-MM-YYYY",
    "current_financial_year": "2024-25",
    "previous_financial_year": "2023-24",
    "currency": "INR"
  },
  "equity_and_liabilities": {
    "shareholders_funds": [
      { "particular": "...", "note_no": X, "current_year": X, "previous_year": X }
    ],
    "non_current_liabilities": [
      { "particular": "...", "note_no": X, "current_year": X, "previous_year": X }
    ],
    "current_liabilities": [
      { "particular": "...", "note_no": X, "current_year": X, "previous_year": X }
    ]
  },
  "profit_and_loss": {
    "revenue": { "particular": "Revenue from Operations", "current_year": X, "previous_year": X },
    "net_profit": { "particular": "Profit for the Year", "current_year": X, "previous_year": X },
    "ebitda": { "particular": "EBITDA", "current_year": X, "previous_year": X },
    "interest_expense": { "particular": "Finance Costs", "current_year": X, "previous_year": X }
  },
  "assets": {
    "non_current_assets": [
      { "particular": "...", "note_no": X, "current_year": X, "previous_year": X }
    ],
    "current_assets": [
      { "particular": "...", "note_no": X, "current_year": X, "previous_year": X }
    ]
  }
}

Important:
- Use absolute numbers (e.g., if it says 1,509.21 crores, return 1509.21).
- If a value is missing or not found, return null.
- Do NOT infer numbers and do NOT use previous year data.
- Ensure all numbers are from the SAME column (the latest year).
"""

import io
import os
import base64
import requests
import markdown
from PIL import Image
from pdf2image import convert_from_path


def extract_tables_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_rows = []

    for page in doc:
        tables = page.find_tables()
        for table in tables:
            for row in table.extract():
                if len(row) >= 2:
                    item = row[0].strip() if row[0] else ""
                    # find the latest year value. 
                    # If multiple numeric columns, try to skip potential note column
                    values = []
                    for cell in row[1:]:
                        v = cell.strip() if cell else ""
                        if v:
                            values.append(v)
                    
                    value = ""
                    if len(values) >= 2:
                        # Left-hand column heuristic:
                        # Values list is [Note?, Value_Latest, Value_Prev]
                        # If values[0] is small (Note index), values[1] is the left-most financial column (Latest).
                        # Otherwise, values[0] is the left-most financial column (Latest).
                        try:
                            v0_num = float(values[0].replace(",", ""))
                            if v0_num < 200: # Likely a Note index
                                value = values[1]
                            else:
                                value = values[0]
                        except:
                            value = values[0]
                    elif values:
                        value = values[0]
                    
                    if item and value:
                        all_rows.append({"item": item, "value": value})

    return all_rows


import re
import json


# ---------------- OLLAMA-BASED OCR HELPERS (from pratipc) ----------------
# These helpers let us ask an Ollama-style model (glm-ocr) to extract text and tables

UPLOAD = "uploads"
os.makedirs(UPLOAD, exist_ok=True)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.1.42:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "glm-ocr:latest")

DPI = 90          # lower DPI to avoid potential GGML crashes
MAX_WIDTH = 1600  # resize large pages for GPU safety


def resize_image_safe(path):
    img = Image.open(path)

    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size)

    img.save(path)


def ask_ollama(prompt, img_b64):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=180)
        data = r.json()

        if "response" in data:
            return data["response"]

        if "error" in data:
            return f"[Ollama Error] {data['error']}"

        return str(data)
    except Exception as e:
        return f"[Request Failed] {str(e)}"


def run_ocr(image_path, skip_tables=False):
    resize_image_safe(image_path)

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    text = ask_ollama("Text Recognition:", img_b64)

    tables_html = ""
    if not skip_tables:
        try:
            tables_md = ask_ollama("Table Recognition:", img_b64)
            tables_html = markdown.markdown(tables_md, extensions=["tables"])
        except Exception:
            tables_html = "<p><i>Table extraction skipped (too large or failed)</i></p>"

    return text, tables_html


def process_pdf(pdf_path):
    pages = convert_from_path(pdf_path, dpi=DPI)

    all_text = []
    all_tables = []

    for i, page in enumerate(pages):
        print(f"Processing page {i+1}/{len(pages)}")

        img_path = os.path.join(UPLOAD, f"page_{i}.png")
        page.save(img_path)

        text, tables = run_ocr(img_path)

        all_text.append(f"\n\n===== PAGE {i+1} =====\n{text}")
        all_tables.append(f"<h3>Page {i+1}</h3>{tables}")

    return "\n".join(all_text), "\n".join(all_tables)


def ocr_pdf(pdf_path, client=None):
    """Run OCR on the PDF using the Ollama-based OCR model.

    Keeps the same signature as before (`ocr_pdf(pdf_path, client)`) but prefers
    Ollama. Returns the combined plain text for downstream extraction.
    """
    try:
        text, _ = process_pdf(pdf_path)
        return text
    except Exception as e:
        print(f"Ollama OCR failed, falling back to PyMuPDF text extract: {e}")
        # Fallback to previous simple text extraction
        doc = fitz.open(pdf_path)
        txt = ""
        for page in doc:
            txt += page.get_text("text") + "\n"
        doc.close()
        return txt


def extract_financials(ocr_text: str, client=None):
    """
    Converts OCR text into structured balance sheet rows using LLM.
    This wrapper exists to keep app.py imports stable.
    """

    if not ocr_text or not isinstance(ocr_text, str):
        return None

    try:
        # If you already have a parser, reuse it
        if "parse_balance_sheet_from_text" in globals():
            return parse_balance_sheet_from_text(ocr_text)

        # Fallback minimal LLM prompt
        if client:
            resp = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
Extract the Balance Sheet as structured JSON.
Return ONLY JSON.

TEXT:
{ocr_text}
""",
                    }
                ],
            )
            return json.loads(resp.choices[0].message.content)

    except Exception as e:
        print(f"extract_financials failed: {e}")
        return None


def _parse_number_token(s: str):
    if not s:
        return None
    s = s.strip().lower()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    # Handle lakhs/crore
    m = re.search(r"([0-9,\.]+)\s*(lakhs?|lakh|crore|crores|cr)?", s, flags=re.IGNORECASE)
    if not m:
        # fallback: strip non-numeric chars
        cleaned = re.sub(r"[^0-9\.\-]", "", s)
        try:
            v = float(cleaned) if cleaned else None
            return -v if neg and v is not None else v
        except Exception:
            return None
    num = float(m.group(1).replace(",", ""))
    mult = (m.group(2) or "").lower()
    if "lakh" in mult:
        num = num * 1e5
    elif "crore" in mult or mult == "cr":
        num = num * 1e7
    return -num if neg else num


def simulate_extract_balance_sheet(ocr_text: str):
    """Lightweight heuristic extractor used only in dev-mode simulation.
    It looks for common labels and numeric tokens and returns the structure
    expected by the app. This is intentionally conservative and non-ML.
    """
    out = {
        "company_details": {
            "company_name": None,
            "cin": None,
            "balance_sheet_date": None,
            "current_financial_year": None,
            "previous_financial_year": None,
            "currency": "INR",
        },
        "equity_and_liabilities": {
            "shareholders_funds": [],
            "non_current_liabilities": [],
            "current_liabilities": [],
        },
        "assets": {
            "non_current_assets": [],
            "current_assets": [],
        },
        "p_and_l": {
            "revenue": {"current": None, "previous": None},
            "net_profit": {"current": None, "previous": None},
            "ebitda": {"current": None, "previous": None},
            "interest_expense": {"current": None, "previous": None},
        },
    }

    # Find year (first 4-digit year)
    y = re.search(r"(20\d{2})", ocr_text)
    if y:
        out["year"] = y.group(1)

    # keywords -> target paths in out
    mapping = {
        r"total assets": ("assets", "total_assets"),
        r"current assets": ("assets", "current_assets"),
        r"total current assets": ("assets", "current_assets"),
        r"total liabilities": ("liabilities", "total_liabilities"),
        r"current liabilities": ("liabilities", "current_liabilities"),
        r"total current liabilities": ("liabilities", "current_liabilities"),
        r"total equity": ("equity", "total_equity"),
        r"cash and cash equivalents|cash and equivalents|cash": ("assets", "cash_and_equivalents"),
        r"inventor(y|ies)": ("assets", "inventories"),
        r"accounts receivable|trade receivables|receivable": ("assets", "trade_receivables"),
        r"property, plant|property & plant|property plant and equipment|ppe|fixed assets": (
            "assets",
            "property_plant_equipment",
        ),
        r"accounts payable|trade payables|payables": ("liabilities", "trade_payables"),
        r"short[- ]term borrowings|short term borrowings|short-term debt": ("liabilities", "short_term_borrowings"),
        r"long[- ]term borrowings|long term debt|long-term debt": ("liabilities", "long_term_borrowings"),
        r"revenue|turnover|sales": ("p_and_l", "revenue"),
        r"net income|net profit|profit for the year": ("p_and_l", "net_profit"),
        r"ebitda": ("p_and_l", "ebitda"),
        r"interest expense|finance costs": ("p_and_l", "interest_expense"),
    }

    # naive search: for each regex, find the first numeric token on the same line
    for line in ocr_text.splitlines():
        ln = line.strip()
        if not ln:
            continue
        low = ln.lower()
        for regex, path in mapping.items():
            if re.search(regex, low):
                # find a numeric-looking token in the line
                # Split the line into potential tokens, assuming item is first, then values
                # This is a heuristic and might need refinement for complex layouts
                tokens = re.findall(r"\(?[0-9,]+(?:\.[0-9]+)?\)?(?:\s*(?:lakhs?|lakh|crore|crores|cr))?|[a-zA-Z\s&,-]+", ln, flags=re.IGNORECASE)
                
                nums = []
                # Start from the second token, assuming the first is the item description
                # or if the first token is not a number, then subsequent tokens are values
                start_idx = 0
                if tokens and not re.match(r"\(?[0-9,]+(?:\.[0-9]+)?\)?", tokens[0]):
                    start_idx = 1

                for t in tokens[start_idx:]:
                    val = _parse_number_token(t)
                    if val is not None:
                        nums.append(val)
                
                v = None
                if len(nums) >= 2:
                    # Robust left-hand column selection:
                    # In Dabur/Indian layouts: [Note] | Latest | Previous
                    if len(nums) >= 3:
                        # Skip Note (index 0), take left-most financial column (index 1)
                        v = nums[1]
                    else:
                        # No Note column? Take left-most financial column (index 0)
                        v = nums[0]
                elif nums:
                    v = nums[0]
                
                if v is not None:
                    section, key = path
                    out.setdefault(section, {})[key] = v

    # Attempt to fill totals if missing by summing parts (but do NOT invent numbers if nothing found)
    # (Keep conservative: only sum if parts exist)
    try:
        a = out.get("assets", {})
        if a.get("total_assets") is None:
            parts = [a.get("current_assets"), a.get("property_plant_equipment")]
            if any(p is not None for p in parts):
                out["assets"]["total_assets"] = sum(p for p in parts if p is not None)
    except Exception:
        pass

    return out


def extract_balance_sheet(ocr_text, client):
    # If running in simulated dev-mode, use heuristics instead of a remote LLM
    if SIMULATE_MISTRAL or not client:
        return simulate_extract_balance_sheet(ocr_text)

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": ocr_text[:25000]},  # increased for better coverage of multiple pages
        ],
    )

    raw = response.choices[0].message.content.strip()

    if not raw:
        raise ValueError("LLM returned empty response")

    # ✅ Extract first JSON block safely
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        print("⚠️ Raw LLM output:\n", raw)
        raise ValueError("No JSON found in LLM response")

    return json.loads(match.group())


def calculate_financial_ratios(data):
    """
    Calculates financial ratios from the new structured JSON format (demo.json style).
    Handles 'equity_and_liabilities' and 'assets' sections where each sub-category
    is a list of objects with 'current_year' and 'previous_year' fields.
    """
    def sum_year(items, year_key):
        total = 0.0
        if not items or not isinstance(items, list):
            return 0.0
        for item in items:
            val = item.get(year_key)
            if isinstance(val, (int, float)):
                total += float(val)
        return total

    def find_particular(items, keywords, year_key):
        if not items or not isinstance(items, list):
            return None
        for item in items:
            p = str(item.get("particular", "")).lower()
            if any(k in p for k in keywords):
                return item.get(year_key)
        return None

    # Determine which years to process
    years = ["current_year", "previous_year"]
    results = {}

    for year in years:
        # 1. Extract and sum values for this year
        el = data.get("equity_and_liabilities", {})
        sh_funds = el.get("shareholders_funds", [])
        nc_liab = el.get("non_current_liabilities", [])
        c_liab = el.get("current_liabilities", [])

        assets_sec = data.get("assets", {})
        nc_assets = assets_sec.get("non_current_assets", [])
        c_assets = assets_sec.get("current_assets", [])

        # Sum totals
        equity = sum_year(sh_funds, year)
        long_term_debt = sum_year(nc_liab, year)
        current_liabilities = sum_year(c_liab, year)
        fixed_assets = sum_year(nc_assets, year)
        current_assets = sum_year(c_assets, year)

        total_assets = fixed_assets + current_assets
        total_liabilities = long_term_debt + current_liabilities

        # Find specific items for ratios
        inventory = find_particular(c_assets, ["inventory", "stock"], year) or 0.0
        receivables = find_particular(c_assets, ["receivable", "debtor"], year) or 0.0
        cash = find_particular(c_assets, ["cash", "bank"], year) or 0.0
        payables = find_particular(c_liab, ["payable", "creditor"], year) or 0.0

        # P&L metrics (if found in the balance sheet - rare, or if provided)
        # Since p_and_l was removed from prompts, we can't easily get these now
        # unless they are provided in the data.
        p_and_l = data.get("p_and_l", {})
        revenue = p_and_l.get(year.replace("_year", "")) if isinstance(p_and_l.get("revenue"), dict) else None
        # Fallback to old keys/structure if any
        if revenue is None: revenue = p_and_l.get("revenue") 
        net_profit = p_and_l.get("net_profit")
        ebitda = p_and_l.get("ebitda")
        interest = p_and_l.get("interest_expense")

        def safe_div(a, b):
            if a is None or b in (None, 0):
                return None
            return round(a / b, 4)

        year_ratios = {
            "current_ratio": safe_div(current_assets, current_liabilities),
            "quick_ratio": safe_div(current_assets - inventory, current_liabilities),
            "cash_ratio": safe_div(cash, current_liabilities),
            "debt_to_equity": safe_div(total_liabilities, equity),
            "debt_to_assets": safe_div(total_liabilities, total_assets),
            "equity_ratio": safe_div(equity, total_assets),
            "roe": safe_div(net_profit, equity),
            "roce": safe_div(ebitda, equity + long_term_debt),
            "net_profit_margin": safe_div(net_profit, revenue),
            "inventory_turnover": safe_div(revenue, inventory),
            "receivables_turnover": safe_div(revenue, receivables),
            "interest_coverage": safe_div(ebitda, interest)
        }
        
        # Filter None and round
        clean_ratios = {k: round(v, 2) if isinstance(v, float) else v for k, v in year_ratios.items() if v is not None}
        results[year] = clean_ratios

    # For backward compatibility, return only current year ratios at top level
    return results.get("current_year", {})


def main():
    if len(sys.argv) != 2:
        print("Usage: python mistral_balance_sheet.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    client = Mistral(api_key=API_KEY)

    print("🔍 Running Mistral OCR...")
    text = ocr_pdf(pdf_path, client)

    print("📊 Extracting latest balance sheet...")
    balance_sheet = extract_balance_sheet(text, client)

    print("\n✅ BALANCE SHEET (LATEST YEAR):\n")
    print(json.dumps(balance_sheet, indent=2))


if __name__ == "__main__":
    main()
