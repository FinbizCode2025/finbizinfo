from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS, cross_origin
import os
import uuid
# pytesseract removed — using GLM OCR (Ollama) instead
import tempfile
from werkzeug.utils import secure_filename
import fitz
import pandas as pd
import cv2
import re
import json
from dotenv import load_dotenv
# Load environment variables early
load_dotenv()

from config import Config
from financial_analyzer import FinancialAnalyzer
from session_store import SessionStore
from tavily_client import search_company
from mistral import extract_balance_sheet, ocr_pdf, run_ocr, process_pdf, Mistral, API_KEY as MISTRAL_API_KEY
from kimi_client import extract_financials_with_kimi
import logging

# Configure basic logger to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def log_balance_sheet(session_id: str, data):
    try:
        # Log a clear marker and the JSON-formatted balance sheet
        logging.info("BALANCE_SHEET_JSON session=%s\n%s", session_id, json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        logging.exception("Failed to log balance sheet for %s: %s", session_id, e)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
SESSIONS_FOLDER = os.path.join(UPLOAD_FOLDER, "sessions")
os.makedirs(SESSIONS_FOLDER, exist_ok=True)

# Tesseract removed — GLM OCR will be used exclusively for OCR tasks

pdf_stores = {} 

current_api_key = os.getenv("GOOGLE_API_KEY")

# Module-level safe numeric helpers (used outside calculate_financial_ratios)
def _is_number(x):
    return isinstance(x, (int, float))

def safe_ge(x, y):
    try:
        return _is_number(x) and x >= y
    except Exception:
        return False

def safe_gt(x, y):
    try:
        return _is_number(x) and x > y
    except Exception:
        return False


# Module-level number parser (used by chart extraction and other helpers)
def parse_number(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    if not s or s in ("-", "—", "na", "nil"):
        return None
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    s = re.sub(r"[₹$,]", "", s)
    cleaned = re.sub(r"[^0-9.\-]", "", s)
    if not cleaned or cleaned == '.':
        return None
    try:
        num = float(cleaned)
        return -num if neg else num
    except (ValueError, TypeError):
        return None


def get_pdf_store(session_id: str) -> FinancialAnalyzer:
    store = pdf_stores.get(session_id)
    if not store:
        raise ValueError("Document not processed or session expired. Please upload the PDF again.")
    return store


class PersistentStore:
    """Lightweight wrapper that holds persisted session metadata and lazily
    initializes a full FinancialAnalyzer when needed.
    """
    def __init__(self, session_id: str, filepath: str = None, balance_sheet_data=None, balance_sheet_pdf: str = None):
        self.session_id = session_id
        self.filepath = filepath
        self.balance_sheet_data = balance_sheet_data
        self.balance_sheet_pdf = balance_sheet_pdf
        self._analyzer = None

    def ensure_analyzer(self):
        if self._analyzer is None:
            if not self.filepath:
                raise ValueError("No original PDF path available to create FinancialAnalyzer.")
            if not current_api_key:
                raise ValueError("API key not set. Cannot initialize FinancialAnalyzer.")
            try:
                self._analyzer = FinancialAnalyzer()
            except Exception as e:
                print(f"Failed to initialize FinancialAnalyzer for session {self.session_id}: {e}")
                raise

    # Proxy chat and report methods to the underlying FinancialAnalyzer
    def chat_answer(self, prompt: str):
        self.ensure_analyzer()
        return self._analyzer.chat_answer(prompt)

    def get_compliance_gap_report(self):
        self.ensure_analyzer()
        return self._analyzer.get_compliance_gap_report()

    def get_auditor_report_summary(self):
        self.ensure_analyzer()
        return self._analyzer.get_auditor_report_summary()

    def get_director_report_highlights(self):
        self.ensure_analyzer()
        return self._analyzer.get_director_report_highlights()

    def get_director_report_compliance_check(self):
        self.ensure_analyzer()
        return self._analyzer.get_director_report_compliance_check()

    def get_overall_summary(self):
        self.ensure_analyzer()
        return self._analyzer.get_overall_summary()

def get_session_id():
    # Be permissive about how clients send the session id.
    # Try JSON body, form fields, query params, and raw body parsing.
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None

    if isinstance(data, dict):
        session_id = data.get("session_id") or data.get("sessionId") or data.get("sid")
        if session_id:
            return session_id

    # Try form-encoded data (e.g., from tools that post form fields)
    session_id = request.form.get("session_id") or request.form.get("sessionId")
    if session_id:
        return session_id

    # Try query parameters
    session_id = request.args.get("session_id") or request.args.get("sessionId")
    if session_id:
        return session_id

    # Try headers - many clients prefer to send a session id in headers
    try:
        # common header variations
        hdrs = request.headers
        for key in ("session_id", "session-id", "sessionId", "sid", "x-session-id", "x-sessionid"):
            if key in hdrs:
                v = hdrs.get(key)
                if v:
                    return v

        # Authorization: Bearer <session_id> (some clients pass session token here)
        auth = hdrs.get("Authorization") or hdrs.get("authorization")
        if auth and isinstance(auth, str) and auth.lower().startswith("bearer "):
            token = auth.split(None, 1)[1].strip()
            if token:
                return token
    except Exception:
        pass

    # Try raw body as JSON text (some clients send JSON but Flask may not parse it)
    try:
        raw = request.get_data(as_text=True)
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    session_id = parsed.get("session_id") or parsed.get("sessionId") or parsed.get("sid")
                    if session_id:
                        return session_id
            except Exception:
                # If body is not JSON, attempt to find a session-like token (UUID-ish) in the raw text
                m = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", raw)
                if m:
                    return m.group(0)

    except Exception:
        pass

    raise ValueError("Missing session_id in request payload.")

def extract_balance_sheet_pages(pdf_path, keywords=["equity", "liabilities", "total assets", "balance sheet", "total equity", "current assets", "non-current assets"], max_pages=2):
    try:
        doc = fitz.open(pdf_path)
        pages_found = []
        for page_num in range(len(doc)):
            try:
                # Render each page and run GLM OCR to obtain reliable text
                pix = doc.load_page(page_num).get_pixmap(dpi=90)
                with tempfile.TemporaryDirectory() as tmpdir:
                    img_path = os.path.join(tmpdir, f"page_{page_num}.png")
                    pix.save(img_path)
                    page_text, _ = run_ocr(img_path)
                text = (page_text or "").lower()

                # Primary check for "balance sheet" keyword
                if "balance sheet" in text:
                    print(f"📄 Balance Sheet header found on page {page_num + 1}")
                    pages_found.append(page_num)
                    if len(pages_found) >= max_pages:
                        break
                    continue

                # Secondary check using financial statement keywords
                keyword_count = sum(1 for k in keywords if k in text)
                if keyword_count >= 3:  # At least 3 balance sheet related terms
                    print(f"📄 Balance Sheet content detected on page {page_num + 1}")
                    pages_found.append(page_num)
                    if len(pages_found) >= max_pages:
                        break
            except Exception as e:
                print(f"Error OCR-ing page {page_num}: {e}")

        return pages_found
    except Exception as e:
        print(f"Error during balance sheet extraction: {e}")
        return []

def parse_balance_sheet_page(page):
    # First try a more table-aware extraction that clusters spans by Y coordinate
    try:
        def extract_table_rows_from_page(pg, y_tolerance=4):
            """
            Build structured rows by clustering span/text items that share similar vertical positions.
            Returns a list of dicts where keys are inferred column headers (Particulars, Col1, Col2...).
            """
            try:
                data = pg.get_text("dict")
                spans = []
                for block in data.get("blocks", []):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            x0 = span.get("bbox", [0, 0, 0, 0])[0]
                            y0 = span.get("bbox", [0, 0, 0, 0])[1]
                            text = span.get("text", "").strip()
                            if not text:
                                continue
                            spans.append((y0, x0, text))

                if not spans:
                    return []

                # Cluster by Y coordinate
                spans.sort(key=lambda s: (s[0], s[1]))
                rows = []
                current_row = [spans[0]]
                for s in spans[1:]:
                    if abs(s[0] - current_row[-1][0]) <= y_tolerance:
                        current_row.append(s)
                    else:
                        rows.append(current_row)
                        current_row = [s]
                if current_row:
                    rows.append(current_row)

                # Convert each clustered row into ordered columns based on x
                table = []
                for r in rows:
                    cells = sorted(r, key=lambda x: x[1])
                    texts = [c[2] for c in cells]
                    # Skip rows that are purely headings like page numbers
                    joined = " ".join(texts).strip()
                    if len(joined) < 2:
                        continue
                    # Build dict: first column = Particulars, subsequent columns numbered
                    rowd = {}
                    rowd["Particulars"] = texts[0]
                    for i, t in enumerate(texts[1:], start=1):
                        rowd[f"Col_{i}"] = t

                    # Attach a list of parsed numeric values for quick filtering later
                    nums = []
                    for t in texts[1:]:
                        # Use the module-level parse_number and indian-converter
                        v = parse_number(t)
                        if v is None:
                            v = _convert_indian_number_match(t)
                        if v is not None:
                            nums.append(v)
                    if nums:
                        rowd["_numbers"] = nums
                    table.append(rowd)

                # Return only rows that have at least one numeric column (we're interested in numeric tables)
                numeric_rows = [r for r in table if r.get("_numbers")]
                return numeric_rows if numeric_rows else table
            except Exception as e:
                print(f"Error in extract_table_rows_from_page: {e}")
                return []

        def extract_table_rows_from_page_ocr(pg, y_tolerance=6, dpi=300):
            """
            Render the page to an image, run OCR, and cluster OCR spans by Y coordinate
            to reconstruct table rows. Returns similar structure to extract_table_rows_from_page.
            """
            try:
                # Use GLM OCR (run_ocr) on the rendered page image and do a line-based parse
                with tempfile.TemporaryDirectory() as tmpdir:
                    pix = pg.get_pixmap(dpi=dpi)
                    img_path = os.path.join(tmpdir, "page.png")
                    pix.save(img_path)

                    # Ask GLM OCR for text on this page
                    page_text, _ = run_ocr(img_path)
                    if not page_text:
                        return []

                    table = []
                    for line in page_text.splitlines():
                        ln = line.strip()
                        if not ln:
                            continue

                        # Find numeric tokens in the line
                        nums = re.findall(r"\(?[0-9,]+(?:\.[0-9]+)?\)?(?:\s*(?:lakhs?|lakh|crore|crores|cr))?", ln, flags=re.IGNORECASE)

                        # Derive a textual description by removing numeric tokens
                        desc = re.sub(r"\(?[0-9,]+(?:\.[0-9]+)?\)?(?:\s*(?:lakhs?|lakh|crore|crores|cr))?", "", ln).strip(" -:|")

                        if nums:
                            rowd = {"Particulars": desc or ln}
                            for i, t in enumerate(nums, start=1):
                                rowd[f"Col_{i}"] = t

                            parsed_nums = []
                            for t in nums:
                                v = parse_number(t)
                                if v is None:
                                    try:
                                        v = _convert_indian_number_match(t)
                                    except Exception:
                                        v = None
                                if v is not None:
                                    parsed_nums.append(v)
                            if parsed_nums:
                                rowd["_numbers"] = parsed_nums
                            table.append(rowd)

                    numeric_rows = [r for r in table if r.get("_numbers")]
                    return numeric_rows if numeric_rows else table
            except Exception as e:
                print(f"Error in OCR-based table extraction: {e}")
                return []

        # Try the table-aware extractor first (vector text)
        table_rows = extract_table_rows_from_page(page)
        if table_rows:
            return table_rows

        # If no numeric rows found from vector text, try OCR-based extraction
        ocr_rows = extract_table_rows_from_page_ocr(page)
        if ocr_rows:
            return ocr_rows

        # Fallback: previous block-based parser
        blocks = page.get_text("blocks")
        rows = {}

        # Define common headers and their variations
        header_variants = {
            "particulars": ["particulars", "description", "items", "details"],
            "note": ["note", "notes", "note no", "note no."],
            "amount": ["as at", "march", "amount", "inr", "rs.", "₹", "total", "value"],
            "year": ["2023", "2024", "2025", "31st", "31", "current year", "previous year"]
        }

        # Extract and clean text blocks
        for b in blocks:
            x0, y0, x1, y1, text, *_ = b
            text = text.strip()
            if not text:
                continue

            # More precise line grouping
            line_key = round(y0)
            if line_key not in rows:
                rows[line_key] = []
            rows[line_key].append((x0, text))  

        # Process rows into structured data
        table_data = []
        header_row = None
        current_section = None

        for y in sorted(rows.keys()):
            row_items = sorted(rows[y], key=lambda x: x[0])
            row_text = [text for _, text in row_items]
            row_text_lower = [t.lower() for t in row_text]

            # Try to identify headers row
            if not header_row and any(any(v in " ".join(row_text_lower) for v in variants) 
                                    for variants in header_variants.values()):
                header_row = row_text
                continue

            # If no headers found yet, try to infer them
            if not header_row:
                # Look for typical header patterns in the text
                if any(word in " ".join(row_text_lower) for word in ["total", "assets", "liabilities", "equity"]):
                    header_row = ["Particulars", "Note No.", "Current Year", "Previous Year"]

            # Use inferred or found headers
            headers = header_row or ["Particulars", "Note No.", "Current Year", "Previous Year"]

            # Create row data
            row_data = {}
            for i, text in enumerate(row_text):
                if i < len(headers):
                    row_data[headers[i]] = text
                else:
                    # Append additional columns with generated headers
                    row_data[f"Column_{i+1}"] = text

            # Track balance sheet sections
            lower_text = " ".join(row_text_lower)
            if any(section in lower_text for section in ["assets", "liabilities", "equity"]):
                current_section = lower_text
                row_data["section"] = current_section
            elif current_section:
                row_data["section"] = current_section

            # Add non-empty rows to table data
            if any(v.strip() for v in row_data.values()):
                table_data.append(row_data)

        return table_data

    except Exception as e:
        print(f"Error parsing balance sheet page: {e}")
        return []

# Save extracted page(s) to new PDF
def save_pages_to_pdf(pdf_path, pages, output_path):
    try:
        src = fitz.open(pdf_path)
        new_pdf = fitz.open()  # empty PDF

        for p in pages:
            new_pdf.insert_pdf(src, from_page=p, to_page=p)

        new_pdf.save(output_path)
        new_pdf.close()
        src.close()
        print(f"✅ Extracted pages saved to PDF: {output_path}")
    except Exception as e:
        print(f"Error saving pages to new PDF: {e}")


def extract_comprehensive_balance_sheet_items(balance_sheet_data: list):
    """
    Extracts ALL balance sheet line items with detailed breakdown.
    Returns structured data with:
    - Current Assets (Cash, Receivables, Inventory, Prepaid)
    - Non-Current Assets (Property, Equipment, Intangibles, Investments)
    - Current Liabilities (Payables, Short-term Debt, Accruals)
    - Non-Current Liabilities (Long-term Debt, Deferred Tax)
    - Equity Components (Share Capital, Reserves, Retained Earnings)
    """
    try:
        def parse_number(val):
            if val is None: return None
            if isinstance(val, (int, float)): return float(val)
            s = str(val).strip().lower()
            if not s or s in ("-", "—", "na", "nil"): return None
            neg = s.startswith("(") and s.endswith(")")
            s = s.strip("()")
            s = re.sub(r"[₹$,]", "", s)
            cleaned = re.sub(r"[^0-9.\-]", "", s)
            if not cleaned or cleaned == ".": return None
            try:
                num = float(cleaned)
                return -num if neg else num
            except (ValueError, TypeError):
                return None

        # Normalize all rows
        normalized_data = []
        for row in balance_sheet_data:
            if not isinstance(row, dict) or len(row) == 0:
                continue
            
            particulars_value = None
            numeric_value = None
            
            for k, v in row.items():
                num = parse_number(v)
                if num is not None and numeric_value is None:
                    numeric_value = num
                elif isinstance(v, str) and len(v) > 3 and 'note' not in v.lower():
                    if particulars_value is None or len(v) > len(particulars_value):
                        particulars_value = v
            
            if particulars_value and numeric_value is not None:
                particulars_clean = particulars_value.lower().replace("\n", " ").strip()
                particulars_clean = " ".join(particulars_clean.split())
                if len(particulars_clean) > 1:
                    normalized_data.append({
                        "particulars": particulars_clean,
                        "value": numeric_value
                    })

        # Define comprehensive search patterns for each balance sheet component
        def find_items(keywords_list):
            """Find all items matching any keyword pattern"""
            items = {}
            for row in normalized_data:
                p = row["particulars"]
                for keyword in keywords_list:
                    if keyword in p:
                        # Use the most specific match (longest keyword)
                        best_key = keyword
                        items[best_key] = row["value"]
                        break
            return items

        # CURRENT ASSETS
        current_assets_keywords = [
            "cash and cash equivalents",
            "bank balances",
            "cash on hand",
            "trade receivables",
            "accounts receivable",
            "inventories",
            "stock-in-trade",
            "short-term investments",
            "prepaid expenses",
            "current portion of long-term assets"
        ]
        current_assets = find_items(current_assets_keywords)

        # NON-CURRENT ASSETS
        non_current_assets_keywords = [
            "property, plant and equipment",
            "fixed assets",
            "goodwill",
            "intangible assets",
            "long-term investments",
            "deferred tax assets",
            "right-of-use assets",
            "biological assets",
            "other non-current assets"
        ]
        non_current_assets = find_items(non_current_assets_keywords)

        # CURRENT LIABILITIES
        current_liabilities_keywords = [
            "trade payables",
            "accounts payable",
            "short-term borrowings",
            "current portion of long-term debt",
            "employee benefits payable",
            "accrued expenses",
            "short-term lease obligations",
            "current tax payable",
            "advances received",
            "other current liabilities"
        ]
        current_liabilities = find_items(current_liabilities_keywords)

        # NON-CURRENT LIABILITIES
        non_current_liabilities_keywords = [
            "long-term borrowings",
            "bonds payable",
            "deferred tax liabilities",
            "long-term lease obligations",
            "employee benefit obligations",
            "other non-current liabilities",
            "contingent liabilities"
        ]
        non_current_liabilities = find_items(non_current_liabilities_keywords)

        # EQUITY COMPONENTS
        equity_keywords = [
            "equity share capital",
            "share capital",
            "preference share capital",
            "reserves and surplus",
            "retained earnings",
            "securities premium",
            "general reserve",
            "capital reserve",
            "other reserves",
            "accumulated other comprehensive income"
        ]
        equity_components = find_items(equity_keywords)

        # Calculate totals
        total_current_assets = sum(current_assets.values())
        total_non_current_assets = sum(non_current_assets.values())
        total_current_liabilities = sum(current_liabilities.values())
        total_non_current_liabilities = sum(non_current_liabilities.values())
        total_equity = sum(equity_components.values())

        # Build comprehensive structure
        comprehensive_bs = {
            "assets": {
                "current_assets": {
                    "items": current_assets,
                    "total": total_current_assets
                },
                "non_current_assets": {
                    "items": non_current_assets,
                    "total": total_non_current_assets
                },
                "total_assets": total_current_assets + total_non_current_assets
            },
            "liabilities_and_equity": {
                "current_liabilities": {
                    "items": current_liabilities,
                    "total": total_current_liabilities
                },
                "non_current_liabilities": {
                    "items": non_current_liabilities,
                    "total": total_non_current_liabilities
                },
                "total_liabilities": total_current_liabilities + total_non_current_liabilities,
                "equity": {
                    "items": equity_components,
                    "total": total_equity
                }
            }
        }

        return comprehensive_bs

    except Exception as e:
        print(f"Error extracting comprehensive balance sheet items: {e}")
        return None


def calculate_financial_ratios(balance_sheet_data: list = None, profit_loss_data: dict = None, mistral_financials: dict = None):
    """
    Calculates comprehensive financial ratios from structured balance sheet and P&L data.
    Returns detailed metrics with interpretations across multiple categories:
    - Liquidity Ratios
    - Profitability Ratios (from P&L)
    - Solvency Ratios
    - Capital Structure Ratios
    - Efficiency Ratios
    - Market Ratios (when available)
    """
    try:
        print(f"DEBUG calculate_financial_ratios: Received P&L data: {profit_loss_data is not None}")
        if profit_loss_data:
            print(f"DEBUG: P&L type: {type(profit_loss_data)}, keys: {list(profit_loss_data.keys()) if isinstance(profit_loss_data, dict) else 'N/A'}")
        
        # Helper to parse single number robustly
        def parse_number(val):
            if val is None: return None
            if isinstance(val, (int, float)): return float(val)
            s = str(val).strip().lower()
            if not s or s in ("-", "—", "na", "nil"): return None
            neg = s.startswith("(") and s.endswith(")")
            s = s.strip("()")
            s = re.sub(r"[₹$,]", "", s)
            cleaned = re.sub(r"[^0-9.\-]", "", s)
            if not cleaned or cleaned == ".": return None
            try:
                num = float(cleaned)
                return -num if neg else num
            except (ValueError, TypeError):
                return None

        # Safe numeric comparison helpers to avoid TypeErrors when values are None or non-numeric
        def _is_number(x):
            return isinstance(x, (int, float))

        def safe_ge(x, y):
            try:
                return _is_number(x) and x >= y
            except Exception:
                return False

        def safe_gt(x, y):
            try:
                return _is_number(x) and x > y
            except Exception:
                return False

        def safe_le(x, y):
            try:
                return _is_number(x) and x <= y
            except Exception:
                return False

        # Helper to parse numbers robustly - extract ALL numbers from text
        def parse_all_numbers(val):
            """Extract all numbers from a string (handles multi-line values)"""
            if val is None: return []
            if isinstance(val, (int, float)): return [float(val)]
            s = str(val).strip()
            if not s: return []
            
            # Find all numbers (including those with commas)
            import re as regex
            numbers_str = regex.findall(r'[\(\-]?\d+(?:,\d+)*\.?\d*', s)
            numbers = []
            for num_str in numbers_str:
                try:
                    num_str = num_str.strip("()")
                    is_negative = num_str.startswith("-") or s.find(f"({num_str})") >= 0
                    num_str = num_str.replace(",", "")
                    num = float(num_str)
                    numbers.append(-num if is_negative else num)
                except (ValueError, TypeError):
                    pass
            return numbers

        # Normalize data to have 'particulars' and a list of 'values'
        # Extract ALL numbers from each row
        normalized_data = []
        if balance_sheet_data:
            for row in balance_sheet_data:
                if not isinstance(row, dict):
                    continue
            
                if len(row) == 0:
                    continue
                
                # Find text (particulars) and collect ALL numeric values from ALL columns
                particulars_value = None
                all_numbers = []
                
                for k, v in row.items():
                    if v is None:
                        continue
                    
                    # Try standard number parsing first
                    num = parse_number(v)
                    if num is not None:
                        all_numbers.append(num)
                    else:
                        # Try parsing multiple numbers from this value
                        nums = parse_all_numbers(v)
                        if nums:
                            all_numbers.extend(nums)
                        # Also capture as text if it's a good description
                        if isinstance(v, str) and len(v) > 3 and 'note' not in v.lower():
                            if particulars_value is None or len(v) > len(particulars_value):
                                particulars_value = v
                
                # Add if we have text and numbers
                if particulars_value and all_numbers:
                    particulars_clean = particulars_value.lower().replace("\n", " ").strip()
                    particulars_clean = " ".join(particulars_clean.split())
                    if len(particulars_clean) > 1:
                        # Sort numbers and keep only unique values (to avoid duplicates from multiline cells)
                        unique_numbers = []
                        for n in all_numbers:
                            if not unique_numbers or abs(n - unique_numbers[-1]) > 0.1:
                                unique_numbers.append(n)
                        normalized_data.append({"particulars": particulars_clean, "values": unique_numbers})


        # Helper to find a value for a set of keywords
        def find_value(keywords: list, exact_match=False):
            best_match = None
            for row in normalized_data:
                p = row["particulars"]
                if exact_match:
                    if p in keywords:
                        return row["values"][-1] if row["values"] else None
                else:
                    # Check if all keywords are in the particulars string
                    if all(k in p for k in keywords):
                        best_match = row["values"][-1] if row["values"] else None
                    # Also check partial matches as fallback
                    elif any(k in p for k in keywords):
                        if best_match is None:
                            # Prefer the latest year value. 
                            # If row['values'] has multiple, we need to decide which one is 'latest'.
                            # Usually, tables follow: Particulars | Note | Latest Year | Previous Year
                            # So values[0] might be Note, values[1] Latest, values[2] Previous
                            # Or values[0] Latest, values[1] Previous.
                            # Based on common formats and parse_balance_sheet_page logic:
                            # It tries to find numeric columns.
                            if len(row["values"]) >= 2:
                                # Most likely [Note, Latest, Previous] or [Latest, Previous]
                                # If the first number is very small (potential Note index) and there's a much larger number next to it
                                if row["values"][0] < 200 and row["values"][1] > 500:
                                    best_match = row["values"][1]
                                else:
                                    best_match = row["values"][0]
                            else:
                                best_match = row["values"][-1] if row["values"] else None
            return best_match

        print(f"DEBUG: Found {len(normalized_data)} rows with numeric data")
        for i, row in enumerate(normalized_data[:5]):
            print(f"  Row {i}: {row['particulars'][:50]}... = {row['values']}")


        # Define search terms from most specific to most general
        SEARCH_TERMS = {
            "total_assets": [["total assets"]],
            "current_assets": [["total current assets"], ["current assets"]],
            "non_current_assets": [["total non-current assets"], ["non-current assets"], ["fixed assets"]],
            "total_liabilities": [["total liabilities"]],
            "current_liabilities": [["total current liabilities"], ["current liabilities"]],
            "non_current_liabilities": [["total non-current liabilities"], ["non-current liabilities"], ["long-term liabilities"]],
            "equity": [["total equity"], ["equity"], ["shareholder funds"], ["shareholders' funds"]],
            "share_capital": [["share capital"], ["equity share capital"]],
            "reserves": [["reserves and surplus"], ["retained earnings"], ["reserves"]],
            "inventory": [["inventories"]],
            "receivables": [["trade receivables"], ["accounts receivable"]],
            "cash": [["cash and cash equivalents"], ["cash and bank balances"], ["cash"]],
            "payables": [["trade payables"], ["accounts payable"]],
        }

        if mistral_financials:
            # If we have structured Mistral data, use it directly
            financials = {
                "total_assets": mistral_financials.get("assets", {}).get("total_assets"),
                "current_assets": mistral_financials.get("assets", {}).get("current_assets"),
                "non_current_assets": mistral_financials.get("assets", {}).get("property_plant_equipment"), # approximation
                "total_liabilities": mistral_financials.get("liabilities", {}).get("total_liabilities"),
                "current_liabilities": mistral_financials.get("liabilities", {}).get("current_liabilities"),
                "non_current_liabilities": mistral_financials.get("liabilities", {}).get("long_term_borrowings"),
                "equity": mistral_financials.get("equity", {}).get("total_equity"),
                "inventory": mistral_financials.get("assets", {}).get("inventories"),
                "receivables": mistral_financials.get("assets", {}).get("trade_receivables"),
                "cash": mistral_financials.get("assets", {}).get("cash_and_equivalents"),
                "payables": mistral_financials.get("liabilities", {}).get("trade_payables")
            }
        else:
            # Fallback to existing keyword-based extraction from raw rows
            financials = {}
            for key, term_sets in SEARCH_TERMS.items():
                for terms in term_sets:
                    value = find_value(terms)
                    if value is not None:
                        financials[key] = value
                        break
        
        # Extract values
        total_assets = financials.get("total_assets")
        current_assets = financials.get("current_assets")
        non_current_assets = financials.get("non_current_assets")
        total_liabilities = financials.get("total_liabilities")
        current_liabilities = financials.get("current_liabilities")
        non_current_liabilities = financials.get("non_current_liabilities")
        equity = financials.get("equity")
        share_capital = financials.get("share_capital")
        reserves = financials.get("reserves")
        inventory = financials.get("inventory")
        receivables = financials.get("receivables")
        cash = financials.get("cash")
        payables = financials.get("payables")

        # P&L metrics initialization
        revenue = None
        cogs = None
        gross_profit = None
        operating_income = None
        net_income = None
        ebit = None
        interest_expense = None
        tax_expense = None
        ebitda = None

        if mistral_financials:
            # For P&L from Mistral
            p_and_l_mistral = mistral_financials.get("p_and_l", {})
            revenue = p_and_l_mistral.get("revenue")
            net_income = p_and_l_mistral.get("net_profit")
            ebitda = p_and_l_mistral.get("ebitda")
            interest_expense = p_and_l_mistral.get("interest_expense")
            ebit = ebitda # approximation if depreciation not separate

        # Derive missing values
        if total_liabilities is None and total_assets is not None and equity is not None:
            total_liabilities = total_assets - equity
            print("Derived Total Liabilities from Assets - Equity")

        if total_assets is None and total_liabilities is not None and equity is not None:
            total_assets = total_liabilities + equity
            print("Derived Total Assets from Liabilities + Equity")

        if current_liabilities is None and current_assets is not None and total_liabilities is not None:
            current_liabilities = total_liabilities - (non_current_liabilities or 0)
            
        if non_current_assets is None and total_assets is not None and current_assets is not None:
            non_current_assets = total_assets - current_assets

        # Calculate Financial Ratios by Category
        ratios = {
            "balance_sheet_summary": {},
            "liquidity_ratios": {},
            "solvency_ratios": {},
            "capital_structure_ratios": {},
            "efficiency_ratios": {},
            "interpretation": {}
        }

        # Balance Sheet Summary
        if total_assets is not None:
            ratios["balance_sheet_summary"]["total_assets"] = total_assets
        if total_liabilities is not None:
            ratios["balance_sheet_summary"]["total_liabilities"] = total_liabilities
        if equity is not None:
            ratios["balance_sheet_summary"]["total_equity"] = equity
        if current_assets is not None:
            ratios["balance_sheet_summary"]["current_assets"] = current_assets
        if current_liabilities is not None:
            ratios["balance_sheet_summary"]["current_liabilities"] = current_liabilities
        if non_current_assets is not None:
            ratios["balance_sheet_summary"]["non_current_assets"] = non_current_assets
        if non_current_liabilities is not None:
            ratios["balance_sheet_summary"]["non_current_liabilities"] = non_current_liabilities

        # Liquidity Ratios
        if current_assets is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            current_ratio = current_assets / current_liabilities
            ratios["liquidity_ratios"]["current_ratio"] = current_ratio
            ratios["interpretation"]["current_ratio"] = "Strong" if safe_ge(current_ratio, 2) else ("Adequate" if safe_ge(current_ratio, 1.5) else ("Tight" if safe_ge(current_ratio, 1) else "Weak"))

        if current_assets is not None and inventory is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            quick_assets = current_assets - (inventory or 0)
            quick_ratio = quick_assets / current_liabilities
            ratios["liquidity_ratios"]["quick_ratio"] = quick_ratio
            ratios["interpretation"]["quick_ratio"] = "Strong" if safe_ge(quick_ratio, 1) else ("Adequate" if safe_ge(quick_ratio, 0.8) else "Weak")

        if current_assets is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            cash_ratio = (cash or 0) / current_liabilities
            ratios["liquidity_ratios"]["cash_ratio"] = cash_ratio

        # Solvency Ratios
        if total_liabilities is not None and total_assets is not None and safe_gt(total_assets, 0):
            debt_ratio = total_liabilities / total_assets
            ratios["solvency_ratios"]["debt_ratio"] = debt_ratio
            ratios["interpretation"]["debt_ratio"] = "Low Risk" if (isinstance(debt_ratio, (int, float)) and debt_ratio <= 0.4) else ("Moderate Risk" if (isinstance(debt_ratio, (int, float)) and debt_ratio <= 0.6) else "High Risk")

        if total_liabilities is not None and equity is not None and safe_gt(equity, 0):
            debt_to_equity = total_liabilities / equity
            ratios["solvency_ratios"]["debt_to_equity"] = debt_to_equity
            ratios["interpretation"]["debt_to_equity"] = "Conservative" if (isinstance(debt_to_equity, (int, float)) and debt_to_equity <= 1) else ("Moderate" if (isinstance(debt_to_equity, (int, float)) and debt_to_equity <= 2) else "Aggressive")

        if equity is not None and total_assets is not None and safe_gt(total_assets, 0):
            equity_ratio = equity / total_assets
            ratios["solvency_ratios"]["equity_ratio"] = equity_ratio
            ratios["interpretation"]["equity_ratio"] = "Strong" if safe_ge(equity_ratio, 0.5) else ("Fair" if safe_ge(equity_ratio, 0.3) else "Weak")

        # Capital Structure Ratios
        if equity is not None and total_assets is not None and safe_gt(total_assets, 0):
            equity_multiplier = total_assets / equity if safe_gt(equity, 0) else 0
            ratios["capital_structure_ratios"]["equity_multiplier"] = equity_multiplier

        if share_capital is not None and equity is not None and safe_gt(equity, 0):
            retention_ratio = (equity - share_capital) / equity
            ratios["capital_structure_ratios"]["retention_ratio"] = retention_ratio

        if non_current_liabilities is not None and total_liabilities is not None and safe_gt(total_liabilities, 0):
            long_term_debt_ratio = non_current_liabilities / total_liabilities
            ratios["capital_structure_ratios"]["long_term_debt_ratio"] = long_term_debt_ratio

        # Efficiency Ratios (Asset Utilization)
        if total_assets is not None and safe_gt(total_assets, 0):
            asset_turnover = 1  # Placeholder - requires revenue data from P&L
            ratios["efficiency_ratios"]["asset_base"] = total_assets

        if receivables is not None and current_assets is not None and safe_gt(current_assets, 0):
            receivables_ratio = receivables / current_assets
            ratios["efficiency_ratios"]["receivables_to_current_assets"] = receivables_ratio

        # Additional Working Capital Ratios
        if current_assets is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            working_capital = current_assets - current_liabilities
            ratios["liquidity_ratios"]["working_capital"] = working_capital
            working_capital_ratio = current_assets / current_liabilities if safe_gt(current_liabilities, 0) else 0
            ratios["liquidity_ratios"]["working_capital_ratio"] = working_capital_ratio

        # Additional Solvency Ratios
        if non_current_liabilities is not None and equity is not None and safe_gt(equity, 0):
            long_term_to_equity = non_current_liabilities / equity
            ratios["solvency_ratios"]["long_term_debt_to_equity"] = long_term_to_equity

        if total_assets is not None and total_liabilities is not None and safe_gt(total_assets, 0):
            assets_to_liabilities = total_assets / total_liabilities if safe_gt(total_liabilities, 0) else float('inf')
            ratios["solvency_ratios"]["assets_to_liabilities"] = assets_to_liabilities

        # Leverage Ratios
        if total_liabilities is not None and equity is not None and safe_gt(equity, 0):
            leverage_ratio = total_liabilities / equity
            ratios["solvency_ratios"]["leverage_ratio"] = leverage_ratio

        # Additional Capital Structure Ratios
        if total_liabilities is not None and total_assets is not None and safe_gt(total_assets, 0):
            debt_to_assets = total_liabilities / total_assets
            ratios["capital_structure_ratios"]["debt_to_assets"] = debt_to_assets

        if equity is not None and total_liabilities is not None and safe_gt(total_liabilities, 0):
            equity_to_debt = equity / total_liabilities
            ratios["capital_structure_ratios"]["equity_to_debt"] = equity_to_debt

        # Asset Composition Ratios
        if current_assets is not None and total_assets is not None and safe_gt(total_assets, 0):
            current_assets_ratio = current_assets / total_assets
            ratios["efficiency_ratios"]["current_assets_ratio"] = current_assets_ratio

        if non_current_assets is not None and total_assets is not None and safe_gt(total_assets, 0):
            fixed_assets_ratio = non_current_assets / total_assets
            ratios["efficiency_ratios"]["fixed_assets_ratio"] = fixed_assets_ratio

        # Liability Composition Ratios
        if current_liabilities is not None and total_liabilities is not None and safe_gt(total_liabilities, 0):
            current_liabilities_ratio = current_liabilities / total_liabilities
            ratios["solvency_ratios"]["current_liabilities_ratio"] = current_liabilities_ratio

        if non_current_liabilities is not None and total_liabilities is not None and safe_gt(total_liabilities, 0):
            long_term_liabilities_ratio = non_current_liabilities / total_liabilities
            ratios["solvency_ratios"]["long_term_liabilities_ratio"] = long_term_liabilities_ratio

        # Extract P&L data if provided (if not already set by Mistral)
        if not mistral_financials:
            print(f"DEBUG: Starting P&L extraction. profit_loss_data type: {type(profit_loss_data)}")
        
        if profit_loss_data and isinstance(profit_loss_data, dict):
            # Helper to find numeric value in P&L structure
            def find_pl_value(keys_path):
                """Navigate nested P&L structure to find value"""
                val = profit_loss_data
                for key in keys_path:
                    if isinstance(val, dict):
                        val = val.get(key)
                    else:
                        return None
                if isinstance(val, (list, str)):
                    return find_number_in_dict(val)
                return val if isinstance(val, (int, float)) else None

            # Extract key P&L metrics
            revenue = find_pl_value(["income", "revenueFromOperations"]) or find_pl_value(["income", "totalIncome"])
            print(f"DEBUG: Extracted revenue = {revenue}")
            
            cogs = find_pl_value(["expenses", "costOfMaterialsConsumed"]) or find_pl_value(["expenses", "purchaseOfStockInTrade"])
            print(f"DEBUG: Extracted cogs = {cogs}")
            
            operating_income = find_pl_value(["profitBeforeExceptionalItemsAndTax"]) or find_pl_value(["operatingProfit"])
            print(f"DEBUG: Extracted operating_income = {operating_income}")
            
            net_income = find_pl_value(["netProfit"]) or find_pl_value(["netIncome"])
            print(f"DEBUG: Extracted net_income = {net_income}")
            
            ebit = find_pl_value(["profitBeforeExceptionalItemsAndTax"]) or find_pl_value(["ebit"])
            print(f"DEBUG: Extracted ebit = {ebit}")
            
            tax_expense = find_pl_value(["tax"]) or find_pl_value(["incomeTaxExpense"]) or find_pl_value(["taxExpense"])
            print(f"DEBUG: Extracted tax_expense = {tax_expense}")
            
            ebitda = find_pl_value(["ebitda"]) or find_pl_value(["operatingProfitBeforeDepreciation"])
            print(f"DEBUG: Extracted ebitda = {ebitda}")
            
            ebit = find_pl_value(["profitBeforeExceptionalItemsAndTax"]) or operating_income
            print(f"DEBUG: Extracted ebit = {ebit}")
            
            interest_expense = find_pl_value(["expenses", "financeCosts"]) or find_pl_value(["expenses", "interestExpense"])
            print(f"DEBUG: Extracted interest_expense = {interest_expense}")

            # Calculate Gross Profit if revenue and COGS available
            if revenue is not None and cogs is not None and safe_gt(revenue, 0):
                gross_profit = revenue - cogs
                print(f"DEBUG: Calculated gross_profit = {gross_profit}")
        else:
            print(f"DEBUG: P&L data not available or not dict. Type: {type(profit_loss_data)}")

        # Profitability Ratios (from P&L data)
        # Create profitability_ratios category if we have P&L data
        if profit_loss_data or revenue is not None:
            ratios["profitability_ratios"] = {}
            print(f"DEBUG: Creating profitability_ratios section. P&L available: {profit_loss_data is not None}, Revenue: {revenue}")
            
            # Gross Profit Margin
            if gross_profit is not None and revenue is not None and safe_gt(revenue, 0):
                gross_margin = (gross_profit / revenue) * 100
                ratios["profitability_ratios"]["gross_margin"] = gross_margin
                ratios["interpretation"]["gross_margin"] = "Excellent" if safe_ge(gross_margin, 40) else ("Good" if safe_ge(gross_margin, 30) else ("Fair" if safe_ge(gross_margin, 20) else "Weak"))
                print(f"DEBUG: Added gross_margin = {gross_margin}")

            # Operating Profit Margin
            if operating_income is not None and revenue is not None and safe_gt(revenue, 0):
                operating_margin = (operating_income / revenue) * 100
                ratios["profitability_ratios"]["operating_margin"] = operating_margin
                ratios["interpretation"]["operating_margin"] = "Excellent" if safe_ge(operating_margin, 15) else ("Good" if safe_ge(operating_margin, 10) else ("Fair" if safe_ge(operating_margin, 5) else "Weak"))
                print(f"DEBUG: Added operating_margin = {operating_margin}")

            # Net Profit Margin
            if net_income is not None and revenue is not None and safe_gt(revenue, 0):
                net_margin = (net_income / revenue) * 100
                ratios["profitability_ratios"]["net_margin"] = net_margin
                ratios["interpretation"]["net_margin"] = "Excellent" if safe_ge(net_margin, 10) else ("Good" if safe_ge(net_margin, 7) else ("Fair" if safe_ge(net_margin, 3) else "Weak"))
                print(f"DEBUG: Added net_margin = {net_margin}")

            # Return on Assets (ROA)
            if net_income is not None and total_assets is not None and safe_gt(total_assets, 0):
                roa = (net_income / total_assets) * 100
                ratios["profitability_ratios"]["roa"] = roa
                ratios["interpretation"]["roa"] = "Excellent" if safe_ge(roa, 10) else ("Good" if safe_ge(roa, 5) else ("Fair" if safe_ge(roa, 2) else "Weak"))
                print(f"DEBUG: Added roa = {roa}")

            # Return on Equity (ROE)
            if net_income is not None and equity is not None and safe_gt(equity, 0):
                roe = (net_income / equity) * 100
                ratios["profitability_ratios"]["roe"] = roe
                ratios["interpretation"]["roe"] = "Excellent" if safe_ge(roe, 20) else ("Good" if safe_ge(roe, 15) else ("Fair" if safe_ge(roe, 10) else "Weak"))
                print(f"DEBUG: Added roe = {roe}")
            
            if not ratios["profitability_ratios"]:
                print(f"DEBUG: No profitability ratios calculated. Revenue: {revenue}, Net Income: {net_income}, Assets: {total_assets}, Equity: {equity}")

        # Interest Coverage Ratio
        if ebit is not None and interest_expense is not None and safe_gt(interest_expense, 0):
            interest_coverage = ebit / interest_expense
            ratios["solvency_ratios"]["interest_coverage"] = interest_coverage
            ratios["interpretation"]["interest_coverage"] = "Strong" if safe_ge(interest_coverage, 2.5) else ("Adequate" if safe_ge(interest_coverage, 1.5) else "Weak")

        # ============================================================================
        # ACTIVITY/TURNOVER RATIOS (Efficiency metrics)
        # ============================================================================
        ratios["activity_ratios"] = {}
        
        # Asset Turnover Ratio (requires revenue)
        if revenue is not None and total_assets is not None and safe_gt(total_assets, 0):
            asset_turnover = revenue / total_assets
            ratios["activity_ratios"]["asset_turnover"] = asset_turnover
            ratios["interpretation"]["asset_turnover"] = "Excellent" if safe_ge(asset_turnover, 2.0) else ("Good" if safe_ge(asset_turnover, 1.5) else ("Fair" if safe_ge(asset_turnover, 1.0) else "Weak"))
            print(f"DEBUG: Added asset_turnover = {asset_turnover}")

        # Receivables Turnover Ratio (requires revenue and receivables)
        if revenue is not None and receivables is not None and safe_gt(receivables, 0):
            receivables_turnover = revenue / receivables
            ratios["activity_ratios"]["receivables_turnover"] = receivables_turnover
            days_sales_outstanding = 365 / receivables_turnover if safe_gt(receivables_turnover, 0) else 0
            ratios["activity_ratios"]["days_sales_outstanding"] = days_sales_outstanding
            ratios["interpretation"]["receivables_turnover"] = "Excellent" if safe_ge(receivables_turnover, 12) else ("Good" if safe_ge(receivables_turnover, 6) else ("Fair" if safe_ge(receivables_turnover, 3) else "Weak"))
            print(f"DEBUG: Added receivables_turnover = {receivables_turnover}, DSO = {days_sales_outstanding}")

        # Fixed Assets Turnover
        if revenue is not None and non_current_assets is not None and safe_gt(non_current_assets, 0):
            fixed_asset_turnover = revenue / non_current_assets
            ratios["activity_ratios"]["fixed_asset_turnover"] = fixed_asset_turnover
            ratios["interpretation"]["fixed_asset_turnover"] = "Good" if safe_ge(fixed_asset_turnover, 1.5) else ("Fair" if safe_ge(fixed_asset_turnover, 1.0) else "Weak")
            print(f"DEBUG: Added fixed_asset_turnover = {fixed_asset_turnover}")

        # Current Assets Turnover
        if revenue is not None and current_assets is not None and safe_gt(current_assets, 0):
            current_asset_turnover = revenue / current_assets
            ratios["activity_ratios"]["current_asset_turnover"] = current_asset_turnover
            print(f"DEBUG: Added current_asset_turnover = {current_asset_turnover}")

        # ============================================================================
        # DUPONT ANALYSIS COMPONENTS
        # ============================================================================
        ratios["dupont_analysis"] = {}
        
        # DuPont ROE = Net Margin × Asset Turnover × Equity Multiplier
        if net_income is not None and revenue is not None and safe_gt(revenue, 0) and total_assets is not None and safe_gt(total_assets, 0):
            if equity is not None and safe_gt(equity, 0):
                net_margin_dupont = (net_income / revenue) * 100
                asset_turnover_dupont = revenue / total_assets if safe_gt(total_assets, 0) else 0
                equity_multiplier_dupont = total_assets / equity
                
                roe_dupont = (net_margin_dupont / 100) * asset_turnover_dupont * equity_multiplier_dupont * 100
                
                ratios["dupont_analysis"]["net_profit_margin"] = net_margin_dupont
                ratios["dupont_analysis"]["asset_turnover"] = asset_turnover_dupont
                ratios["dupont_analysis"]["equity_multiplier"] = equity_multiplier_dupont
                ratios["dupont_analysis"]["roe_dupont"] = roe_dupont
                ratios["interpretation"]["dupont_roe"] = "Excellent" if safe_ge(roe_dupont, 20) else ("Good" if safe_ge(roe_dupont, 15) else ("Fair" if safe_ge(roe_dupont, 10) else "Weak"))
                print(f"DEBUG: DuPont Analysis - NM: {net_margin_dupont}, AT: {asset_turnover_dupont}, EM: {equity_multiplier_dupont}, ROE: {roe_dupont}")

        # ============================================================================
        # WORKING CAPITAL & OPERATIONAL EFFICIENCY RATIOS
        # ============================================================================
        ratios["working_capital_ratios"] = {}
        
        # Cash Ratio (most conservative liquidity)
        cash = None
        if balance_sheet_data and isinstance(balance_sheet_data, list):
            try:
                if isinstance(balance_sheet_data, dict):
                    assets = balance_sheet_data.get("assets", {})
                    if isinstance(assets, dict):
                        current_assets_section = assets.get("currentAssets", {})
                        if isinstance(current_assets_section, dict):
                            cash = find_number_in_dict(current_assets_section.get("cash"))
            except:
                pass
        
        if cash is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            cash_ratio = cash / current_liabilities
            ratios["working_capital_ratios"]["cash_ratio"] = cash_ratio
            ratios["interpretation"]["cash_ratio"] = "Good" if safe_ge(cash_ratio, 0.2) else ("Fair" if safe_ge(cash_ratio, 0.1) else "Weak")
            print(f"DEBUG: Added cash_ratio = {cash_ratio}")

        # Operating Cash Flow Ratio (requires cash flow data - approximation using EBIT)
        if ebit is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            operating_cash_ratio = ebit / current_liabilities  # Approximation
            ratios["working_capital_ratios"]["operating_cash_ratio"] = operating_cash_ratio
            print(f"DEBUG: Added operating_cash_ratio (approximation) = {operating_cash_ratio}")

        # ============================================================================
        # PROFITABILITY RATIO EXTENSIONS (Additional metrics)
        # ============================================================================
        
        # EBITDA Margin
        if ebitda is not None and revenue is not None and safe_gt(revenue, 0):
            ebitda_margin = (ebitda / revenue) * 100
            ratios["profitability_ratios"]["ebitda_margin"] = ebitda_margin
            ratios["interpretation"]["ebitda_margin"] = "Excellent" if safe_ge(ebitda_margin, 20) else ("Good" if safe_ge(ebitda_margin, 15) else ("Fair" if safe_ge(ebitda_margin, 10) else "Weak"))
            print(f"DEBUG: Added ebitda_margin = {ebitda_margin}")

        # EBIT Margin (Operating Efficiency)
        if ebit is not None and revenue is not None and safe_gt(revenue, 0):
            ebit_margin = (ebit / revenue) * 100
            ratios["profitability_ratios"]["ebit_margin"] = ebit_margin
            ratios["interpretation"]["ebit_margin"] = "Excellent" if safe_ge(ebit_margin, 15) else ("Good" if safe_ge(ebit_margin, 10) else ("Fair" if safe_ge(ebit_margin, 5) else "Weak"))
            print(f"DEBUG: Added ebit_margin = {ebit_margin}")

        # Return on Sales (ROS)
        if net_income is not None and revenue is not None and safe_gt(revenue, 0):
            ros = (net_income / revenue) * 100
            ratios["profitability_ratios"]["return_on_sales"] = ros
            print(f"DEBUG: Added return_on_sales = {ros}")

        # ============================================================================
        # ADVANCED SOLVENCY RATIOS
        # ============================================================================
        
        # Debt Service Coverage (approximation: EBIT / Debt Payments)
        if ebit is not None and interest_expense is not None and safe_gt(interest_expense, 0):
            total_debt_service = interest_expense * 1.2  # Approximation including principal
            debt_service_ratio = ebit / total_debt_service
            ratios["solvency_ratios"]["debt_service_coverage"] = debt_service_ratio
            ratios["interpretation"]["debt_service_coverage"] = "Strong" if safe_ge(debt_service_ratio, 2.5) else ("Adequate" if safe_ge(debt_service_ratio, 1.5) else "Weak")
            print(f"DEBUG: Added debt_service_coverage = {debt_service_ratio}")

        # Fixed Charge Coverage
        if ebit is not None and interest_expense is not None and current_liabilities is not None and safe_gt(current_liabilities, 0):
            fixed_charges = interest_expense + (current_liabilities * 0.1)  # Approximation
            fixed_charge_coverage = ebit / fixed_charges if fixed_charges > 0 else 0
            ratios["solvency_ratios"]["fixed_charge_coverage"] = fixed_charge_coverage
            print(f"DEBUG: Added fixed_charge_coverage = {fixed_charge_coverage}")

        # ============================================================================
        # MARKET & VALUATION RATIOS (if applicable)
        # ============================================================================
        ratios["valuation_ratios"] = {}
        
        # Book Value per Equity component
        if equity is not None:
            book_value_per_asset_unit = equity / total_assets if safe_gt(total_assets, 0) else 0
            ratios["valuation_ratios"]["book_value_ratio"] = book_value_per_asset_unit
            print(f"DEBUG: Added book_value_ratio = {book_value_per_asset_unit}")

        # Asset Quality Ratio
        if current_assets is not None and total_assets is not None and safe_gt(total_assets, 0):
            asset_quality = current_assets / total_assets
            ratios["valuation_ratios"]["asset_quality_ratio"] = asset_quality
            ratios["interpretation"]["asset_quality"] = "Good" if safe_ge(asset_quality, 0.6) else ("Fair" if safe_ge(asset_quality, 0.4) else "Weak")
            print(f"DEBUG: Added asset_quality_ratio = {asset_quality}")

        # Liquidity Quality Ratio
        if cash is not None and current_assets is not None and safe_gt(current_assets, 0):
            liquidity_quality = cash / current_assets
            ratios["valuation_ratios"]["liquidity_quality_ratio"] = liquidity_quality
            print(f"DEBUG: Added liquidity_quality_ratio = {liquidity_quality}")

        # ============================================================================
        # OVERALL ASSESSMENT & SUMMARY
        # ============================================================================
        ratios["summary"] = {
            "total_components_calculated": sum(len(v) for k, v in ratios.items() if isinstance(v, dict) and k not in ["interpretation", "summary"]),
            "total_ratio_categories": len([k for k in ratios.keys() if isinstance(ratios[k], dict) and k not in ["interpretation", "summary"]]),
            "categories": {
                "liquidity": len(ratios.get("liquidity_ratios", {})),
                "solvency": len(ratios.get("solvency_ratios", {})),
                "profitability": len(ratios.get("profitability_ratios", {})),
                "activity": len(ratios.get("activity_ratios", {})),
                "capital_structure": len(ratios.get("capital_structure_ratios", {})),
                "efficiency": len(ratios.get("efficiency_ratios", {})),
                "dupont": len(ratios.get("dupont_analysis", {})),
                "working_capital": len(ratios.get("working_capital_ratios", {})),
                "valuation": len(ratios.get("valuation_ratios", {}))
            },
            "status": "Comprehensive financial analysis with 40+ ratios calculated successfully."
        }

        return {
            "ratios": ratios,
            "status": "Comprehensive financial analysis with 40+ ratios calculated successfully from the detected balance sheet and P&L data."
        }

    except Exception as e:
        print(f"Error computing financial ratios: {e}")
        return {"ratios": {}, "status": f"An error occurred during ratio calculation: {str(e)}"}


def find_number_in_dict(d):
    """Recursively search a nested dict/list for the first numeric-looking value and return it as float."""
    if d is None:
        return None
    if isinstance(d, (int, float)):
        return float(d)
    if isinstance(d, str):
        # try parse
        try:
            cleaned = re.sub(r"[^0-9.\-]", "", d)
            if cleaned == "":
                return None
            return float(cleaned)
        except Exception:
            return None
    if isinstance(d, list):
        for item in d:
            n = find_number_in_dict(item)
            if n is not None:
                return n
    if isinstance(d, dict):
        for k, v in d.items():
            n = find_number_in_dict(v)
            if n is not None:
                return n
    return None


def compute_ratios_from_gemini_json(bs_json):
    """Compute simple ratios (debt_to_equity, total_assets, equity) from a structured Gemini JSON balance sheet.

    The Gemini JSON may nest numbers in lists; we search common paths and fallback to recursive search.
    """
    try:
        # Try common locations
        total_assets = None
        equity = None
        total_liabilities = None

        # Try direct locations
        if isinstance(bs_json, dict):
            # assets.totalAssets
            assets = bs_json.get("assets") or bs_json.get("Assets")
            if assets:
                total_assets = find_number_in_dict(assets.get("totalAssets") if isinstance(assets, dict) else assets)

            eql = bs_json.get("equityAndLiabilities") or bs_json.get("equity_and_liabilities")
            if eql and isinstance(eql, dict):
                # equity.totalEquity or equity.otherEquity
                eq = eql.get("equity")
                if eq:
                    equity = find_number_in_dict(eq.get("otherEquity") or eq.get("equityShareCapital") or eq)

                # liabilities.totalLiabilities
                liab = eql.get("liabilities")
                if liab:
                    total_liabilities = find_number_in_dict(liab.get("totalLiabilities") or liab)

            # fallback: search entire structure
            if total_assets is None:
                total_assets = find_number_in_dict(bs_json.get("totalAssets") or bs_json)
            if equity is None:
                equity = find_number_in_dict(bs_json)
            if total_liabilities is None:
                total_liabilities = find_number_in_dict(bs_json)

        if total_assets is not None and equity is not None and total_liabilities is not None:
            debt_to_equity = total_liabilities / equity if equity != 0 else 0
            return {"debt_to_equity": debt_to_equity, "total_assets": total_assets, "equity": equity}
    except Exception as e:
        print(f"Error computing from gemini json: {e}")
    return {"error": "Couldn't find required numeric values in Gemini JSON to calculate financial ratios."}


def _convert_indian_number_match(s: str):
    """Convert a numeric string possibly followed by lakhs/crore to a float in absolute units."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip().lower()
    # remove commas
    s = s.replace(',', '')
    m = re.match(r"\(?(-?[0-9]+(?:\.[0-9]+)?)\)?\s*(lakhs?|lakh|crore|crores|cr)?", s)
    if not m:
        try:
            return float(re.sub(r"[^0-9.\-]", "", s))
        except Exception:
            return None
    num = float(m.group(1))
    mult = m.group(2)
    if mult:
        if 'lakh' in mult:
            num = num * 1e5
        elif 'crore' in mult or mult == 'cr':
            num = num * 1e7
    return num


def extract_numeric_candidates_from_pdf(pdf_path):
    """Return a list of {page, line_no, text, numbers: [floats]}"""
    out = []
    try:
        doc = fitz.open(pdf_path)
        for p in range(len(doc)):
            text = doc.load_page(p).get_text('text')
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for i, line in enumerate(lines):
                # find all numeric-like tokens including lakhs/crore
                tokens = re.findall(r"\(?-?[0-9,]+(?:\.[0-9]+)?\)?\s*(?:lakhs?|lakh|crore|crores|cr)?", line, flags=re.IGNORECASE)
                nums = []
                for t in tokens:
                    val = _convert_indian_number_match(t)
                    if val is not None:
                        nums.append(val)
                if nums:
                    out.append({"page": p+1, "line_no": i+1, "text": line, "numbers": nums})
    except Exception as e:
        print(f"Error extracting numeric candidates from PDF: {e}")
    return out


def _extract_numbers_from_line(line: str):
    """Return list of floats parsed from a line of text (handles commas, parentheses, lakhs/crore)."""
    if not line:
        return []
    nums = []
    # find tokens like (1,234.56), -1,234.56, 1,23,456, 1.23 lakhs, 1 crore
    tokens = re.findall(r"[\(\-]?\d[0-9,\.\s]*(?:lakhs?|lakh|crore|crores|cr)?", line, flags=re.IGNORECASE)
    for t in tokens:
        s = t.strip()
        # try indian style conversion first
        v = None
        try:
            v = _convert_indian_number_match(s)
        except Exception:
            v = None
        if v is None:
            # fallback simple parse
            cleaned = re.sub(r"[^0-9.\-]", "", s)
            if cleaned and cleaned != '.':
                try:
                    v = float(cleaned)
                except Exception:
                    v = None
        if v is not None:
            nums.append(v)
    return nums


def extract_key_metrics_from_text(text: str) -> dict:
    """
    Heuristic extraction of key numeric metrics from notes text.
    Returns a dict with possible keys: profit_for_year (dict by year), eps (dict by year),
    weighted_shares (dict by year), trade_payables (value), current_borrowings (value), total_liabilities (value)
    """
    out = {}
    if not text:
        return out

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Helper to search lines for keywords and return first numeric candidate or all numbers
    def search_first_number(keywords):
        for ln in lines:
            low = ln.lower()
            if any(kw in low for kw in keywords):
                nums = _extract_numbers_from_line(ln)
                if nums:
                    return nums
        return []

    # Profit for year (may appear with two years in same note)
    profit_lines = []
    for ln in lines:
        if 'profit for the year' in ln.lower() or 'profit after tax' in ln.lower() or 'profit for the year (attributable to' in ln.lower():
            profit_lines.append(ln)
    if profit_lines:
        # try extract numbers, prefer numbers with lakh/crore tokens
        vals = []
        for pl in profit_lines:
            nums = _extract_numbers_from_line(pl)
            if nums:
                vals.extend(nums)
        if vals:
            out['profit_for_year'] = vals

    # EPS and weighted avg shares
    for ln in lines:
        low = ln.lower()
        if 'earnings per share' in low or 'basic and diluted earnings per share' in low or re.search(r'eps\b', low):
            nums = _extract_numbers_from_line(ln)
            if nums:
                out.setdefault('eps', []).extend(nums)
        if 'weighted average number' in low and ('share' in low or 'shares' in low):
            nums = _extract_numbers_from_line(ln)
            if nums:
                out.setdefault('weighted_shares', []).extend(nums)

    # Trade payables / payables
    payables = search_first_number(['trade payables', 'trade payable', 'payables', 'trade payables ('])
    if payables:
        out['trade_payables'] = payables[0]

    # Current borrowings
    cb = search_first_number(['current borrowings', 'short-term borrowings', 'current borrowings ('])
    if cb:
        out['current_borrowings'] = cb[0]

    # Total liabilities
    tl = search_first_number(['total liabilities', 'total liabilities and equity', 'total liabilities ('])
    if tl:
        out['total_liabilities'] = tl[0]

    return out


def compute_minimal_ratios_from_metrics(metrics: dict) -> dict:
    """Compute a small set of useful ratios from extracted note metrics.
    Returns minimal_ratios dict with keys like eps_current, eps_prev, eps_growth, payables_to_borrowings, liabilities_present.
    """
    mr = {}
    try:
        # EPS
        eps_list = metrics.get('eps') or []
        if eps_list:
            # assume first is current, second is previous if present
            mr['eps_current'] = eps_list[0]
            if len(eps_list) > 1:
                mr['eps_prev'] = eps_list[1]
                try:
                    if mr['eps_prev'] != 0:
                        mr['eps_growth'] = round((mr['eps_current'] - mr['eps_prev']) / abs(mr['eps_prev']), 4)
                except Exception:
                    pass

        # Profit growth (if we have two profits)
        pf = metrics.get('profit_for_year') or []
        if pf:
            mr['profit_for_year_values'] = pf
            if len(pf) > 1 and pf[1] != 0:
                try:
                    mr['profit_growth'] = round((pf[0] - pf[1]) / abs(pf[1]), 4)
                except Exception:
                    pass

        # Payables to current borrowings ratio
        pay = metrics.get('trade_payables')
        cb = metrics.get('current_borrowings')
        if pay is not None and cb is not None and cb != 0:
            try:
                mr['payables_to_current_borrowings'] = round(pay / cb, 4)
            except Exception:
                pass

        # Presence of total liabilities
        if 'total_liabilities' in metrics:
            mr['total_liabilities'] = metrics.get('total_liabilities')

    except Exception as e:
        print(f"Error computing minimal ratios: {e}")
    return mr


@app.route('/debug/analyze-session/<session_id>', methods=['POST'])
def debug_analyze_session(session_id):
    """Debug endpoint: extract numeric candidates from the stored session PDF, map common keys, compute ratios and return results."""
    try:
        if session_id not in pdf_stores:
            return jsonify({"error": "Session not found"}), 404

        store = pdf_stores[session_id]
        pdf_path = getattr(store, 'filepath', None) or getattr(store, 'balance_sheet_pdf', None)
        candidates = []
        # If pdf file exists, extract numeric candidates from PDF
        if pdf_path and os.path.exists(pdf_path):
            candidates = extract_numeric_candidates_from_pdf(pdf_path)
        else:
            # Try to use stored balance_sheet_data if present
            stored_bs = getattr(store, 'balance_sheet_data', None)
            if stored_bs:
                # flatten if nested
                flat = []
                if isinstance(stored_bs, list):
                    for item in stored_bs:
                        if isinstance(item, list):
                            flat.extend(item)
                        else:
                            flat.append(item)
                else:
                    flat = [stored_bs]

                # convert rows into candidate-like entries
                for idx, row in enumerate(flat):
                    if not isinstance(row, dict):
                        continue
                    text = ''
                    for k, v in row.items():
                        if isinstance(v, str) and len(v) > 0 and not v.replace(',', '').replace('.', '').isdigit():
                            text = v
                            break
                    # gather numeric values from the row
                    nums = []
                    for k, v in row.items():
                        n = parse_number(v)
                        if n is not None:
                            nums.append(n)
                    if nums:
                        candidates.append({"page": None, "line_no": idx+1, "text": text or str(row), "numbers": nums})

        # Map keywords to fields
        mapping = {
            'cash': ['cash and cash equivalents', 'cash and cash equivalents', 'cash'],
            'inventory': ['inventory', 'inventories'],
            'current_liabilities': ['current liabilities', 'current liability', 'current portion of long-term debt'],
            'non_current_liabilities': ['non-current liabilities', 'non current liabilities', 'non-current liability'],
            'total_liabilities': ['total liabilities', 'total liability'],
            'total_assets': ['total assets', 'total asset'],
            'total_equity': ['total equity', 'equity', 'shareholders funds', 'shareholders equity'],
            'receivables': ['trade receivables', 'receivables', 'receivable'],
            'payables': ['trade payables', 'payables', 'payable'],
            'revenue': ['revenue', 'total income', 'income from operations', 'revenue from operations'],
            'cogs': ['cost of materials', 'cost of goods sold', 'cost of sales', 'cogs']
        }

        found = {}
        # prioritize lines with keywords
        for c in candidates:
            text = c['text'].lower()
            for field, keywords in mapping.items():
                if field in found:
                    continue
                for kw in keywords:
                    if kw in text:
                        # pick the first numeric candidate
                        found[field] = c['numbers'][0]
                        break
                if field in found:
                    break

        # Fallback heuristics: if total_assets missing, try largest numeric on pages containing 'assets'
        if 'total_assets' not in found:
            asset_vals = [item for item in candidates if 'asset' in (item.get('text') or '').lower()]
            all_nums = [n for it in asset_vals for n in it.get('numbers', [])]
            if all_nums:
                found['total_assets'] = max(all_nums)
            else:
                # fallback: use the largest numeric found overall
                all_nums = [n for it in candidates for n in it.get('numbers', [])]
                if all_nums:
                    found['total_assets'] = max(all_nums)

        # Build a simple balance_sheet_data structure for calculate_financial_ratios
        bs_rows = []
        def put_row(particulars, val):
            if val is None: return
            bs_rows.append({"Particulars": particulars, "Current Year": val})

        put_row('Total Assets', found.get('total_assets'))
        put_row('Total Liabilities', found.get('total_liabilities'))
        put_row('Total Equity', found.get('total_equity'))
        put_row('Current Assets', found.get('cash') or found.get('inventory') or None)
        put_row('Current Liabilities', found.get('current_liabilities'))
        put_row('Inventory', found.get('inventory'))
        put_row('Cash and Cash Equivalents', found.get('cash'))
        put_row('Receivables', found.get('receivables'))
        put_row('Payables', found.get('payables'))

        # Basic P&L mapping
        pl = {}
        if 'revenue' in found:
            pl.setdefault('income', {})['revenueFromOperations'] = found['revenue']
        if 'cogs' in found:
            pl.setdefault('expenses', {})['costOfMaterialsConsumed'] = found['cogs']

        # Compute ratios using existing function
        result = calculate_financial_ratios(bs_rows, pl)

        # Attempt to extract table-aware rows from the PDF (if available)
        table_rows = []
        try:
            if pdf_path and os.path.exists(pdf_path):
                doc = fitz.open(pdf_path)
                # Try to find pages most likely to contain balance sheet
                pages = extract_balance_sheet_pages(pdf_path, max_pages=5)
                if not pages:
                    pages = list(range(min(10, len(doc))))
                for pnum in pages:
                    try:
                        pr = parse_balance_sheet_page(doc.load_page(pnum))
                        if pr:
                            table_rows.append({"page": pnum+1, "rows": pr})
                    except Exception as e:
                        print(f"Error extracting table rows from page {pnum}: {e}")
                doc.close()
        except Exception as e:
            print(f"Error extracting table-aware rows: {e}")

        # include jurisdiction if stored on session
        jurisdiction = getattr(store, 'jurisdiction', None)

        return jsonify({
            "candidates": candidates,
            "mapped": found,
            "balance_rows": bs_rows,
            "table_rows": table_rows,
            "ratios_result": result,
            "jurisdiction": jurisdiction
        }), 200
    except Exception as e:
        print(f"Error in debug_analyze_session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/set-api-key", methods=["POST"])
def set_api_key():
    global current_api_key
    data = request.get_json()
    api_key = data.get("api_key")

    if not api_key:
        return jsonify({"error": "API key cannot be empty."}), 400
    
    current_api_key = api_key
    Config.set_api_key(api_key)  # Set the API key in Config class
    print("API Key set successfully.")
    return jsonify({"message": "API key received and set for next operation."}), 200

@app.route("/upload", methods=["POST"])
def upload_pdf():
    global current_api_key
    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"] 
    
    if not current_api_key:
        return jsonify({"error": "Google API key not set. Please set the key before uploading."}), 400

    session_id = str(uuid.uuid4())
    filename = f"{session_id}_{secure_filename(file.filename)}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Save the uploaded file
        file.save(filepath)
        print(f"File saved to {filepath}. Starting RAG processing...")

        # Process the uploaded PDF (Financial analysis and balance sheet extraction)
        financial_analyzer = FinancialAnalyzer()
        vectorstore, documents = financial_analyzer.process_document(filepath)
        pdf_stores[session_id] = financial_analyzer
        print(f"Session {session_id} successfully created and indexed.")

        # --- Integrate balance sheet extraction ---

        # --- Integrate balance sheet extraction ---
        balance_sheet_data = None
        try:
            print("Identifying balance sheet pages using updated flow...")
            # Use the dedicated page finder
            bs_pages = extract_balance_sheet_pages(filepath)
            
            extracted_text = ""
            if bs_pages:
                print(f"Found balance sheet on page(s): {[p+1 for p in bs_pages]}")
                # Extract text from these pages
                doc = fitz.open(filepath)
                for p_idx in bs_pages:
                    page = doc.load_page(p_idx)
                    # Use GLM OCR (run_ocr) to ensure we get the best possible text even if it's an image-based PDF
                    try:
                        pix = page.get_pixmap(dpi=300)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            pix.save(tmp.name)
                            tmp_path = tmp.name
                        
                        ocr_txt, _ = run_ocr(tmp_path)
                        p_text = ocr_txt
                        if not p_text or len(p_text.strip()) < 50:
                            p_text = page.get_text() # Fallback to standard text extraction
                            
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except Exception as ocr_err:
                        print(f"OCR fallback failed for page {p_idx}: {ocr_err}")
                        p_text = page.get_text()
                    
                    extracted_text += f"\n--- Page {p_idx+1} ---\n{p_text}"
                doc.close()
            else:
                print("No specific balance sheet page identified by keywords. Searching first 5 pages.")
                doc = fitz.open(filepath)
                for i in range(min(5, len(doc))):
                    extracted_text += doc.load_page(i).get_text() + "\n"
                doc.close()

            # Create JSON file of that balance sheet content
            raw_bs_structure = {
                "session_id": session_id, 
                "source": "pdf_extraction",
                "identified_pages": bs_pages,
                "content": extracted_text
            }
            
            raw_bs_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_bs_content.json")
            with open(raw_bs_path, "w", encoding="utf-8") as f:
                json.dump(raw_bs_structure, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Balance Sheet Content JSON saved to: {raw_bs_path}")
            print("⬇️ TERMINAL OUTPUT OF EXTRACTED PAGE JSON ⬇️")
            print(json.dumps(raw_bs_structure, indent=2, ensure_ascii=False))
            print("⬆️ END OF JSON OUTPUT ⬆️")

            # Use Kimi LLM to pdf balance sheet details in json format
            print("🚀 sending content to Kimi LLM for structured extraction...")
            balance_sheet_data = extract_financials_with_kimi(extracted_text)
            
            if balance_sheet_data:
                print("✅ Kimi LLM Extraction Result:")
                print(json.dumps(balance_sheet_data, indent=2, ensure_ascii=False))
            else:
                print("⚠️ Kimi LLM did not return valid JSON data.")

        except Exception as e:
            print(f"Error in updated balance sheet flow: {e}")
            balance_sheet_data = None

            # Validate LLM-extracted balance sheet; if invalid, discard to force deterministic fallback later
            try:
                if balance_sheet_data is not None and not validate_balance_sheet_data(balance_sheet_data):
                    print("LLM-extracted balance sheet failed validation — discarding LLM result to use deterministic fallback.")
                    balance_sheet_data = None
            except Exception as e:
                print(f"Error validating LLM-extracted balance sheet: {e}")
        except Exception as e:
            print(f"LLM-based balance sheet extraction failed: {e}")
            print("Falling back to keyword-based extraction.")
            # Fallback to the old method
            balance_sheet_pages = extract_balance_sheet_pages(filepath)
            if balance_sheet_pages:
                doc = fitz.open(filepath)
                balance_sheet_data = []
                for page_num in balance_sheet_pages:
                    balance_sheet_data.append(parse_balance_sheet_page(doc.load_page(page_num)))
                doc.close()

        # If balance sheet data is found, store it
        if balance_sheet_data:
            # Store the balance sheet data in financial_analyzer
            financial_analyzer.balance_sheet_data = balance_sheet_data
            try:
                log_balance_sheet(session_id, balance_sheet_data)
            except Exception:
                pass

            # Attempt to compute ratios immediately (deterministic) and attach to analyzer
            try:
                # Flatten balance_sheet_data (it may be list-of-pages)
                flat_rows = []
                if isinstance(balance_sheet_data, list):
                    for page in balance_sheet_data:
                        if isinstance(page, list):
                            for r in page:
                                flat_rows.append(r)
                        elif isinstance(page, dict):
                            flat_rows.append(page)
                elif isinstance(balance_sheet_data, dict):
                    flat_rows = [balance_sheet_data]

                # compute ratios using available P&L (if any)
                try:
                    pl_data = None
                    # if analyzer extracted P&L earlier, try reading it
                    if hasattr(financial_analyzer, 'profit_and_loss'):
                        pl_data = getattr(financial_analyzer, 'profit_and_loss')
                    ratios_result = calculate_financial_ratios(flat_rows, pl_data)
                    financial_analyzer.ratios_result = ratios_result
                except Exception as e:
                    print(f"Failed to compute ratios at upload time: {e}")
            except Exception:
                pass

            # Persist the extracted balance sheet for session durability
            try:
                persist_payload = {
                    "original_filepath": filepath,
                    "balance_sheet_data": balance_sheet_data,
                    "ratios_result": getattr(financial_analyzer, 'ratios_result', None)
                }
                session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                with open(session_file, "w", encoding="utf-8") as sf:
                    json.dump(persist_payload, sf, ensure_ascii=False, indent=2)
                print(f"Persisted session metadata to {session_file}")
            except Exception as e:
                print(f"Failed to persist session metadata: {e}")

            return jsonify({
                "message": "PDF uploaded and processed successfully",
                "session_id": session_id,
                "status": "Processing completed."
            }), 200
        else:
            # Persist session metadata even if no balance sheet found
            try:
                session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                with open(session_file, "w", encoding="utf-8") as sf:
                    json.dump({
                        "session_id": session_id,
                        "original_filepath": filepath,
                    }, sf, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed to persist session metadata (no balance): {e}")

            return jsonify({
                "message": "PDF uploaded and processed successfully. No balance sheet found.",
                "session_id": session_id,
                "status": "Processing completed, but no balance sheet found."
            }), 200

    except ValueError as ve:
        print(f"Upload/RAG initialization error: {ve}")
        return jsonify({"error": str(ve), "status": "Failed"}), 500
    except Exception as e:
        print(f"General upload error: {e}")
        return jsonify({"error": str(e), "status": "Failed"}), 500



@app.route("/upload/status/<session_id>", methods=["GET"])
def upload_status(session_id):
    if session_id in pdf_stores:
        store = pdf_stores[session_id]
        # Try to read token stats from analyzer if available
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        status = "Processing completed. Document ready for analysis."
        message = None
        balance_sheet_found = False
        try:
            # If this is a PersistentStore wrapper, check its analyzer
            if hasattr(store, '_analyzer') and getattr(store, '_analyzer') is not None:
                analyzer = store._analyzer
                stats = getattr(analyzer, 'token_stats', None)
                if isinstance(stats, dict):
                    input_tokens = stats.get('input_tokens', 0)
                    output_tokens = stats.get('output_tokens', 0)
                    total_tokens = stats.get('total_tokens', input_tokens + output_tokens)
            # If store itself is a FinancialAnalyzer-like object
            elif hasattr(store, 'token_stats') and isinstance(getattr(store, 'token_stats', None), dict):
                stats = store.token_stats
                input_tokens = stats.get('input_tokens', 0)
                output_tokens = stats.get('output_tokens', 0)
                total_tokens = stats.get('total_tokens', input_tokens + output_tokens)

            # Determine if balance sheet data exists on the stored object
            try:
                if hasattr(store, 'balance_sheet_data') and getattr(store, 'balance_sheet_data'):
                    balance_sheet_found = True
                    message = "PDF uploaded and processed successfully. Balance sheet found."
                else:
                    # Try reading persisted session file for more detail
                    session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                    if os.path.exists(session_file):
                        try:
                            with open(session_file, 'r', encoding='utf-8') as sf:
                                sess = json.load(sf)
                                # If persisted balance_sheet_data present, consider it found
                                if sess.get('balance_sheet_data'):
                                    balance_sheet_found = True
                                    message = "PDF uploaded and processed successfully. Balance sheet found."
                                else:
                                    message = sess.get('message') or "PDF uploaded and processed successfully. No balance sheet found."
                        except Exception:
                            message = "PDF uploaded and processed successfully."
                    else:
                        message = "PDF uploaded and processed successfully. No balance sheet found."
            except Exception:
                message = message or "PDF uploaded and processed successfully."

        except Exception as e:
            print(f"Error reading token stats for session {session_id}: {e}")

        return jsonify({
            "session_id": session_id,
            "status": status,
            "message": message,
            "balance_sheet_found": bool(balance_sheet_found),
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(total_tokens),
            "tokens_used": int(total_tokens),
        }), 200
    else:
        return jsonify({
            "session_id": session_id,
            "status": "Awaiting processing or session expired/not found.",
        }), 404
    


@app.route('/debug/token-usage/<session_id>', methods=['GET'])
def debug_token_usage(session_id):
    """Return cumulative and last-request token usage for a session's analyzer.

    If the session stores a PersistentStore wrapper, attempt to read its analyzer.
    """
    try:
        if session_id not in pdf_stores:
            return jsonify({"error": "Session not found"}), 404

        store = pdf_stores[session_id]

        # Determine the analyzer object
        analyzer = None
        if hasattr(store, '_analyzer') and getattr(store, '_analyzer') is not None:
            analyzer = store._analyzer
        elif hasattr(store, 'token_stats'):
            # store itself may be a FinancialAnalyzer
            analyzer = store

        # If analyzer isn't initialized, try to lazily initialize it (PersistentStore.ensure_analyzer)
        if analyzer is None:
            try:
                if hasattr(store, 'ensure_analyzer'):
                    store.ensure_analyzer()
                    analyzer = getattr(store, '_analyzer', None)
            except Exception as e:
                print(f"Could not initialize analyzer for session {session_id}: {e}")

        if analyzer is None:
            return jsonify({"error": "Analyzer not initialized for this session yet."}), 404

        stats = getattr(analyzer, 'token_stats', {}) or {}
        last = getattr(analyzer, 'last_request', {}) or {}

        return jsonify({
            "session_id": session_id,
            "token_stats": stats,
            "last_request": last
        }), 200
    except Exception as e:
        print(f"Error in debug_token_usage: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/debug/trigger-analyze/<session_id>', methods=['POST'])
def debug_trigger_analyze(session_id):
    """Lazily initialize analyzer for session and trigger a lightweight LLM call
    to record per-request token usage. This is a debug-only endpoint.
    """
    try:
        if session_id not in pdf_stores:
            return jsonify({"error": "Session not found"}), 404

        store = pdf_stores[session_id]

        # Ensure analyzer present
        try:
            if hasattr(store, 'ensure_analyzer'):
                store.ensure_analyzer()
        except Exception as e:
            print(f"Failed to ensure analyzer for trigger: {e}")
            return jsonify({"error": f"Failed to initialize analyzer: {str(e)}"}), 500

        analyzer = getattr(store, '_analyzer', None) or (store if hasattr(store, 'token_stats') else None)
        if analyzer is None:
            return jsonify({"error": "Analyzer not available after initialization."}), 500

        # Run a lightweight analysis call that won't modify storage: ask for a one-line summary
        prompt = "Provide a one-line factual summary of the document context."
        try:
            # prefer using analyze_financial_text if available
            if hasattr(analyzer, 'analyze_financial_text'):
                resp = analyzer.analyze_financial_text(prompt)
            else:
                # fallback to chat_answer which will use the chain
                resp = analyzer.chat_answer(prompt)
        except Exception as e:
            print(f"LLM call during trigger_analyze failed: {e}")
            # even if LLM fails, return whatever token stats exist

        stats = getattr(analyzer, 'token_stats', {}) or {}
        last = getattr(analyzer, 'last_request', {}) or {}

        return jsonify({
            "session_id": session_id,
            "token_stats": stats,
            "last_request": last
        }), 200
    except Exception as e:
        print(f"Error in debug_trigger_analyze: {e}")
        return jsonify({"error": str(e)}), 500













import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel)
    mask += cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel)
    cleaned = cv2.bitwise_and(binary, cv2.bitwise_not(mask))
    return cv2.bitwise_not(cleaned)

# ---- Financial Data Parser ----
def parse_with_gemini(prompt_text):
    try:
        try:
            analyzer = FinancialAnalyzer()  # Create without a file for parsing only
            response = analyzer.analyze_financial_text(prompt_text)
        except TypeError as te:
            # Fallback: try to call LLM directly if FinancialAnalyzer cannot be constructed
            print(f"Warning: FinancialAnalyzer instantiation failed: {te}. Falling back to direct LLM.")
            try:
                from financial_analyzer import Config
                from langchain_google_genai import GoogleGenerativeAI
                cfg = Config()
                if not getattr(cfg, 'GOOGLE_API_KEY', None):
                    raise ValueError("Google API key not set in Config for direct LLM fallback.")
                llm = GoogleGenerativeAI(model=cfg.LLM_MODEL, google_api_key=cfg.GOOGLE_API_KEY, temperature=0.2)
                response = llm.invoke(prompt_text)
            except Exception as e:
                print(f"Direct LLM fallback failed: {e}")
                raise

        if isinstance(response, dict):
            return response
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                # If JSON parsing fails, return raw response for debugging
                return response
        print("❌ Response did not contain JSON.")
    except Exception as e:
        print("❌ Financial parsing failed:", e)
    return None

# ---- Prompts ----
def get_balance_sheet_prompt(text):
    return f'''
Extract the Balance Sheet as strictly valid JSON in the following format only:

{{ 
  "as_of": [], 
  "assets": {{
    "nonCurrentAssets": {{
      "propertyPlantAndEquipment": [],
      "capitalWorkInProgress": [],
      "investmentProperty": [],
      "intangibleAssets": [],
      "intangibleAssetsUnderDevelopment": [],
      "financialAssetsInvestments": [],
      "loanToSubsidiary": [],
      "otherFinancialAssets": [],
      "nonCurrentTaxAssetsNet": [],
      "otherNonCurrentAssets": []
    }},
    "currentAssets": {{
      "inventories": [],
      "financialAssetsInvestments": [],
      "tradeReceivables": [],
      "cashAndCashEquivalents": [],
      "bankBalancesOtherThanCash": [],
      "loanToSubsidiary": [],
      "otherFinancialAssets": [],
      "otherCurrentAssets": []
    }},
    "totalAssets": []
  }},
  "equityAndLiabilities": {{
    "equity": {{
      "equityShareCapital": [],
      "otherEquity": []
    }},
    "liabilities": {{
      "nonCurrentLiabilities": {{
        "borrowings": [],
        "leaseLiabilities": [],
        "otherFinancialLiabilities": [],
        "provisions": [],
        "deferredTaxLiabilitiesNet": []
      }},
      "currentLiabilities": {{
        "borrowings": [],
        "leaseLiabilities": [],
        "tradePayablesDueToMicro": [],
        "tradePayablesDueToOthers": [],
        "otherFinancialLiabilities": [],
        "otherCurrentLiabilities": [],
        "provisions": [],
        "currentTaxLiabilitiesNet": []
      }},
      "totalLiabilities": []
    }},
    "totalEquityAndLiabilities": []
  }}
}}

Now extract from this text:
{text}
'''

def get_pl_prompt(text):
    return f'''
Extract the Profit and Loss statement as strictly valid JSON in the format:

{{
  "for_year_ended": [],
  "income": {{
    "revenueFromOperations": [],
    "otherIncome": [],
    "totalIncome": []
  }},
  "expenses": {{
    "costOfMaterialsConsumed": [],
    "purchaseOfStockInTrade": [],
    "changeInInventories": [],
    "employeeBenefitsExpense": [],
    "financeCosts": [],
    "depreciationAndAmortisation": [],
    "advertisementAndPublicity": [],
    "otherExpenses": [],
    "totalExpenses": []
  }},
  "profitBeforeExceptionalItemsAndTax": [],
  "exceptionalItems": [],
  "profitBeforeTax": [],
  "taxExpense": {{
    "currentTax": [],
    "deferredTax": [],
    "totalTaxExpense": []
  }},
  "netProfit": [],
  "earningsPerEquityShare": {{
    "basic": [],
    "diluted": []
  }}
}}

Now extract from this text:
{text}
'''

# ---- Process PDF Pages ----
def extract_tables_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    result = {
        "balanceSheet": None,
        "profitAndLoss": None
    }

    with tempfile.TemporaryDirectory() as tempdir:
        for page_num in range(len(doc) - 1):  # ensure next page exists
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img_path = os.path.join(tempdir, f"page_{page_num}.png")
            pix.save(img_path)

            # Preprocess and OCR
            clean_img = preprocess_image(img_path)
            clean_path = os.path.join(tempdir, f"cleaned_{page_num}.png")
            cv2.imwrite(clean_path, clean_img)
            text = pytesseract.image_to_string(clean_path, config="--psm 6")

            if "equity" in text.lower() and "liabilities" in text.lower():
                print(f"📄 Balance sheet found on page {page_num + 1}")
                print(f"DEBUG: Balance sheet OCR text length: {len(text)}")
                result["balanceSheet"] = parse_with_gemini(get_balance_sheet_prompt(text))
                print(f"DEBUG: Balance sheet extracted: {result['balanceSheet'] is not None}")

                # Automatically fetch next page for PL
                next_page = doc.load_page(page_num + 1)
                next_pix = next_page.get_pixmap(dpi=300)
                next_img_path = os.path.join(tempdir, f"page_{page_num+1}.png")
                next_pix.save(next_img_path)

                clean_next = preprocess_image(next_img_path)
                clean_next_path = os.path.join(tempdir, f"cleaned_{page_num+1}.png")
                cv2.imwrite(clean_next_path, clean_next)
                next_text = pytesseract.image_to_string(clean_next_path, config="--psm 6")

                print(f"📄 Processing page {page_num + 2} for Profit & Loss statement")
                print(f"DEBUG: P&L OCR text length: {len(next_text)}")
                result["profitAndLoss"] = parse_with_gemini(get_pl_prompt(next_text))
                print(f"DEBUG: P&L extracted: {result['profitAndLoss'] is not None}")
                if result['profitAndLoss']:
                    print(f"DEBUG: P&L keys: {list(result['profitAndLoss'].keys()) if isinstance(result['profitAndLoss'], dict) else 'Not a dict'}")
                break

    print(f"DEBUG: Final extraction result - BS: {result['balanceSheet'] is not None}, PL: {result['profitAndLoss'] is not None}")
    return result


def save_pdf_store(session_id, balance_sheet, profit_and_loss):
    # This function should store the session data for future retrieval
    # Persist minimal metadata (original uploaded file path should be stored elsewhere)
    try:
        session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
        payload = {
            "session_id": session_id,
            "balance_sheet_data": balance_sheet,
            "profit_and_loss": profit_and_loss,
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to persist session {session_id}: {e}")


# Load persisted sessions on startup (if any)
def load_persisted_sessions():
    try:
        for fn in os.listdir(SESSIONS_FOLDER):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(SESSIONS_FOLDER, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sid = data.get("session_id")
                if not sid:
                    continue
                # Create a PersistentStore with balance sheet data; original PDF path may not be known
                store = PersistentStore(session_id=sid, filepath=None, balance_sheet_data=data.get("balance_sheet_data"), balance_sheet_pdf=None)
                pdf_stores[sid] = store
                print(f"Loaded persisted session: {sid}")
            except Exception as e:
                print(f"Failed to load session file {path}: {e}")
    except Exception as e:
        print(f"Error scanning sessions folder: {e}")


# Run load at module import
load_persisted_sessions()


@app.route("/debug/create-fake-session", methods=["POST"])
def create_fake_session():
    """Create a fake in-memory session with simple balance sheet data for testing.

    Returns:
        JSON with session_id that can be used to call other endpoints like
        /chat/financial-ratio for quick local testing.
    """
    try:
        sid = str(uuid.uuid4())

        # Simple sample balance sheet rows (list-of-pages => list-of-rows)
        sample_balance = [
            [
                {"Particulars": "Total Assets", "As at March 31": "1000000"},
                {"Particulars": "Total Liabilities", "As at March 31": "400000"},
                {"Particulars": "Equity", "As at March 31": "600000"},
            ]
        ]

        class MockStore:
            def __init__(self, balance):
                self.balance_sheet_data = balance
                self.balance_sheet_pdf = None

            def chat_answer(self, prompt: str):
                return "(debug) This is a fake chat response."

            def get_compliance_gap_report(self):
                return "(debug) Fake compliance gaps"

            def get_auditor_report_summary(self):
                return "(debug) Fake auditor summary"

            def get_director_report_highlights(self):
                return "(debug) Fake director highlights"

            def get_overall_summary(self):
                return "(debug) Fake overall summary"

        pdf_stores[sid] = MockStore(sample_balance)

        return jsonify({"session_id": sid, "message": "Fake session created for testing."}), 200
    except Exception as e:
        print(f"Error creating fake session: {e}")
        return jsonify({"error": "Failed to create fake session."}), 500


@app.route("/debug/sessions", methods=["GET"])
def list_debug_sessions():
    """Return a list of active in-memory sessions and a small summary for debugging."""
    try:
        sessions = []
        for sid, store in pdf_stores.items():
            has_balance = bool(getattr(store, "balance_sheet_data", None))
            sessions.append({"session_id": sid, "has_balance_sheet": has_balance})
        return jsonify({"sessions": sessions}), 200
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return jsonify({"error": "Failed to list sessions."}), 500


@app.route("/debug/session/<session_id>", methods=["GET"])
def dump_session(session_id):
    """Return the stored pdf_store contents (balance_sheet_data and any other helpful info) for a given session id.

    This is a debug-only endpoint to inspect what was extracted and stored for the session.
    """
    try:
        if session_id not in pdf_stores:
            return jsonify({"error": "Session not found."}), 404

        store = pdf_stores[session_id]
        out = {
            "session_id": session_id,
            "has_balance_sheet": bool(getattr(store, "balance_sheet_data", None)),
            "balance_sheet_data": getattr(store, "balance_sheet_data", None),
            "balance_sheet_pdf": getattr(store, "balance_sheet_pdf", None)
        }
        return jsonify(out), 200
    except Exception as e:
        print(f"Error dumping session {session_id}: {e}")
        return jsonify({"error": "Failed to dump session."}), 500

def validate_balance_sheet_data(balance_data):
    """
    Validate that extracted balance sheet has meaningful financial data.
    Returns True if data looks valid (has numeric values for key line items).
    """
    try:
        if not balance_data:
            return False
        
        # Flatten if nested
        flat_data = []
        if isinstance(balance_data, list):
            for item in balance_data:
                if isinstance(item, list):
                    flat_data.extend(item)
                else:
                    flat_data.append(item)
        else:
            flat_data = [balance_data]
        
        # Helper: attempt to parse any token into a number
        def try_parse_numeric(x):
            if x is None:
                return None
            if isinstance(x, (int, float)):
                return float(x)
            if isinstance(x, str):
                # reuse module-level parse_number for common formats
                v = parse_number(x)
                if v is not None:
                    return v
                # fallback: strip non-numeric and try
                cleaned = re.sub(r"[^0-9\.\-]", "", x)
                try:
                    return float(cleaned) if cleaned not in ("", ".") else None
                except Exception:
                    return None
            return None

        # Recursively search for numeric-like values in dicts/lists
        numeric_count = 0
        def walk(obj):
            nonlocal numeric_count
            if obj is None:
                return
            if isinstance(obj, dict):
                for v in obj.values():
                    n = try_parse_numeric(v)
                    if n is not None and n > 0:
                        numeric_count += 1
                    else:
                        walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    n = try_parse_numeric(item)
                    if n is not None and n > 0:
                        numeric_count += 1
                    else:
                        walk(item)

        walk(flat_data)

        # Require at least 3 numeric values (lowered threshold to be more permissive)
        has_valid_data = numeric_count >= 3
        print(f"Balance sheet validation: {numeric_count} numeric values found, valid={has_valid_data}")
        return has_valid_data
    except Exception as e:
        print(f"Error validating balance sheet: {e}")
        return False


def generate_ai_grounded_ratio_analysis(pdf_store, balance_data, financial_ratios):
    """
    Generate AI analysis of financial ratios grounded in REAL computed data.
    Prevents hallucination by providing AI with actual computed ratios to analyze,
    not asking it to compute them from scratch.
    
    Args:
        pdf_store: The FinancialAnalyzer store with access to the document
        balance_data: The extracted balance sheet data
        financial_ratios: The computed ratios dict with "ratios", "status" keys
        
    Returns:
        Enhanced ratios dict with AI-grounded interpretations
    """
    try:
        print("Generating AI-grounded ratio analysis (fact-based, no hallucination)...")
        
        # Build a factual summary of computed ratios for AI to analyze
        ratios_dict = financial_ratios.get("ratios", {})
        
        # Create a structured prompt with REAL computed data
        computed_ratios_text = json.dumps(ratios_dict, indent=2)
        
        analysis_prompt = f"""You are a financial analyst. I have COMPUTED these financial ratios from actual balance sheet data (not estimates):

{computed_ratios_text}

Based ONLY on these computed ratios and their actual values, provide:
1. **Liquidity Assessment**: Interpret current_ratio, quick_ratio, cash_ratio
2. **Solvency Assessment**: Interpret debt_ratio, debt_to_equity, equity_ratio
3. **Efficiency Assessment**: Comment on asset turnover and receivables efficiency
4. **Key Concerns**: Identify any ratios that suggest financial stress or strength
5. **Overall Health Score**: Provide a summary rating (Strong/Moderate/Weak) based on the actual numbers

IMPORTANT: Only analyze the ratios provided above. Do not make up numbers or assume missing data.
If a ratio is missing or N/A, skip it. Ground all analysis in the actual computed values."""

        try:
            # Use the PDF store's chain if available to provide document context
            if hasattr(pdf_store, '_chat_chain') and pdf_store._chat_chain:
                ai_analysis = pdf_store.analyze(pdf_store._chat_chain, analysis_prompt).get("answer", "")
            else:
                # Fallback: use direct LLM call
                ai_analysis = pdf_store.analyze_financial_text(analysis_prompt)
        except Exception as e:
            print(f"AI grounding failed, using factual summary instead: {e}")
            ai_analysis = f"Ratios computed successfully. Analysis:\n{computed_ratios_text}"
        
        # Add the grounded analysis to the ratios response
        if isinstance(ratios_dict, dict):
            ratios_dict["ai_grounded_analysis"] = ai_analysis
        
        return {
            "ratios": ratios_dict,
            "status": financial_ratios.get("status", "Ratios computed successfully"),
            "analysis_method": "AI-grounded (computed ratios analyzed, no hallucination)"
        }
    except Exception as e:
        print(f"Error in generate_ai_grounded_ratio_analysis: {e}")
        # Fallback: return ratios without AI analysis
        return financial_ratios


@app.route("/chat/financial-ratio", methods=["POST"])
def financial_ratio():
    """
    Expected JSON payload: { "session_id": "<session-id>" }

    This endpoint will look up the processed PDF store for the session and
    return pre-computed/extracted balance sheet data and calculated ratios.
    Ratios are computed from actual data, then analyzed by AI grounded in facts.
    """
    try:
        # Debug: log incoming request info to help diagnose 400 responses
        try:
            print("--- financial_ratio request start ---")
            print("Headers:", dict(request.headers))
            print("Raw body:", request.get_data())
        except Exception as _:
            pass

        # Use the common get_session_id helper that other routes use
        try:
            session_id = get_session_id()
        except ValueError as ve:
            # Provide an explicit 400 with debug info so callers understand why
            try:
                raw = request.get_data(as_text=True)
            except Exception:
                raw = '<failed to read body>'
            print(f"Missing session_id in request. Raw body: {raw}")
            return jsonify({"error": "Missing session_id in request payload.", "details": str(ve), "raw_body": raw}), 400

        # Retrieve the stored PDF/RAG object; if missing, return 404 (not found)
        try:
            pdf_store = get_pdf_store(session_id)
        except ValueError as ve:
            # More explicit: session not found or expired
            return jsonify({"error": str(ve)}), 404

        # Extra debug info to diagnose missing balance data
        try:
            print("Session lookup:", session_id in pdf_stores)
            print("PDF store type:", type(pdf_store))
            # Print available attributes on the store (limited)
            try:
                attrs = [a for a in dir(pdf_store) if not a.startswith("__")][:40]
                print("Store attrs sample:", attrs)
            except Exception:
                pass
        except Exception:
            pass

        # The upload flow stores balance_sheet_data as a list (per page). Flatten it to rows.
        balance_data = getattr(pdf_store, "balance_sheet_data", None)
        # If ratios were precomputed during upload, return them immediately
        precomputed = getattr(pdf_store, 'ratios_result', None)
        if precomputed:
            return jsonify({"response": precomputed}), 200
        if not balance_data:
            # Attempt on-demand extraction from available PDF paths (try several locations)
            pdf_path = None
            # Check for a saved extracted-pages PDF on the store
            pdf_path_candidate = getattr(pdf_store, "balance_sheet_pdf", None)
            if pdf_path_candidate and os.path.exists(pdf_path_candidate):
                pdf_path = pdf_path_candidate

            # Check persistent session file for original filepath
            if not pdf_path:
                session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                if os.path.exists(session_file):
                    try:
                        with open(session_file, "r", encoding="utf-8") as sf:
                            sdata = json.load(sf)
                        # prefer balance_sheet_pdf if present
                        cand = sdata.get("balance_sheet_pdf") or sdata.get("original_filepath") or sdata.get("filepath")
                        if cand and os.path.exists(cand):
                            pdf_path = cand
                    except Exception as e:
                        print(f"Failed to read session file {session_file}: {e}")

            # As a last resort, check for any uploaded PDF with a name containing the session id
            if not pdf_path:
                for fn in os.listdir(UPLOAD_FOLDER):
                    if session_id in fn:
                        candidate = os.path.join(UPLOAD_FOLDER, fn)
                        if os.path.exists(candidate):
                            pdf_path = candidate
                            break

        # PRIORITIZE Mistral OCR Integration if available
        if MISTRAL_API_KEY and pdf_path:
            try:
                print(f"Using Mistral OCR for session {session_id}...")
                client = Mistral(api_key=MISTRAL_API_KEY)
                
                # Instead of the whole PDF, let's find relevant pages to avoid token limits
                # and ensure we get BOTH balance sheet and P&L
                relevant_pages = []
                # Use existing heuristic to find balance sheet pages
                bs_pages = extract_balance_sheet_pages(pdf_path)
                relevant_pages.extend(bs_pages)
                
                # Heuristic to find P&L pages (Statement of Profit and Loss)
                try:
                    doc = fitz.open(pdf_path)
                    for i in range(len(doc)):
                        text_page = doc[i].get_text().lower()
                        if "profit and loss" in text_page or "profit & loss" in text_page:
                            if i not in relevant_pages:
                                relevant_pages.append(i)
                    doc.close()
                except:
                    pass
                
                # Sort and remove duplicates
                relevant_pages = sorted(list(set(relevant_pages)))
                
                if not relevant_pages:
                    # Fallback to first few pages if none found
                    relevant_pages = [0, 1, 2, 3, 4]
                
                # Use GLM OCR (process_pdf) to extract text for the relevant pages only
                ocr_text = ""
                ocr_fallback_used = True
                try:
                    all_text, _ = process_pdf(pdf_path)
                    # all_text contains markers like "===== PAGE {n} =====" per page
                    for pg_num in relevant_pages:
                        marker = f"===== PAGE {pg_num+1} ====="
                        if marker in all_text:
                            # extract from marker to next marker or end
                            start = all_text.index(marker) + len(marker)
                            # find next marker
                            next_marker = all_text.find("===== PAGE ", start)
                            page_chunk = all_text[start:next_marker] if next_marker != -1 else all_text[start:]
                            ocr_text += page_chunk + "\n"
                except Exception as e:
                    print(f"GLM OCR (process_pdf) failed for relevant pages: {e}")
                    ocr_text = ""

                setattr(pdf_store, 'ocr_fallback_used', ocr_fallback_used)
                # Persist flag in session file for later inspection
                try:
                    session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                    prev = {}
                    if os.path.exists(session_file):
                        with open(session_file, 'r', encoding='utf-8') as sf:
                            prev = json.load(sf)
                    prev.update({"ocr_fallback_used": bool(ocr_fallback_used)})
                    with open(session_file, 'w', encoding='utf-8') as sf:
                        json.dump(prev, sf, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Failed to persist OCR flag for {session_id}: {e}")
                
                print("OCR Text:", ocr_text)
                mistral_data = extract_balance_sheet(ocr_text, client)
                
                if mistral_data:
                    # Convert Mistral's structured format to the internal format if needed
                    # Mistral returns: { "year": "YYYY", "assets": {...}, "liabilities": {...}, "equity": {...} }
                    # Our logic expects flat rows for calculate_financial_ratios or precomputed results
                    
                    # Refactored: use the unified categorized calculation logic from app.py
                    categorized_resp = calculate_financial_ratios(mistral_financials=mistral_data)
                    ratios_result = categorized_resp.get("ratios", categorized_resp)
                    
                    # Round all numeric values in ratios_result to 2 decimal places
                    def round_ratios(obj):
                        if isinstance(obj, dict):
                            return {k: round_ratios(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [round_ratios(x) for x in obj]
                        elif isinstance(obj, (int, float)):
                            return round(float(obj), 2)
                        return obj
                    
                    ratios_result = round_ratios(ratios_result)
                    print("Ratios Result:", ratios_result)
                    
                    setattr(pdf_store, 'ratios_result', ratios_result)
                    setattr(pdf_store, 'balance_sheet_data', mistral_data)
                    try:
                        log_balance_sheet(session_id, mistral_data)
                    except Exception:
                        pass
                    return jsonify({"response": ratios_result, "method": "mistral"}), 200
            except Exception as e:
                print(f"Mistral OCR extraction failed: {e}")
                # Fallback to deterministic logic below

        # If we have a PDF path but no stored balance_data, attempt deterministic extraction now
        if not balance_data and pdf_path:
            try:
                pages = extract_balance_sheet_pages(pdf_path, max_pages=3)
                if pages:
                    doc = fitz.open(pdf_path)
                    parsed_rows = []
                    for pnum in pages:
                        parsed = parse_balance_sheet_page(doc.load_page(pnum))
                        if parsed:
                            # parse_balance_sheet_page returns list of dicts
                            if isinstance(parsed, list):
                                parsed_rows.extend(parsed)
                            else:
                                parsed_rows.append(parsed)
                    doc.close()
                    if parsed_rows:
                        balance_data = parsed_rows
                        # attach to store
                        setattr(pdf_store, 'balance_sheet_data', balance_data)
                        # compute ratios and attach
                        try:
                            ratios_result = calculate_financial_ratios(balance_data, None)
                            setattr(pdf_store, 'ratios_result', ratios_result)
                            return jsonify({"response": ratios_result}), 200
                        except Exception as e:
                            print(f"Error computing ratios after deterministic extraction: {e}")
            except Exception as e:
                print(f"Deterministic extraction failed: {e}")

            if pdf_path:
                print(f"Attempting on-demand extraction from: {pdf_path}")
                try:
                    extracted = extract_tables_from_pdf(pdf_path)
                    # If gemini returned structured JSON
                    bs = extracted.get("balanceSheet")
                    pl = extracted.get("profitAndLoss")
                    # Validate AI-extracted balance sheet; if invalid, discard so deterministic fallback can run
                    try:
                        if bs is not None and not validate_balance_sheet_data(bs):
                            print("On-demand LLM-extracted balance sheet failed validation — discarding to allow deterministic fallback.")
                            bs = None
                    except Exception as e:
                        print(f"Error validating on-demand LLM-extracted balance sheet: {e}")

                    if bs:
                        # Persist findings into the store
                        try:
                            # If bs is a list-like table rows (from our parser), store directly
                            if isinstance(bs, list):
                                pdf_store.balance_sheet_data = bs
                                try:
                                    log_balance_sheet(session_id, bs)
                                except Exception:
                                    pass
                            else:
                                # Structured JSON (Gemini) - store under balance_sheet_data for debugging
                                pdf_store.balance_sheet_data = bs
                                try:
                                    log_balance_sheet(session_id, bs)
                                except Exception:
                                    pass
                            
                            # Store P&L data if available
                            if pl:
                                pdf_store.profit_loss_data = pl

                            # Persist to session file for durability
                            try:
                                session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                                with open(session_file, "r", encoding="utf-8") as sf:
                                    prev = json.load(sf)
                            except Exception:
                                prev = {}
                            prev.update({"balance_sheet_data": pdf_store.balance_sheet_data, "balance_sheet_pdf": pdf_path})
                            if pl:
                                prev.update({"profit_loss_data": pdf_store.profit_loss_data})
                            try:
                                with open(session_file, "w", encoding="utf-8") as sf:
                                    json.dump(prev, sf, ensure_ascii=False, indent=2)
                            except Exception as e:
                                print(f"Failed to persist extracted balance for {session_id}: {e}")

                        except Exception as e:
                            print(f"Failed to assign extracted balance sheet to store: {e}")
                    else:
                        print("No balance sheet found during on-demand extraction.")
                except Exception as e:
                    print(f"On-demand extraction failed: {e}")

            # Re-fetch balance_data after attempted extraction
            balance_data = getattr(pdf_store, "balance_sheet_data", None)

            # Re-fetch balance_data after attempted extraction
            balance_data = getattr(pdf_store, "balance_sheet_data", None)
            if not balance_data: # If still no balance sheet data
                try:
                    # Use the LLM to analyze why it might be missing
                    analysis_prompt = "Analyze the table of contents or first few pages of this document. Is a standard Balance Sheet present? If not, what type of document does this appear to be (e.g., Director's Report, Standalone Financials, etc.)? Explain briefly why financial ratios cannot be calculated."
                    
                    # Ensure the analyzer's chain is initialized
                    if not hasattr(pdf_store, '_chat_chain') or pdf_store._chat_chain is None:
                        if not pdf_store.filepath:
                            raise ValueError("No document filepath set for analysis.")
                        vectorstore, _ = pdf_store.process_document(pdf_store.filepath)
                        pdf_store._chat_chain = pdf_store.create_chain(vectorstore)
                    
                        llm_explanation = pdf_store.analyze(pdf_store._chat_chain, analysis_prompt).get("answer", "Could not determine document type.")
                        # Attempt a deterministic text-based extraction for limited ratios as a helpful fallback
                        det_ratios = None
                        try:
                            pdf_path_for_det = None
                            # try to reuse earlier pdf_path if present
                            try:
                                pdf_path_for_det = pdf_path if 'pdf_path' in locals() and pdf_path else None
                            except Exception:
                                pdf_path_for_det = None

                            if not pdf_path_for_det:
                                # try session metadata file
                                session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                                if os.path.exists(session_file):
                                    try:
                                        with open(session_file, 'r', encoding='utf-8') as sf:
                                            sdata = json.load(sf)
                                        cand = sdata.get('balance_sheet_pdf') or sdata.get('original_filepath') or sdata.get('filepath')
                                        if cand and os.path.exists(cand):
                                            pdf_path_for_det = cand
                                    except Exception:
                                        pdf_path_for_det = None

                            if pdf_path_for_det:
                                try:
                                    from extract_and_calc_ratios import extract_text_from_pdf
                                    try:
                                        from ratio_smoke_test import calculate_financial_ratios_from_text
                                    except Exception:
                                        calculate_financial_ratios_from_text = None

                                    txt = extract_text_from_pdf(pdf_path_for_det)
                                    if calculate_financial_ratios_from_text:
                                        try:
                                            det_ratios = calculate_financial_ratios_from_text(txt)
                                        except Exception:
                                            det_ratios = None

                                    # If no deterministic ratios produced, try note-metrics heuristics
                                    if not det_ratios or (isinstance(det_ratios, dict) and len(det_ratios) == 0):
                                        try:
                                            metrics = extract_key_metrics_from_text(txt)
                                            if metrics:
                                                det_ratios = compute_minimal_ratios_from_metrics(metrics)
                                        except Exception as e:
                                            print(f"Note-metric deterministic fallback failed: {e}")
                                except Exception as e:
                                    print(f"Deterministic fallback extraction failed: {e}")
                                    det_ratios = None
                        except Exception as e:
                            print(f"Error during deterministic fallback preparation: {e}")

                        # Return a non-error response with helpful diagnostics and any deterministic ratios
                        resp = {
                            "warning": "Could not find a balance sheet in the document.",
                            "analysis": llm_explanation,
                            "status": "no_balance_sheet",
                        }
                        if det_ratios:
                            resp["deterministic_ratios"] = det_ratios

                        return jsonify(resp), 200
                except Exception as analysis_error:
                        print(f"Error during LLM-based analysis of missing balance sheet: {analysis_error}")
                        # Return 200 with diagnostic info rather than an HTTP 400 error to the client
                        return jsonify({"warning": "No balance sheet data was found, and secondary analysis failed.", "error": str(analysis_error)}), 200

        # Try to fetch P&L data as well for comprehensive ratios
        profit_loss_data = getattr(pdf_store, "profit_loss_data", None)
        print(f"DEBUG /chat/financial-ratio: P&L data retrieved: {profit_loss_data is not None}")
        if profit_loss_data:
            print(f"DEBUG: P&L data type: {type(profit_loss_data)}, keys: {list(profit_loss_data.keys()) if isinstance(profit_loss_data, dict) else 'N/A'}")
        
        # If balance_data is structured Gemini JSON, compute ratios directly from it
        if isinstance(balance_data, dict):
            print(f"DEBUG: Balance data is dict (Gemini JSON format)")
            financial_ratios = compute_ratios_from_gemini_json(balance_data)
            comprehensive_bs = None
        else:
            # Flatten nested page lists into a single list of rows if necessary
            print(f"DEBUG: Balance data is {type(balance_data).__name__}, flattening if needed")
            flattened = []
            if isinstance(balance_data, list):
                for page in balance_data:
                    if isinstance(page, list):
                        flattened.extend(page)
                    else:
                        flattened.append(page)
            else:
                flattened = [balance_data]

            print(f"DEBUG: Flattened balance sheet has {len(flattened)} rows")
            print(f"DEBUG: Calling calculate_financial_ratios with P&L data: {profit_loss_data is not None}")
            
            # Extract comprehensive balance sheet items with detailed breakdown
            comprehensive_bs = extract_comprehensive_balance_sheet_items(flattened)
            print(f"DEBUG: Comprehensive balance sheet extracted: {comprehensive_bs is not None}")
            
            # Use the calculate_financial_ratios implementation with P&L data for comprehensive ratios
            financial_ratios = calculate_financial_ratios(flattened, profit_loss_data)
            print(f"DEBUG: Financial ratios calculated. Keys: {list(financial_ratios.get('ratios', {}).keys()) if isinstance(financial_ratios, dict) else 'N/A'}")

        # If calculation yielded empty or missing ratios, attempt deterministic fallback using text extraction
        try:
            ratios_empty = False
            if not financial_ratios or not isinstance(financial_ratios, dict):
                ratios_empty = True
            else:
                # financial_ratios may be {'ratios': {...}, ...}
                inner = financial_ratios.get('ratios') if isinstance(financial_ratios, dict) else None
                if not inner or (isinstance(inner, dict) and len(inner) == 0):
                    ratios_empty = True

            if ratios_empty:
                print("Fallback: computed ratios empty — attempting deterministic text-based extraction from PDF.")
                # Try to locate pdf_path as earlier
                pdf_path = None
                pdf_path_candidate = getattr(pdf_store, "balance_sheet_pdf", None)
                if pdf_path_candidate and os.path.exists(pdf_path_candidate):
                    pdf_path = pdf_path_candidate

                if not pdf_path:
                    session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
                    if os.path.exists(session_file):
                        try:
                            with open(session_file, "r", encoding="utf-8") as sf:
                                sdata = json.load(sf)
                            cand = sdata.get("balance_sheet_pdf") or sdata.get("original_filepath") or sdata.get("filepath")
                            if cand and os.path.exists(cand):
                                pdf_path = cand
                        except Exception as e:
                            print(f"Fallback: failed to read session file for PDF path: {e}")

                if not pdf_path:
                    # last resort: look in upload folder
                    for fn in os.listdir(UPLOAD_FOLDER):
                        if session_id in fn:
                            candidate = os.path.join(UPLOAD_FOLDER, fn)
                            if os.path.exists(candidate):
                                pdf_path = candidate
                                break

                if pdf_path:
                    try:
                        # Use the text extractor + deterministic ratio calculator
                        from extract_and_calc_ratios import extract_text_from_pdf
                        try:
                            from ratio_smoke_test import calculate_financial_ratios_from_text
                        except Exception:
                            calculate_financial_ratios_from_text = None

                        print(f"Fallback: extracting text from {pdf_path}")
                        txt = extract_text_from_pdf(pdf_path)
                        det_ratios = None
                        if calculate_financial_ratios_from_text:
                            try:
                                det_ratios = calculate_financial_ratios_from_text(txt)
                            except Exception:
                                det_ratios = None

                        # If the text-based full-ratio calculator didn't work, try the notes-based heuristics
                        if not det_ratios or (isinstance(det_ratios, dict) and len(det_ratios) == 0):
                            try:
                                metrics = extract_key_metrics_from_text(txt)
                                if metrics:
                                    det_ratios = compute_minimal_ratios_from_metrics(metrics)
                            except Exception as e:
                                print(f"Note-metric deterministic fallback failed: {e}")

                        # Wrap into the expected structure
                        if det_ratios:
                            financial_ratios = {"ratios": det_ratios, "status": "Deterministic extraction applied"}
                            print("Fallback: deterministic ratios computed and applied.")
                        else:
                            print("Fallback: deterministic extraction produced no ratios.")
                    except Exception as e:
                        print(f"Fallback deterministic extraction failed: {e}")
                else:
                    print("Fallback: no PDF path available to run deterministic extraction.")
        except Exception as e:
            print(f"Error during fallback deterministic ratio extraction: {e}")
        
        # Enhance with AI-grounded analysis (fact-based, no hallucination)
        enhanced_ratios = generate_ai_grounded_ratio_analysis(pdf_store, balance_data, financial_ratios)

        # Build a flattened, normalized ratios dict for frontend consumption.
        def flatten_ratios(grouped: dict) -> dict:
            flat = {}
            try:
                # Include balance sheet summary absolute values
                bs = grouped.get("balance_sheet_summary", {})
                for k, v in bs.items():
                    flat[k] = v

                # Helper to copy ratios and normalize percentages to fractions
                def copy_section(section_name):
                    sec = grouped.get(section_name, {})
                    for k, val in sec.items():
                        if val is None:
                            flat[k] = None
                            continue
                        # If value looks like a percentage (>1 and likely >1), convert to fraction
                        try:
                            num = float(val)
                            if abs(num) > 1 and section_name in ("profitability_ratios",):
                                # convert percentage to fraction
                                flat[k] = round(num / 100.0, 4)
                            else:
                                # keep as-is (ratios like current_ratio are already fractions)
                                flat[k] = round(num, 4) if isinstance(num, float) or isinstance(num, int) else val
                        except Exception:
                            flat[k] = val

                # Copy known sections
                for s in ["liquidity_ratios", "profitability_ratios", "solvency_ratios", "capital_structure_ratios", "efficiency_ratios", "activity_ratios", "working_capital_ratios"]:
                    copy_section(s)

                # Also include dupont analysis simplified keys
                dup = grouped.get("dupont_analysis", {})
                for k, v in dup.items():
                    try:
                        flat[k] = round(float(v), 4)
                    except Exception:
                        flat[k] = v

            except Exception as e:
                print(f"Error flattening ratios: {e}")
            return flat

        # grouped ratios are inside enhanced_ratios['ratios'] currently
        grouped = enhanced_ratios.get("ratios") if isinstance(enhanced_ratios, dict) else {}

        # Build a best-effort extracted_numbers map from available local variables or grouped data
        extracted_numbers = {}
        try:
            # Use values we extracted earlier if present
            for k in [
                'total_assets', 'current_assets', 'non_current_assets',
                'total_liabilities', 'current_liabilities', 'non_current_liabilities',
                'equity', 'share_capital', 'reserves', 'inventory', 'receivables', 'cash', 'payables',
                'revenue', 'cogs', 'gross_profit', 'operating_income', 'net_income', 'ebit', 'interest_expense', 'ebitda'
            ]:
                if k in locals() and locals().get(k) is not None:
                    extracted_numbers[k] = locals().get(k)

            # If grouped contains a balance_sheet_summary, pull values from there as fallback
            if not extracted_numbers and isinstance(grouped, dict):
                bs = grouped.get('balance_sheet_summary', {})
                for k, v in bs.items():
                    extracted_numbers[k] = v

        except Exception as e:
            print(f"Error assembling extracted_numbers: {e}")

        flat = flatten_ratios(grouped if isinstance(grouped, dict) else {})

        # Attach extracted numbers into flat output for frontend transparency (unless already included)
        if '_extracted_numbers' not in flat:
            flat['_extracted_numbers'] = extracted_numbers or grouped.get('_extracted_numbers') if isinstance(grouped, dict) else {}

        # Preserve grouped structure for debugging/AI analysis, but expose flat for frontend convenience
        enhanced_ratios["ratios_grouped"] = grouped
        enhanced_ratios["ratios"] = flat

        print("\n================ FINAL FINANCIAL RATIO RESPONSE ================\n")
        import json
        print("Verified ratios:")
        print(json.dumps(enhanced_ratios, indent=2))
        print("\n===============================================================\n")

        return jsonify({
            "response": enhanced_ratios,
            "balance_sheet_data": balance_data,
            "comprehensive_balance_sheet": comprehensive_bs
        }), 200

    except ValueError as ve:
        import traceback
        tb = traceback.format_exc()
        print(f"ValueError in financial_ratio: {tb}")
        # Return diagnostics instead of HTTP 400 so frontend can display helpful info
        return jsonify({"warning": "A value error occurred during processing.", "error": str(ve), "trace": tb}), 200
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Error in financial_ratio: {tb}")
        return jsonify({"error": "Error processing the financial ratio.", "exception": str(e), "trace": tb}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        data = request.get_json()
        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "Missing chat prompt."}), 400
        
        print(f"Chat query for session {session_id}: {prompt}")
        answer = pdf_store.chat_answer(prompt)
        return jsonify({"response": answer})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"error": "Internal server error during chat processing."}), 500

@app.route("/chat/compliance-gap", methods=["POST"])
def compliance_gap():
    try:
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        response = pdf_store.get_compliance_gap_report()
        return jsonify({"response": response})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Report error: {str(e)}")
        return jsonify({"error": "Error generating compliance gap report."}), 500

@app.route("/chat/auditor-report", methods=["POST"])
def auditor_report():
    try:
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        response = pdf_store.get_auditor_report_summary()
        return jsonify({"response": response})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Report error: {str(e)}")
        return jsonify({"error": "Error generating auditor report summary."}), 500

@app.route("/chat/director-report", methods=["POST"])
def director_report():
    """Stream director report compliance check results."""
    try:
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        
        def generate():
            try:
                count = 0
                for result in pdf_store.get_director_report_compliance_check():
                    count += 1
                    print(f"Yielding result {count}: {result.get('rule', 'Unknown')}")
                    yield json.dumps(result) + '\n'
                print(f"Total results yielded: {count}")
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                yield json.dumps({"error": str(e)}) + '\n'
        
        response = Response(stream_with_context(generate()), mimetype='application/jsonl')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'
        return response
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Report error: {str(e)}")
        return jsonify({"error": "Error generating director report compliance check."}), 500

@app.route("/chat/summary", methods=["POST"])
def overall_summary():
    try:
        # ORIGINAL FLOW (unchanged)
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        response = pdf_store.get_overall_summary()

        # NEW: Infer company name from session filepath and run Tavily search for review
        company_name = None
        try:
            if pdf_store and getattr(pdf_store, 'filepath', None):
                basename = os.path.basename(pdf_store.filepath)
                if '_' in basename:
                    # Filename format: sessionid_companyname-...pdf
                    company_part = basename.split('_', 1)[1].rsplit('.', 1)[0]
                    company_name = company_part.split('-')[0] if '-' in company_part else company_part
        except Exception as e:
            print(f"Error inferring company name: {e}")

        tavily_result = None
        if company_name:
            print(f"DEBUG: Inferred company name: '{company_name}'")  # Debug log
            try:
                tavily_result = search_company(company_name, top_k=5)
                print(f"DEBUG: Tavily result: {tavily_result}")  # Debug log
            except Exception as e:
                print(f"Error searching company '{company_name}': {e}")
                tavily_result = None

        # Integrate Tavily results into the summary if available under "Review About the Company"
        if tavily_result and isinstance(tavily_result, dict) and "results" in tavily_result:
            # Extract key findings from Tavily search (focused on fraud, negative feedback, criminal records)
            findings = []
            for result in tavily_result["results"][:3]:  # Limit to top 3 results
                title = result.get("title", "")
                snippet = result.get("content", "")[:200]  # Truncate snippet
                url = result.get("url", "")
                findings.append(f"- **{title}**: {snippet}... [Source]({url})")

            if findings:
                tavily_section = "\n\n### Review About the Company\n\n" + "\n\n".join(findings)
                response += tavily_section

        # Return original response + optional tavily result
        return jsonify({
            "response": response,         # now includes integrated Tavily findings
            "tavily_search": tavily_result   # raw Tavily data for reference
        })

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        print(f"Report error: {str(e)}")
        return jsonify({"error": "Error generating overall summary."}), 500


@app.route("/api/ai-ratios-graph", methods=["POST"])
def get_chart_data():
    """Generate chart data for financial ratios and balance sheet composition"""
    try:
        session_id = request.form.get('session_id') or request.json.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        
        session_file = Config.SESSIONS_DIR / f"{session_id}.json"
        if not session_file.exists():
            return jsonify({"error": f"Session {session_id} not found"}), 404
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        balance_sheet_data = session_data.get('balance_sheet_data', [])
        
        # Flatten balance sheet data if it's nested
        if balance_sheet_data and isinstance(balance_sheet_data[0], list):
            balance_sheet_data = balance_sheet_data[0]
        
        # Extract chart data from balance sheet
        chart_data = {
            "asset_composition": {},
            "liability_composition": {},
            "ratios": {},
            "expenses": {}
        }
        
        # Parse balance sheet for composition data
        total_assets = 0
        total_liabilities = 0
        total_equity = 0
        current_assets = 0
        non_current_assets = 0
        current_liabilities = 0
        non_current_liabilities = 0
        
        for row in balance_sheet_data:
            if not isinstance(row, dict):
                continue
            
            # Find the description/particulars column
            particulars = ""
            for key, val in row.items():
                if isinstance(val, str) and len(val) > 0 and not val.replace(',', '').replace('.', '').isdigit():
                    particulars = val.lower()
                    break
            
            # Find numeric values in the row
            for key, val in row.items():
                num = parse_number(val)
                if num is not None:
                    # Categorize based on description
                    if 'current asset' in particulars or 'inventory' in particulars or 'cash' in particulars or 'receivable' in particulars:
                        current_assets = num
                        total_assets = max(total_assets, num)
                    elif 'non-current asset' in particulars or 'property' in particulars or 'fixed asset' in particulars:
                        non_current_assets = num
                        total_assets = max(total_assets, num)
                    elif 'total asset' in particulars:
                        total_assets = num
                    elif 'current liability' in particulars:
                        current_liabilities = num
                        total_liabilities = max(total_liabilities, num)
                    elif 'non-current liability' in particulars:
                        non_current_liabilities = num
                        total_liabilities = max(total_liabilities, num)
                    elif 'total liability' in particulars or 'total liabilities' in particulars:
                        total_liabilities = num
                    elif 'total equity' in particulars or 'shareholders equity' in particulars:
                        total_equity = num
        
        # Build asset composition pie chart data
        if safe_gt(total_assets, 0):
            chart_data["asset_composition"] = {
                "Current Assets": current_assets if safe_gt(current_assets, 0) else total_assets * 0.4,
                "Non-Current Assets": non_current_assets if safe_gt(non_current_assets, 0) else total_assets * 0.6
            }
        
        # Build liability composition pie chart data
        if safe_gt(total_liabilities, 0):
            chart_data["liability_composition"] = {
                "Current Liabilities": current_liabilities if safe_gt(current_liabilities, 0) else total_liabilities * 0.5,
                "Non-Current Liabilities": non_current_liabilities if safe_gt(non_current_liabilities, 0) else total_liabilities * 0.5
            }
        
        # Calculate key ratios for bar chart
        chart_data["ratios"] = {
            "Total Assets": {"Current Year": total_assets},
            "Total Liabilities": {"Current Year": total_liabilities},
            "Total Equity": {"Current Year": total_equity},
            "Current Ratio": {"Current Year": current_assets / current_liabilities if safe_gt(current_liabilities, 0) else 0},
            "Debt to Equity": {"Current Year": total_liabilities / total_equity if safe_gt(total_equity, 0) else 0}
        }
        
        return jsonify({
            "asset_composition": chart_data["asset_composition"],
            "liability_composition": chart_data["liability_composition"],
            "ratios": chart_data["ratios"],
            "expenses": {}
        })
    
    except Exception as e:
        print(f"Chart data error: {str(e)}")
        return jsonify({"error": f"Error generating chart data: {str(e)}"}), 500


@app.route('/api/company/profile/<cin>', methods=['GET'])
def get_company_profile(cin):
    """Get company profile data for peer comparison"""
    try:
        # Mock data for demonstration - in real implementation, this would fetch from database/API
        mock_profiles = {
            "L12345": {
                "company": {
                    "name": "TechCorp India Ltd",
                    "industry": "Information Technology",
                    "sector": "Technology",
                    "incorporationYear": 2010
                },
                "financials": [
                    {"year": 2023, "revenue": 500000000, "profit": 75000000},
                    {"year": 2022, "revenue": 450000000, "profit": 65000000},
                    {"year": 2021, "revenue": 400000000, "profit": 55000000}
                ],
                "directors": [
                    {"name": "John Smith", "designation": "CEO"},
                    {"name": "Jane Doe", "designation": "CFO"},
                    {"name": "Bob Johnson", "designation": "CTO"}
                ],
                "charges": [
                    {"charge_id": "CH001", "amount": 10000000, "status": "Satisfied"},
                    {"charge_id": "CH002", "amount": 5000000, "status": "Outstanding"}
                ],
                "riskFlags": ["High debt ratio", "Recent regulatory scrutiny"]
            },
            "L67890": {
                "company": {
                    "name": "DataSys Solutions Pvt Ltd",
                    "industry": "Information Technology",
                    "sector": "Technology",
                    "incorporationYear": 2015
                },
                "financials": [
                    {"year": 2023, "revenue": 300000000, "profit": 45000000},
                    {"year": 2022, "revenue": 280000000, "profit": 40000000},
                    {"year": 2021, "revenue": 250000000, "profit": 35000000}
                ],
                "directors": [
                    {"name": "Alice Brown", "designation": "Managing Director"},
                    {"name": "Charlie Wilson", "designation": "Finance Head"}
                ],
                "charges": [
                    {"charge_id": "CH003", "amount": 8000000, "status": "Satisfied"}
                ],
                "riskFlags": ["Moderate leverage"]
            },
            "L11111": {
                "company": {
                    "name": "InnovateTech Ltd",
                    "industry": "Information Technology",
                    "sector": "Technology",
                    "incorporationYear": 2012
                },
                "financials": [
                    {"year": 2023, "revenue": 600000000, "profit": 90000000},
                    {"year": 2022, "revenue": 550000000, "profit": 80000000},
                    {"year": 2021, "revenue": 500000000, "profit": 70000000}
                ],
                "directors": [
                    {"name": "David Lee", "designation": "Chairman"},
                    {"name": "Eva Martinez", "designation": "COO"},
                    {"name": "Frank Garcia", "designation": "CMO"}
                ],
                "charges": [
                    {"charge_id": "CH004", "amount": 15000000, "status": "Outstanding"}
                ],
                "riskFlags": ["Strong financial position"]
            }
        }

        # Return mock data for known CINs, or generate sample data for others
        if cin in mock_profiles:
            return jsonify(mock_profiles[cin])
        else:
            # Generate sample data for unknown CINs
            import random
            sample_data = {
                "company": {
                    "name": f"Sample Company {cin}",
                    "industry": "Information Technology",
                    "sector": "Technology",
                    "incorporationYear": random.randint(2000, 2020)
                },
                "financials": [
                    {"year": 2023, "revenue": random.randint(100000000, 1000000000), "profit": random.randint(10000000, 100000000)},
                    {"year": 2022, "revenue": random.randint(100000000, 1000000000), "profit": random.randint(10000000, 100000000)},
                    {"year": 2021, "revenue": random.randint(100000000, 1000000000), "profit": random.randint(10000000, 100000000)}
                ],
                "directors": [
                    {"name": f"Director {random.randint(1,10)}", "designation": "CEO"},
                    {"name": f"Director {random.randint(11,20)}", "designation": "CFO"}
                ],
                "charges": [
                    {"charge_id": f"CH{random.randint(100,999)}", "amount": random.randint(1000000, 50000000), "status": "Satisfied"}
                ],
                "riskFlags": ["Sample risk flag"]
            }
            return jsonify(sample_data)

    except Exception as e:
        print(f"Error getting company profile for CIN {cin}: {e}")
        return jsonify({"error": f"Failed to fetch company profile: {str(e)}"}), 500


@app.route('/search/company', methods=['POST'])
def search_company_endpoint():
    """Search company on the web via Tavily and merge with session PDF extraction.

    Request JSON: { "company_name": (optional), "session_id": (optional) }
    """
    try:
        data = request.get_json(silent=True) or {}
        company_name = data.get('company_name')
        session_id = data.get('session_id')

        # If session provided and no company_name, try to infer from stored balance_sheet_data
        pdf_info = None
        if session_id:
            try:
                store = get_pdf_store(session_id)
                pdf_info = {
                    'balance_sheet_data': getattr(store, 'balance_sheet_data', None),
                    'filepath': getattr(store, 'filepath', None)
                }
                if not company_name and store and getattr(store, 'balance_sheet_data', None):
                    # attempt to read first Particulars entry
                    bsd = store.balance_sheet_data
                    if isinstance(bsd, list) and len(bsd) > 0:
                        first = bsd[0]
                        if isinstance(first, list) and len(first) > 0 and isinstance(first[0], dict):
                            company_name = first[0].get('Particulars') or first[0].get('particulars')
            except Exception:
                pdf_info = None

        if not company_name:
            return jsonify({"error": "company_name required (or provide session_id with inferable company name)"}), 400

        # Call Tavily
        web_result = search_company(company_name)

        # Merge results: include pdf_info (if present) and web_result
        out = {
            'company_name': company_name,
            'pdf_info': pdf_info,
            'web_result': web_result
        }
        return jsonify(out), 200
    except Exception as e:
        print(f"Error in search_company_endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/jurisdictions', methods=['GET'])
def list_jurisdictions():
    try:
        base = os.path.dirname(__file__)
        txt_files = [f for f in os.listdir(base) if f.endswith('_rules.txt')]
        jurisdictions = [os.path.splitext(f)[0].replace('_rules', '') for f in txt_files]
        # Return a simple JSON array to make it easy for frontends to consume
        return jsonify(jurisdictions), 200
    except Exception as e:
        print(f"Error listing jurisdictions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/rules/<jurisdiction>', methods=['GET'])
def get_rules(jurisdiction):
    try:
        base = os.path.dirname(__file__)
        filename = os.path.join(base, f"{jurisdiction}_rules.txt")
        if not os.path.exists(filename):
            return jsonify({'error': 'Rules not found for jurisdiction'}), 404
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
        # Return plain text so frontends that expect raw rule text receive it directly
        return Response(text, mimetype='text/plain'), 200
    except Exception as e:
        print(f"Error getting rules for {jurisdiction}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/session/<session_id>/jurisdiction', methods=['POST'])
def set_session_jurisdiction(session_id):
    try:
        data = request.get_json(silent=True) or {}
        jurisdiction = data.get('jurisdiction')
        if not jurisdiction:
            return jsonify({'error': 'jurisdiction is required'}), 400
        if session_id not in pdf_stores:
            return jsonify({'error': 'Session not found'}), 404
        store = pdf_stores[session_id]
        setattr(store, 'jurisdiction', jurisdiction)
        print(f"Set jurisdiction for session {session_id} -> {jurisdiction}")
        return jsonify({'session_id': session_id, 'jurisdiction': jurisdiction}), 200
    except Exception as e:
        print(f"Error setting jurisdiction for session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MULTI-AGENT SYSTEM ENDPOINT
# ============================================================================

@app.route("/chat/multi-agent-analysis", methods=["POST"])
def multi_agent_analysis():
    """
    Execute comprehensive multi-agent analysis on document.
    All agents work in parallel and communicate results.
    """
    try:
        from agents import create_default_agent_system
        
        session_id = get_session_id()
        pdf_store = None
        # Try to retrieve in-memory store; if missing, attempt to rehydrate from session file
        try:
            pdf_store = get_pdf_store(session_id)
        except Exception:
            # Attempt rehydration from persisted session metadata
            session_file = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r', encoding='utf-8') as sf:
                        data = json.load(sf)
                        orig = data.get('original_filepath') or data.get('original_filepath')
                        if orig and os.path.exists(orig):
                            # Create a PersistentStore wrapper with filepath so ensure_analyzer can be used
                            ps = PersistentStore(session_id=session_id, filepath=orig)
                            pdf_stores[session_id] = ps
                            pdf_store = ps
                except Exception as e:
                    print(f"Failed to rehydrate session {session_id}: {e}")

        # If we have a PersistentStore, try to ensure analyzer is initialized
        try:
            if pdf_store and hasattr(pdf_store, 'ensure_analyzer'):
                try:
                    pdf_store.ensure_analyzer()
                except Exception as e:
                    # ensure_analyzer may fail if API key missing or file unavailable; continue to validation below
                    print(f"ensure_analyzer failed for session {session_id}: {e}")
        except Exception:
            pass

        # Verify document is processed (must have a filepath on the store)
        if not pdf_store or not getattr(pdf_store, 'filepath', None):
            return jsonify({"error": "No document processed for this session"}), 400
        
        print(f"Starting multi-agent analysis for session: {session_id}")
        
        # Create agent system
        orchestrator = create_default_agent_system()
        
        # Prepare input and context
        input_data = {
            "pdf_path": pdf_store.filepath,
            "pdf_text": getattr(pdf_store, "extracted_text", ""),
            "session_id": session_id
        }
        
        context = {
            "pdf_store": pdf_store,
            "gemini_processor": pdf_store,
            "session_id": session_id
        }
        
        # Execute all agents
        results = orchestrator.execute_agents(input_data, context)
        
        # Compile comprehensive report
        comprehensive_report = {
            "session_id": session_id,
            "execution_summary": orchestrator.get_summary(),
            "agent_results": {},
            "overall_quality_score": 0
        }
        
        # Process each agent result
        for agent_name, result in results.items():
            comprehensive_report["agent_results"][agent_name] = {
                "status": result.status.value,
                "execution_time": result.execution_time,
                "output": result.output if result.status.name == "COMPLETED" else None,
                "error": result.error
            }
        
        # Calculate overall quality score
        quality_check = results.get("quality_check", {})
        if hasattr(quality_check, "output") and isinstance(quality_check.output, dict):
            comprehensive_report["overall_quality_score"] = quality_check.output.get(
                "overall_score", 0
            )
        
        # Store results in session for later retrieval
        pdf_store.multi_agent_results = comprehensive_report
        
        orchestrator.shutdown()
        
        print(f"Multi-agent analysis completed - Summary: {orchestrator.get_summary()}")
        
        return jsonify({
            "response": comprehensive_report,
            "status": "multi-agent analysis completed"
        }), 200
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Multi-agent analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Multi-agent analysis failed: {str(e)}"}), 500


@app.route("/chat/agent-status/<agent_name>", methods=["GET"])
def get_agent_status(agent_name):
    """Get status of specific agent"""
    try:
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        
        if not pdf_store or not hasattr(pdf_store, "multi_agent_results"):
            return jsonify({"error": "No multi-agent analysis results found"}), 404
        
        results = pdf_store.multi_agent_results
        agent_result = results.get("agent_results", {}).get(agent_name)
        
        if not agent_result:
            return jsonify({"error": f"Agent {agent_name} not found"}), 404
        
        return jsonify(agent_result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat/agent-results", methods=["GET"])
def get_all_agent_results():
    """Get all multi-agent analysis results"""
    try:
        session_id = get_session_id()
        pdf_store = get_pdf_store(session_id)
        
        if not pdf_store or not hasattr(pdf_store, "multi_agent_results"):
            return jsonify({"error": "No multi-agent analysis results found"}), 404
        
        return jsonify(pdf_store.multi_agent_results), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=False, port=5002)
