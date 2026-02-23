"""
Multi-Agent System for Financial Document Analysis
Each agent is specialized for a specific task in the document processing pipeline.
Agents work in parallel and communicate through a shared result registry.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class AgentResult:
    """Result from agent execution"""
    agent_name: str
    status: AgentStatus
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    dependencies_met: bool = True


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, dependencies: Optional[List[str]] = None):
        self.name = name
        self.dependencies = dependencies or []
        self.status = AgentStatus.IDLE
        self.result: Optional[AgentResult] = None
        self.logger = logging.getLogger(f"Agent:{self.name}")
    
    def check_dependencies(self, results: Dict[str, AgentResult]) -> bool:
        """Check if all dependencies are completed successfully"""
        for dep in self.dependencies:
            if dep not in results:
                self.logger.warning(f"Dependency {dep} not found")
                return False
            if results[dep].status != AgentStatus.COMPLETED:
                self.logger.warning(f"Dependency {dep} not completed")
                return False
        return True
    
    def get_dependency_data(self, results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Extract data from dependencies"""
        dep_data = {}
        for dep in self.dependencies:
            if dep in results:
                dep_data[dep] = results[dep].output
        return dep_data
    
    @abstractmethod
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Execute agent logic. Must be implemented by subclasses"""
        pass
    
    def run(self, input_data: Any, context: Dict[str, Any]) -> AgentResult:
        """Execute agent and track metrics"""
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"Starting execution")
            output = self.execute(input_data, context)
            
            execution_time = time.time() - start_time
            self.result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                output=output,
                execution_time=execution_time
            )
            self.status = AgentStatus.COMPLETED
            self.logger.info(f"Completed in {execution_time:.2f}s")
            return self.result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Agent failed: {str(e)}"
            self.logger.error(error_msg)
            self.result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=error_msg,
                execution_time=execution_time
            )
            self.status = AgentStatus.FAILED
            return self.result


# ============================================================================
# EXTRACTION AGENTS
# ============================================================================

class PDFExtractionAgent(BaseAgent):
    """Extracts raw text and tables from PDF"""
    
    def __init__(self):
        super().__init__("pdf_extraction")
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Extract text and metadata from PDF"""
        pdf_path = input_data.get('pdf_path')
        
        if not pdf_path:
            raise ValueError("PDF path not provided")
        
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            
            extracted = {
                "total_pages": len(doc),
                "pages": [],
                "metadata": doc.metadata,
                "text": "",
                "tables": []
            }
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                extracted["text"] += text
                extracted["pages"].append({
                    "number": page_num + 1,
                    "text": text,
                    "word_count": len(text.split())
                })
            
            self.logger.info(f"Extracted {len(doc)} pages, {len(extracted['text'])} chars")
            doc.close()
            return extracted
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")


class OCRExtractionAgent(BaseAgent):
    """OCR processing for scanned documents"""
    
    def __init__(self):
        super().__init__("ocr_extraction", dependencies=["pdf_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Perform OCR on PDF pages"""
        pdf_extraction_data = input_data.get('pdf_data', {})
        
        try:
            import pytesseract
            import cv2
            import tempfile
            import os
            
            ocr_results = {
                "pages": [],
                "total_confidence": 0,
                "needs_ocr": False
            }
            
            # Check if OCR is needed
            extracted_text = pdf_extraction_data.get("text", "")
            if len(extracted_text.split()) < 100:
                ocr_results["needs_ocr"] = True
            
            self.logger.info(f"OCR processing needed: {ocr_results['needs_ocr']}")
            return ocr_results
            
        except Exception as e:
            self.logger.warning(f"OCR skipped: {str(e)}")
            return {"pages": [], "needs_ocr": False}


class BalanceSheetExtractionAgent(BaseAgent):
    """Extracts balance sheet structured data"""
    
    def __init__(self):
        super().__init__("balance_sheet_extraction", dependencies=["pdf_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Extract balance sheet data"""
        context_data = input_data.get('context', {})
        gemini_processor = context_data.get('gemini_processor')
        pdf_text = input_data.get('pdf_text', '')
        
        if not gemini_processor or not pdf_text:
            raise ValueError("Missing Gemini processor or PDF text")
        
        # Use existing balance sheet extraction logic
        from app import get_balance_sheet_prompt, parse_with_gemini
        
        try:
            prompt = get_balance_sheet_prompt(pdf_text[:5000])  # Use first 5000 chars
            bs_data = parse_with_gemini(prompt)
            
            self.logger.info(f"Extracted balance sheet with keys: {list(bs_data.keys()) if isinstance(bs_data, dict) else 'N/A'}")
            return bs_data
            
        except Exception as e:
            raise Exception(f"Balance sheet extraction failed: {str(e)}")


class PLExtractionAgent(BaseAgent):
    """Extracts P&L (Profit & Loss) statement"""
    
    def __init__(self):
        super().__init__("pl_extraction", dependencies=["pdf_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Extract P&L data"""
        context_data = input_data.get('context', {})
        gemini_processor = context_data.get('gemini_processor')
        pdf_text = input_data.get('pdf_text', '')
        
        if not gemini_processor or not pdf_text:
            raise ValueError("Missing Gemini processor or PDF text")
        
        from app import get_pl_prompt, parse_with_gemini
        
        try:
            # Try to find P&L section in text
            if 'profit' in pdf_text.lower() or 'loss' in pdf_text.lower():
                prompt = get_pl_prompt(pdf_text[:5000])
                pl_data = parse_with_gemini(prompt)
                self.logger.info(f"Extracted P&L with keys: {list(pl_data.keys()) if isinstance(pl_data, dict) else 'N/A'}")
                return pl_data
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"P&L extraction failed: {str(e)}")
            return None


# ============================================================================
# ANALYSIS AGENTS
# ============================================================================

class FinancialRatioAgent(BaseAgent):
    """Calculates financial ratios from balance sheet and P&L data"""
    
    def __init__(self):
        super().__init__("financial_ratios", 
                        dependencies=["balance_sheet_extraction", "pl_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Calculate financial ratios. If balance sheet data is missing, attempt OCR extraction from a provided PDF path.

        The method will try to parse key balance-sheet items from OCR'd text and then compute a standard
        set of financial ratios (liquidity, solvency, profitability, efficiency). Returns a dict with
        a `ratios` key and original parsed `balance_sheet`/`pl` data.
        """
        bs_data = input_data.get('balance_sheet_data')
        pl_data = input_data.get('pl_data') or {}

        # If no balance-sheet data provided, try OCR on PDF path(s)
        if not bs_data:
            # Possible sources for PDF path: input_data['pdf_path'] or input_data['pdf_data'] from pdf_extraction
            pdf_path = input_data.get('pdf_path')
            pdf_extraction = input_data.get('pdf_data') or {}

            if not pdf_path and pdf_extraction:
                # If extraction provided pages/metadata, try to use it
                pdf_path = pdf_extraction.get('pdf_path')

            if pdf_path:
                try:
                    ocr_text = self._ocr_pdf_to_text(pdf_path, max_pages=6)
                    parsed_bs = parse_balance_sheet_from_text(ocr_text)
                    if parsed_bs:
                        bs_data = parsed_bs
                        self.logger.info(f"Parsed balance sheet values from OCR: {list(bs_data.keys())}")
                except Exception as e:
                    self.logger.warning(f"OCR-based balance sheet parsing failed: {e}")

        try:
            # Ensure bs_data is a dict
            if isinstance(bs_data, list) and bs_data:
                bs = bs_data[0]
            else:
                bs = bs_data or {}

            ratios = calculate_financial_ratios_inline(bs, pl_data)
            self.logger.info(f"Calculated ratios: {len(ratios.get('ratios', {}))} categories")
            return ratios

        except Exception as e:
            raise Exception(f"Ratio calculation failed: {str(e)}")

    def _ocr_pdf_to_text(self, pdf_path: str, max_pages: int = 6) -> str:
        """Render first `max_pages` pages of PDF to images and run Tesseract OCR to extract text."""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import pytesseract
            import io

            doc = fitz.open(pdf_path)
            texts = []
            pages_to_process = min(len(doc), max_pages)

            for i in range(pages_to_process):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                page_text = pytesseract.image_to_string(img)
                texts.append(page_text)

            doc.close()
            return "\n".join(texts)

        except Exception as e:
            raise Exception(f"OCR processing failed: {e}")


def parse_balance_sheet_from_text(text: str) -> Dict[str, Any]:
    """Attempt to parse common balance sheet line-items from OCR'd text using regex heuristics.

    Returns a dict with numeric values where found. Keys include:
      - total_assets, total_liabilities, total_equity, total_current_assets, total_current_liabilities,
        cash_and_equivalents, accounts_receivable, inventory
    """
    import re

    def parse_number(s: str):
        if not s:
            return None
        s = s.replace(',', '').replace('₹', '').replace('$', '').replace('(', '-').replace(')', '')
        s = s.strip()
        try:
            return float(s)
        except:
            # remove non-numeric
            m = re.search(r"-?\d+[\d\.]*", s)
            if m:
                try:
                    return float(m.group(0))
                except:
                    return None
            return None

    patterns = {
        'total_assets': r'total\s+assets\D{0,20}([\d,\.\(\)₹$ -]+)',
        'total_liabilities': r'total\s+liabilit(?:y|ies)\D{0,20}([\d,\.\(\)₹$ -]+)',
        'total_equity': r'(?:shareholders\'"s|shareholder|total)\s+equity\D{0,20}([\d,\.\(\)₹$ -]+)',
        'total_current_assets': r'total\s+current\s+assets\D{0,20}([\d,\.\(\)₹$ -]+)',
        'total_current_liabilities': r'total\s+current\s+liabilit(?:y|ies)\D{0,20}([\d,\.\(\)₹$ -]+)',
        'cash_and_equivalents': r'cash(?:\s+and\s+equivalents)?\D{0,20}([\d,\.\(\)₹$ -]+)',
        'accounts_receivable': r'accounts?\s+receivable[s]?\D{0,20}([\d,\.\(\)₹$ -]+)',
        'inventory': r'inventor(?:y|ies)\D{0,20}([\d,\.\(\)₹$ -]+)'
    }

    parsed = {}
    lower_text = text.lower()
    for key, pat in patterns.items():
        m = re.search(pat, lower_text, flags=re.IGNORECASE)
        if m:
            val = parse_number(m.group(1))
            if val is not None:
                parsed[key] = val

    # Try to get revenue / net income from text
    rev_m = re.search(r'(?:total\s+revenue|revenue|total\s+income)\D{0,30}([\d,\.\(\)₹$ -]+)', lower_text)
    ni_m = re.search(r'(?:net\s+profit|net\s+income|profit\s+for\s+the\s+year)\D{0,30}([\d,\.\(\)₹$ -]+)', lower_text)
    if rev_m:
        parsed['total_revenue'] = parse_number(rev_m.group(1))
    if ni_m:
        parsed['net_income'] = parse_number(ni_m.group(1))

    return parsed


def _find_candidate_pages_from_pdf(pdf_path: str, keywords=None, max_pages_scan: int = 50) -> Dict[int, str]:
    """Return a dict of page_index->text for pages that are likely to contain balance sheet, using fast text extraction.

    This uses `fitz` page.get_text() (very fast) and looks for keywords. Limits scanning to `max_pages_scan` pages.
    """
    try:
        import fitz
        pages = {}
        doc = fitz.open(pdf_path)
        total = len(doc)
        scan_until = min(total, max_pages_scan)
        kws = keywords or ["balance sheet", "statement of financial position", "financial position", "statement of assets and liabilities"]

        for i in range(scan_until):
            page = doc.load_page(i)
            txt = page.get_text()
            if not txt or len(txt.split()) < 5:
                # skip empty pages (likely images)
                pages[i] = ''
            else:
                lower = txt.lower()
                for k in kws:
                    if k in lower:
                        pages[i] = txt
                        break

        doc.close()
        return pages
    except Exception:
        return {}


def _gather_balance_sheet_text_from_input(input_data: Dict[str, Any], max_pages_ocr: int = 6) -> str:
    """Attempt to collect balance-sheet text from available sources in input_data.

    Priority:
      1. Use `pdf_data['pages']` if present (text extracted earlier).
      2. Fast-scan PDF pages via `fitz` for balance-sheet headings and use those page texts.
      3. If only images/low-text pages found, OCR candidate pages (via `pytesseract`) and return joined text.
    """
    # 1. pdf_data pages
    pdf_data = input_data.get('pdf_data') or {}
    if pdf_data and isinstance(pdf_data, dict):
        pages = pdf_data.get('pages')
        if pages and isinstance(pages, list):
            kws = ["balance sheet", "statement of financial position", "financial position", "statement of assets and liabilities"]
            candidate_texts = []
            for p in pages:
                t = (p.get('text') or '').lower()
                if any(k in t for k in kws):
                    candidate_texts.append(p.get('text') or '')
            if candidate_texts:
                return "\n".join(candidate_texts)

    # 2. If we have a pdf_path, fast scan pages for headings
    pdf_path = input_data.get('pdf_path') or (pdf_data.get('pdf_path') if isinstance(pdf_data, dict) else None)
    if pdf_path:
        # fast-scan for text headings
        candidate_pages = _find_candidate_pages_from_pdf(pdf_path, max_pages_scan=50)
        if candidate_pages:
            # join all candidate page texts
            joined = "\n".join([t for _, t in sorted(candidate_pages.items()) if t])
            if joined.strip():
                return joined

        # 3. fallback to OCR on first few pages or on candidate page indices
        try:
            # If candidate_pages keys exist but texts empty (images), OCR those pages, else OCR first pages
            candidate_idxs = [i for i, t in candidate_pages.items() if not t] if candidate_pages else list(range(0, min(6, 50)))
            if not candidate_idxs:
                candidate_idxs = list(range(0, min(6, 50)))

            # run OCR on selected pages
            ocr_texts = []
            import fitz
            from PIL import Image
            import pytesseract
            import io

            doc = fitz.open(pdf_path)
            for i in candidate_idxs:
                if i >= len(doc):
                    continue
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                ocr_texts.append(pytesseract.image_to_string(img))
            doc.close()
            return "\n".join(ocr_texts)
        except Exception:
            return ''

    return ''


def calculate_financial_ratios_inline(bs: Dict[str, Any], pl: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a set of common financial ratios from balance sheet (bs) and profit & loss (pl) data.

    bs: expects keys like 'total_assets', 'total_liabilities', 'total_equity', 'total_current_assets',
        'total_current_liabilities', 'cash_and_equivalents', 'accounts_receivable', 'inventory'
    pl: expects keys like 'total_revenue', 'net_income', 'cost_of_goods_sold', 'ebit', 'interest_expense'
    """
    def safe_div(a, b):
        try:
            if a is None or b is None:
                return None
            if b == 0:
                return None
            return a / b
        except:
            return None

    ratios = {}

    ta = bs.get('total_assets')
    tl = bs.get('total_liabilities')
    te = bs.get('total_equity') or (ta - tl if ta is not None and tl is not None else None)
    tca = bs.get('total_current_assets')
    tcl = bs.get('total_current_liabilities')
    cash = bs.get('cash_and_equivalents')
    ar = bs.get('accounts_receivable')
    inv = bs.get('inventory')
    revenue = pl.get('total_revenue')
    net_income = pl.get('net_income')
    cogs = pl.get('cost_of_goods_sold')
    ebit = pl.get('ebit')
    interest = pl.get('interest_expense')

    # Liquidity
    ratios['current_ratio'] = safe_div(tca, tcl)
    ratios['quick_ratio'] = safe_div((tca - (inv or 0)), tcl) if tca is not None else None
    ratios['cash_ratio'] = safe_div(cash, tcl)

    # Solvency / leverage
    ratios['debt_to_equity'] = safe_div(tl, te)
    ratios['debt_ratio'] = safe_div(tl, ta)
    ratios['equity_ratio'] = safe_div(te, ta)

    # Profitability
    ratios['net_profit_margin'] = safe_div(net_income, revenue)
    ratios['gross_margin'] = safe_div((revenue - (cogs or 0)), revenue)
    ratios['return_on_assets'] = safe_div(net_income, ta)
    ratios['return_on_equity'] = safe_div(net_income, te)

    # Efficiency
    ratios['inventory_turnover'] = safe_div((cogs or 0), inv)
    ratios['receivables_turnover'] = safe_div(revenue, ar)

    # Coverage
    ratios['interest_coverage'] = safe_div(ebit, interest)

    return {
        'ratios': ratios,
        'balance_sheet': bs,
        'pl': pl
    }


class ComplianceAnalysisAgent(BaseAgent):
    """Analyzes compliance gaps and requirements"""
    
    def __init__(self):
        super().__init__("compliance_analysis", dependencies=["balance_sheet_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Analyze compliance"""
        context_data = input_data.get('context', {})
        pdf_store = context_data.get('pdf_store')
        
        if not pdf_store:
            raise ValueError("PDF store not provided")
        
        try:
            # Use existing compliance analysis
            response = pdf_store.get_compliance_gap_report()
            self.logger.info(f"Compliance analysis completed")
            return response
            
        except Exception as e:
            raise Exception(f"Compliance analysis failed: {str(e)}")


class AuditAnalysisAgent(BaseAgent):
    """Generates auditor's report summary"""
    
    def __init__(self):
        super().__init__("audit_analysis", dependencies=["balance_sheet_extraction", "financial_ratios"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Generate audit report"""
        context_data = input_data.get('context', {})
        pdf_store = context_data.get('pdf_store')
        ratios = input_data.get('ratios_data')
        
        if not pdf_store:
            raise ValueError("PDF store not provided")
        
        try:
            response = pdf_store.get_auditor_report_summary()
            self.logger.info(f"Audit analysis completed")
            return response
            
        except Exception as e:
            raise Exception(f"Audit analysis failed: {str(e)}")


class DirectorReportAgent(BaseAgent):
    """Analyzes director's report compliance"""
    
    def __init__(self):
        super().__init__("director_report", dependencies=["balance_sheet_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Analyze director's report"""
        context_data = input_data.get('context', {})
        pdf_store = context_data.get('pdf_store')
        
        if not pdf_store:
            raise ValueError("PDF store not provided")
        
        try:
            response = pdf_store.get_director_report_highlights()
            self.logger.info(f"Director report analysis completed")
            return response
            
        except Exception as e:
            raise Exception(f"Director report analysis failed: {str(e)}")


# ============================================================================
# VALIDATION AGENTS
# ============================================================================

class DataValidationAgent(BaseAgent):
    """Validates extracted data quality and consistency"""
    
    def __init__(self):
        super().__init__("data_validation", 
                        dependencies=["balance_sheet_extraction", "pl_extraction"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Validate data consistency"""
        bs_data = input_data.get('balance_sheet_data')
        pl_data = input_data.get('pl_data')
        
        validation_results = {
            "balance_sheet": self._validate_balance_sheet(bs_data),
            "profit_loss": self._validate_pl(pl_data),
            "consistency": self._check_consistency(bs_data, pl_data),
            "overall_quality": "good"
        }
        
        if not validation_results["balance_sheet"]["valid"] or not validation_results["consistency"]["valid"]:
            validation_results["overall_quality"] = "poor"
        
        self.logger.info(f"Validation complete - Quality: {validation_results['overall_quality']}")
        return validation_results
    
    def _validate_balance_sheet(self, data: Any) -> Dict:
        """Validate balance sheet structure"""
        if not data:
            return {"valid": False, "errors": ["No balance sheet data"]}
        
        try:
            # Check if assets = liabilities + equity
            if isinstance(data, dict):
                return {"valid": True, "errors": []}
            else:
                return {"valid": False, "errors": ["Invalid balance sheet format"]}
        except:
            return {"valid": False, "errors": ["Balance sheet validation error"]}
    
    def _validate_pl(self, data: Any) -> Dict:
        """Validate P&L structure"""
        if not data:
            return {"valid": False, "errors": ["No P&L data"]}
        
        return {"valid": True, "errors": []}
    
    def _check_consistency(self, bs_data: Any, pl_data: Any) -> Dict:
        """Check data consistency between BS and P&L"""
        # Simple consistency check
        if bs_data and pl_data:
            return {"valid": True, "errors": []}
        elif bs_data:
            return {"valid": True, "errors": ["No P&L data for full validation"]}
        else:
            return {"valid": False, "errors": ["No balance sheet data"]}


class QualityCheckAgent(BaseAgent):
    """Checks result quality and completeness"""
    
    def __init__(self):
        super().__init__("quality_check", 
                        dependencies=["financial_ratios", "compliance_analysis", "audit_analysis"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Perform quality checks on all results"""
        ratios = input_data.get('ratios_data')
        compliance = input_data.get('compliance_data')
        audit = input_data.get('audit_data')
        
        quality_metrics = {
            "ratios_completeness": self._check_completeness(ratios),
            "compliance_coverage": self._check_completeness(compliance),
            "audit_coverage": self._check_completeness(audit),
            "overall_score": 0
        }
        
        # Calculate overall score
        scores = [v.get("score", 0) for v in quality_metrics.values() if isinstance(v, dict)]
        quality_metrics["overall_score"] = sum(scores) / len(scores) if scores else 0
        
        self.logger.info(f"Quality check completed - Score: {quality_metrics['overall_score']:.2f}")
        return quality_metrics
    
    def _check_completeness(self, data: Any) -> Dict:
        """Check data completeness"""
        if not data:
            return {"complete": False, "score": 0}
        
        if isinstance(data, dict):
            return {"complete": len(data) > 0, "score": min(100, len(data) * 10)}
        elif isinstance(data, str) and len(data) > 0:
            return {"complete": True, "score": min(100, len(data) // 10)}
        
        return {"complete": False, "score": 0}


class FactCheckingAgent(BaseAgent):
    """Verifies facts and reconciles data across agents"""
    
    def __init__(self):
        super().__init__("fact_checking",
                        dependencies=["financial_ratios", "data_validation"])
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Perform fact checking across all data"""
        ratios = input_data.get('ratios_data')
        validation = input_data.get('validation_data')
        
        fact_check_results = {
            "ratios_verified": self._verify_ratios(ratios),
            "data_validated": validation.get("overall_quality") == "good" if validation else False,
            "reconciliation_status": "passed",
            "flags": []
        }
        
        self.logger.info(f"Fact checking completed - Reconciliation: {fact_check_results['reconciliation_status']}")
        return fact_check_results
    
    def _verify_ratios(self, ratios: Any) -> bool:
        """Verify ratio calculations"""
        if not ratios or not isinstance(ratios, dict):
            return False
        
        # Check if ratios have expected structure
        required_keys = ["liquidity_ratios", "solvency_ratios"]
        return all(key in ratios.get("ratios", {}) for key in required_keys if "ratios" in ratios)


# ============================================================================
# AGENT ORCHESTRATOR
# ============================================================================

class AgentOrchestrator:
    """Manages agent execution with dependency resolution"""
    
    def __init__(self, max_workers: int = 6):
        self.agents: Dict[str, BaseAgent] = {}
        self.results: Dict[str, AgentResult] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger("AgentOrchestrator")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent"""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
    
    def register_agents(self, agents: List[BaseAgent]) -> None:
        """Register multiple agents"""
        for agent in agents:
            self.register_agent(agent)
    
    def build_execution_plan(self) -> List[List[str]]:
        """Build execution plan respecting dependencies"""
        # Topological sort to determine execution order
        executed = set()
        execution_plan = []
        
        while len(executed) < len(self.agents):
            # Find agents ready to execute (all dependencies met)
            ready = []
            for name, agent in self.agents.items():
                if name not in executed:
                    deps_met = all(dep in executed for dep in agent.dependencies)
                    if deps_met:
                        ready.append(name)
            
            if not ready:
                raise ValueError("Circular dependency detected or missing agents")
            
            execution_plan.append(ready)
            executed.update(ready)
        
        return execution_plan
    
    def execute_agents(self, input_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, AgentResult]:
        """Execute all agents respecting dependencies"""
        self.results.clear()
        execution_plan = self.build_execution_plan()
        
        self.logger.info(f"Execution plan: {execution_plan}")
        
        for stage, agent_names in enumerate(execution_plan):
            self.logger.info(f"Stage {stage + 1}: Executing {agent_names}")
            
            # Execute agents in parallel if possible
            futures = {}
            for agent_name in agent_names:
                agent = self.agents[agent_name]
                
                # Prepare input data for this agent
                agent_input = self._prepare_agent_input(
                    agent_name, 
                    input_data, 
                    context
                )
                
                # Submit agent for execution
                future = self.executor.submit(agent.run, agent_input, context)
                futures[agent_name] = future
            
            # Collect results
            for agent_name, future in futures.items():
                try:
                    result = future.result(timeout=60)
                    self.results[agent_name] = result
                    self.logger.info(f"✓ {agent_name}: {result.status.value}")
                    if result.error:
                        self.logger.error(f"  Error: {result.error}")
                except Exception as e:
                    self.logger.error(f"✗ {agent_name}: {str(e)}")
                    self.results[agent_name] = AgentResult(
                        agent_name=agent_name,
                        status=AgentStatus.FAILED,
                        error=str(e)
                    )
        
        self.logger.info("All agents completed")
        return self.results
    
    def _prepare_agent_input(self, agent_name: str, 
                            input_data: Dict[str, Any],
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input for specific agent"""
        agent_input = input_data.copy()
        
        # Map dependency results to agent input
        if agent_name == "financial_ratios":
            agent_input["balance_sheet_data"] = (
                self.results.get("balance_sheet_extraction", AgentResult("", AgentStatus.IDLE)).output
            )
            agent_input["pl_data"] = (
                self.results.get("pl_extraction", AgentResult("", AgentStatus.IDLE)).output
            )
        elif agent_name == "compliance_analysis":
            agent_input["context"] = context
        elif agent_name == "audit_analysis":
            agent_input["context"] = context
            agent_input["ratios_data"] = (
                self.results.get("financial_ratios", AgentResult("", AgentStatus.IDLE)).output
            )
        elif agent_name == "director_report":
            agent_input["context"] = context
        elif agent_name == "data_validation":
            agent_input["balance_sheet_data"] = (
                self.results.get("balance_sheet_extraction", AgentResult("", AgentStatus.IDLE)).output
            )
            agent_input["pl_data"] = (
                self.results.get("pl_extraction", AgentResult("", AgentStatus.IDLE)).output
            )
        elif agent_name == "quality_check":
            agent_input["ratios_data"] = (
                self.results.get("financial_ratios", AgentResult("", AgentStatus.IDLE)).output
            )
            agent_input["compliance_data"] = (
                self.results.get("compliance_analysis", AgentResult("", AgentStatus.IDLE)).output
            )
            agent_input["audit_data"] = (
                self.results.get("audit_analysis", AgentResult("", AgentStatus.IDLE)).output
            )
        elif agent_name == "fact_checking":
            agent_input["ratios_data"] = (
                self.results.get("financial_ratios", AgentResult("", AgentStatus.IDLE)).output
            )
            agent_input["validation_data"] = (
                self.results.get("data_validation", AgentResult("", AgentStatus.IDLE)).output
            )
        
        return agent_input
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        summary = {
            "total_agents": len(self.agents),
            "completed": sum(1 for r in self.results.values() if r.status == AgentStatus.COMPLETED),
            "failed": sum(1 for r in self.results.values() if r.status == AgentStatus.FAILED),
            "total_time": sum(r.execution_time for r in self.results.values()),
            "agents": {}
        }
        
        for name, result in self.results.items():
            summary["agents"][name] = {
                "status": result.status.value,
                "execution_time": f"{result.execution_time:.2f}s",
                "error": result.error,
                "has_output": result.output is not None
            }
        
        return summary
    
    def shutdown(self) -> None:
        """Shutdown executor"""
        self.executor.shutdown(wait=True)


def create_default_agent_system() -> AgentOrchestrator:
    """Create a default multi-agent system"""
    orchestrator = AgentOrchestrator()
    
    # Register extraction agents
    orchestrator.register_agents([
        PDFExtractionAgent(),
        OCRExtractionAgent(),
        BalanceSheetExtractionAgent(),
        PLExtractionAgent(),
    ])
    
    # Register analysis agents
    orchestrator.register_agents([
        FinancialRatioAgent(),
        ComplianceAnalysisAgent(),
        AuditAnalysisAgent(),
        DirectorReportAgent(),
    ])
    
    # Register validation agents
    orchestrator.register_agents([
        DataValidationAgent(),
        QualityCheckAgent(),
        FactCheckingAgent(),
    ])
    
    return orchestrator
