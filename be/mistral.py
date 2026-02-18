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
Extract the balance sheet and profit & loss for the latest financial year only.
The PDF typically contains multiple years (e.g., 2024 and 2023).
CRITICAL RULE: Always use the LEFT-HAND column for the latest year numbers. Ignore all other columns for previous years.

PDF Layout Warning:
In many Indian financial reports (like Dabur India Limited), the layout is:
Particulars | Note | 31 March 2024 (Latest) | 31 March 2023 (Previous)
You MUST skip the 'Note' column and pick the numbers from the '31 March 2024' column.

Output the data in EXACTLY this JSON format:
{
  "year": "2024",
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


def run_ocr(image_path):
    resize_image_safe(image_path)

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    text = ask_ollama("Text Recognition:", img_b64)

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
        "year": None,
        "assets": {
            "total_assets": None,
            "current_assets": None,
            "cash_and_equivalents": None,
            "inventories": None,
            "trade_receivables": None,
            "property_plant_equipment": None,
        },
        "liabilities": {
            "total_liabilities": None,
            "current_liabilities": None,
            "trade_payables": None,
            "short_term_borrowings": None,
            "long_term_borrowings": None,
        },
        "equity": {"total_equity": None},
        "p_and_l": {"turnover": None, "net_profit": None, "ebitda": None, "interest_expense": None},
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
    ratios = {}

    A = data.get("assets", {})
    L = data.get("liabilities", {})
    E = data.get("equity", {})

    def safe_div(a, b):
        if a is None or b in (None, 0):
            return None
        return round(a / b, 4)

    ratios["current_ratio"] = safe_div(
        A.get("current_assets"), L.get("current_liabilities")
    )
    ratios["quick_ratio"] = safe_div(
        (A.get("cash_and_equivalents") or 0) + (A.get("trade_receivables") or 0),
        L.get("current_liabilities"),
    )
    ratios["debt_to_equity"] = safe_div(
        L.get("total_liabilities"), E.get("total_equity")
    )
    ratios["debt_to_assets"] = safe_div(
        L.get("total_liabilities"), A.get("total_assets")
    )
    ratios["equity_ratio"] = safe_div(E.get("total_equity"), A.get("total_assets"))
    ratios["roe"] = safe_div(
        data.get("p_and_l", {}).get("net_profit"), E.get("total_equity")
    )

    capital_employed = (E.get("total_equity") or 0) + (L.get("total_liabilities") or 0)
    ratios["roce"] = safe_div(data.get("p_and_l", {}).get("ebitda"), capital_employed)

    p_and_l = data.get("p_and_l", {})
    ratios["net_profit_margin"] = safe_div(
        p_and_l.get("net_profit"), p_and_l.get("revenue")
    )
    ratios["inventory_turnover"] = safe_div(
        p_and_l.get("revenue"), A.get("inventories")
    )
    ratios["trade_receivables_turnover"] = safe_div(
        p_and_l.get("revenue"), A.get("trade_receivables")
    )
    ratios["trade_payables_turnover"] = safe_div(
        p_and_l.get("revenue"), L.get("trade_payables")
    )
    ratios["debt_service_coverage"] = safe_div(
        p_and_l.get("ebitda"), p_and_l.get("interest_expense")
    )
    ratios["roi"] = safe_div(p_and_l.get("net_profit"), capital_employed)

    net_capital = safe_div(
        (A.get("total_assets") or 0) - (L.get("total_liabilities") or 0), 1
    )
    ratios["net_capital_turnover"] = safe_div(p_and_l.get("revenue"), net_capital)

    for k, v in ratios.items():
        if isinstance(v, float):
            ratios[k] = round(v, 2)

    return ratios


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
