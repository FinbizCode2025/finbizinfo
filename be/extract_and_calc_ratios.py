import sys
import json
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from ratio_smoke_test import calculate_financial_ratios_from_text


def extract_text_from_pdf(path: Path) -> str:
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is not installed. Install with: pip install pymupdf")
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    return "\n\n".join(texts)


if __name__ == '__main__':
    # Choose PDF path: first CLI arg or the first file in uploads/ with .pdf
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        uploads = Path(__file__).parent / 'uploads'
        pdfs = list(uploads.glob('*.pdf'))
        if not pdfs:
            print("No PDF files found in 'be/uploads'. Provide a PDF path as an argument.")
            sys.exit(1)
        pdf_path = pdfs[0]

    if not pdf_path.exists():
        print(f"PDF file not found: {pdf_path}")
        sys.exit(1)

    print(f"Extracting text from: {pdf_path}")
    try:
        text = extract_text_from_pdf(pdf_path)
    except ImportError as e:
        print(str(e))
        sys.exit(2)
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        sys.exit(3)

    ratios = calculate_financial_ratios_from_text(text)
    print(json.dumps(ratios, indent=2))
