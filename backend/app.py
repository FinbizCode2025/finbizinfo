import os
import json
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from docling.document_converter import DocumentConverter

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)  # Allow requests from your frontend origin

# --- Configuration ---
GOOGLE_API_KEY = 'AIzaSyAgjjIB1JKQL0L9wIKUb4XBCUYtXeiomjc'

if not GOOGLE_API_KEY:
    raise ValueError("FATAL ERROR: GOOGLE_API_KEY environment variable not set.")

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL_NAME = 'gemini-1.5-flash'  # Or 'gemini-2.0-flash' or 'gemini-pro'
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"Successfully configured Generative AI model: {MODEL_NAME}")
except Exception as e:
    raise RuntimeError(f"FATAL ERROR: Failed to configure Google Generative AI: {e}")

# --- Financial Ratio Definitions ---
RATIO_FORMULAS = """
Current Ratio = Current Assets / Current Liabilities
Quick Ratio = (Current Assets - Inventory) / Current Liabilities
Debt-to-Equity Ratio = Total Debt / Total Equity
Gross Profit Margin = (Revenue - Cost of Goods Sold) / Revenue
Net Profit Margin = Net Income / Revenue
Return on Equity (ROE) = Net Income / Average Shareholder's Equity
Inventory Turnover = Cost of Goods Sold / Average Inventory
Accounts Receivable Turnover = Net Credit Sales / Average Accounts Receivable
Asset Turnover Ratio = Net Sales / Average Total Assets
Return on Assets (ROA) = Net Income / Average Total Assets
Earnings Per Share (EPS) = (Net Income - Preferred Dividends) / Average Outstanding Common Shares
Price-to-Earnings (P/E) Ratio = Market Price per Share / Earnings Per Share (EPS)
Debt Ratio = Total Liabilities / Total Assets
Times Interest Earned (TIE) = Earnings Before Interest and Taxes (EBIT) / Interest Expense
"""

COMPLIANCE_RULES = [
    {
        "rule": "Financial Highlights & Change Business - Rule 8(5)(i) & (ii)",
        "keywords": ["financial highlights", "change in the nature of business"]
    },
    {
        "rule": "Web Link of Annual Return - S 134(3)(a)",
        "keywords": ["web address", "annual return", "section 92"]
    },
    {
        "rule": "Number Of Board Meetings - S 134(3)(b)",
        "keywords": ["board meetings held", "date of board meetings", "committee meeting", "director attendance"]
    },
    {
        "rule": "Director Responsibility Statement - S 134(3)(c)",
        "keywords": ["directors' responsibility", "accounting standards", "accounting policy", "internal financial control", "going concern", "compliance with laws"]
    },
    {
        "rule": "Fraud Reporting by Auditor - S 134(3)(ca)",
        "keywords": ["fraud reported", "section 143(12)"]
    },
    {
        "rule": "Declaration by Independent Director - S 134(3)(d)",
        "keywords": ["independent director", "declaration of independence"]
    },
    {
        "rule": "Risk Management Policy - S 134(3)(n)",
        "keywords": ["risk management policy", "elements of risk"]
    },
    {
        "rule": "Explanation on Auditor Qualification - S 134(3)(f)",
        "keywords": ["auditor qualification", "auditor remarks", "auditor disclaimer", "board comments"]
    },
    {
        "rule": "Inter-Corporate Loans & Investments - S 134(3)(g)",
        "keywords": ["section 186", "loan", "investment", "guarantee", "security"]
    },
    {
        "rule": "Related Party Transactions - S 134(3)(h)",
        "keywords": ["related party transaction", "contract", "arrangement", "section 188"]
    },
    {
        "rule": "State of Company’s Affairs - S 134(3)(i)",
        "keywords": ["state of affairs", "company’s performance", "sales turnover", "net profit"]
    },
    {
        "rule": "Transfer to Reserves - S 134(3)(j)",
        "keywords": ["transfer to reserve", "general reserve", "debenture redemption reserve"]
    },
    {
        "rule": "Dividends - S 134(3)(k)",
        "keywords": ["dividend", "recommendation", "rate of dividend"]
    },
    {
        "rule": "Post Balance Sheet Events - S 134(3)(l)",
        "keywords": ["material changes", "post balance sheet", "financial position after year end"]
    },
    {
        "rule": "Energy, Tech, & Foreign Exchange - Rule 8(3) + S 134(3)(m)",
        "keywords": ["conservation of energy", "technology absorption", "foreign exchange earnings", "foreign exchange outgo"]
    },
    {
        "rule": "Auditor Appointment/Reappointment",
        "keywords": ["auditor appointment", "auditor reappointment", "continuation of auditor"]
    },
    {
        "rule": "Subsidiaries, JVs, Associates - Rule 8(5)(iv)",
        "keywords": ["subsidiary", "joint venture", "associate company", "ceased", "became"]
    },
    {
        "rule": "Performance of Subsidiaries, Associates, JVs - Rule 8(1)",
        "keywords": ["performance of subsidiary", "associate company", "joint venture", "consolidated financial statement"]
    },
    {
        "rule": "Directors/KMP Changes - S 134(3)(q) r/w Rule 8(5)(iii)",
        "keywords": ["appointment of director", "resignation of director", "appointment of KMP", "resignation of KMP"]
    },
    {
        "rule": "Sexual Harassment Committee - Rule 8(5)(x)",
        "keywords": ["sexual harassment", "committee for women", "workplace policy"]
    },
    {
        "rule": "Voluntary Revision - S 131",
        "keywords": ["revision of board report", "revised financial statement", "section 131"]
    },
    {
        "rule": "Internal Financial Controls - Rule 8(5)(viii)",
        "keywords": ["internal financial control", "adequacy of internal control", "section 134(5)(e)"]
    },
    {
        "rule": "Details of Deposits - Rule 8(5)(v)",
        "keywords": ["deposits", "loan from directors"]
    },
    {
        "rule": "Cost Records Compliance - Rule 8(5)(ix)",
        "keywords": ["cost records", "cost accounting records", "maintenance of cost records"]
    },
    {
        "rule": "Insolvency Proceedings - Rule 8(5)(xi)",
        "keywords": ["insolvency", "bankruptcy code", "IBC", "pending proceedings"]
    },
    {
        "rule": "Valuation Differences - Rule 8(5)(xii)",
        "keywords": ["valuation difference", "settlement valuation", "loan valuation", "financial institution"]
    }
]

def extract_text_from_md(md_file):
    """Extracts text content from a Markdown file"""
    try:
        text = md_file.read().decode('utf-8')  # Assuming the file is UTF-8 encoded
        return text
    except Exception as e:
        error_message = f"Error reading Markdown file: {e}"
        print(error_message)
        return jsonify({'error': error_message}), 400
    
def analyze_audit_report(md_text):
    """Analyze an auditor's report and extract key information."""
    if not md_text.strip():
        return jsonify({'error': 'Markdown file has no extractable text.'}), 400

    prompt = f"""
    As a Chartered Accountant, please review the following auditor's report text and provide insights based on the checklist below.
    Identify key information and potential red flags.

    Auditor's Report Text:
    ```
    {md_text}
    ```

    Provide your analysis in a structured JSON format. The JSON should look like:
    {{
      "report_type": "...",
      "compliance_standards": "...",
      "emphasis_of_matter": "...",
      "other_matters": "...",
      "key_elements": {{
        "title_addressee": "...",
        "management_responsibility": "...",
        "auditor_responsibility": "...",
        "opinion_paragraph": "...",
        "basis_for_opinion": "...",
        "key_audit_matters": "...",
        "emphasis_other_matters": "...",
        "legal_regulatory_requirements": "...",
        "signature_date_place_udin": "...",
      }},
      "consistency": "...",
      "red_flags": "...",
      "summary": "..."
    }}
    """

    try:
        response = model.generate_content(prompt)
        print("Gemini raw response:\n", response.text)

        json_start = response.text.find('{')
        json_end = response.text.rfind('}')
        if json_start == -1 or json_end == -1:
            raise ValueError("Gemini response did not include a valid JSON block.")

        json_text = response.text[json_start:json_end + 1]
        analysis_result = json.loads(json_text)

        return analysis_result

    except Exception as e:
        print("Error in Gemini response processing:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': f"Gemini error: {str(e)}"}), 500
    
def check_director_compliance_rules(text):
    results = []
    text_lower = text.lower()

    compliant_count = 0

    for rule in COMPLIANCE_RULES:
        found = any(keyword.lower() in text_lower for keyword in rule["keywords"])
        if found:
            compliant_count += 1
        results.append({
            "rule": rule["rule"],
            "status": "Compliant" if found else "Non-Compliant",
            "remarks": "" if found else f"Missing disclosures: {', '.join(rule['keywords'])}"
        })

    total_rules = len(COMPLIANCE_RULES)
    if compliant_count == total_rules:
        conclusion = "Fully Compliant – All required disclosures are present."
    elif compliant_count == 0:
        conclusion = "Non-Compliant – No required disclosures found."
    else:
        conclusion = f"Partially Compliant – {compliant_count} out of {total_rules} rules satisfied."

    return {
        "results": results,
        "conclusion": conclusion
    }

def generate_automatic_ratio_analysis(markdown_content, ratio_formulas):
    """Generates response using AI to automatically calculate all possible ratios."""
    prompt = f"""
    I’m uploading a financial report (e.g., annual report or Form 10-K) for a company. Please analyze the document and:

    Determine whether it includes the necessary numerical data to calculate key financial ratios. Specifically, look for:
    Net Sales (Revenue)
    Gross Profit
    Net Income
    Total Assets
    Total Liabilities
    Shareholders’ Equity
    Current Assets
    Current Liabilities
    Inventory
    Cost of Goods Sold (COGS)
    Number of Outstanding Shares (if available)
    If the necessary financial data is missing or incomplete, explain what’s missing and outline the key financial ratios that would typically be calculated for such a company. Include:
    The name and formula for each ratio
    A short interpretation of what the ratio tells us about the business
    Any relevant context or insights you can infer from the qualitative content of the report
    If possible, create a hypothetical example of the ratios using estimated or assumed values, and explain the reasoning.
    Please format the output clearly using headings for each ratio category (e.g., Profitability, Liquidity, Leverage, Efficiency, Market).
    
    **Financial Ratio Formulas:**
    {ratio_formulas}

    **MARKDOWN Content:**
    ```text
    {markdown_content}
    ```
    """
    
    try:
        response = model.generate_content(prompt)
        if not response.parts:
            return f"Error: AI analysis failed. Reason: {response.prompt_feedback.block_reason.name if response.prompt_feedback.block_reason else 'No block reason provided.'}"
        return response.text.strip()
    except Exception as e:
        return f"Error: An unexpected error occurred while generating the analysis ({e})."

def parse_pdf_with_docling(pdf_file_path):
    """Extracts text from a PDF file using Docling and converts it to markdown."""
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_file_path)
        markdown = result.document.export_to_markdown()
        return markdown, None
    except Exception as e:
        return None, f"Error during Docling conversion: {e}"

# --- Flask Routes ---
@app.route('/analyze_pdf_ratios', methods=['POST'])
def process_markdown_for_ratios():
    """Handles Markdown file upload, text extraction, and automatic ratio analysis."""
    if 'markdown' not in request.files:
        return jsonify({'error': 'Request is missing the Markdown file part'}), 400

    markdown_file = request.files['markdown']
    if markdown_file.filename == '':
        return jsonify({'error': 'No Markdown file selected'}), 400

    if not markdown_file.filename.lower().endswith('.md'):
        return jsonify({'error': 'Invalid file type. Only Markdown files are allowed.'}), 400

    # Save the uploaded markdown file temporarily
    markdown_file_path = f'./temp/{markdown_file.filename}'
    os.makedirs(os.path.dirname(markdown_file_path), exist_ok=True)
    markdown_file.save(markdown_file_path)

    # Read the content of the markdown file
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
    except Exception as e:
        return jsonify({'error': f"Failed to read the Markdown file: {e}"}), 400

    # Call the AI function for ratio analysis
    ai_response = generate_automatic_ratio_analysis(markdown_content, RATIO_FORMULAS)

    if "AI response blocked" in ai_response or "AI model returned an empty response" in ai_response:
        return jsonify({'error': ai_response}), 500
    else:
        return jsonify({'response': ai_response})

@app.route('/generate_markdown', methods=['POST'])
def generate_markdown():
    """Handles PDF upload, generates markdown content, and saves it to a file."""
    if 'pdf' not in request.files:
        return jsonify({'error': 'Request is missing the PDF file part'}), 400

    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({'error': 'No PDF file selected'}), 400

    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400

    # Save the uploaded file temporarily
    pdf_file_path = f'./temp/{pdf_file.filename}'
    os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)
    pdf_file.save(pdf_file_path)

    # Parse PDF using Docling
    markdown_content, error = parse_pdf_with_docling(pdf_file_path)

    if error:
        return jsonify({'error': f"PDF Processing Failed: {error}"}), 400

    # Save the markdown content to a file
    markdown_file_path = f'./saved_markdowns/{os.path.splitext(pdf_file.filename)[0]}.md'
    os.makedirs(os.path.dirname(markdown_file_path), exist_ok=True)
    with open(markdown_file_path, 'w', encoding='utf-8') as markdown_file:
        markdown_file.write(markdown_content)

    return jsonify({
        'message': 'Markdown file generated and saved successfully.',
        'markdown_file_path': markdown_file_path
    })

@app.route('/saved_markdowns/<filename>', methods=['GET'])
def get_markdown_file(filename):
    try:
        return send_from_directory('./saved_markdowns', filename)
    except FileNotFoundError:
        return jsonify({'error': 'Markdown file not found'}), 404

@app.route('/api/analyze-audit-report', methods=['POST'])
def upload_and_analyze():
    """Handles Markdown file upload and analyzes the content."""
    if 'md_file' not in request.files:
        return jsonify({'error': "No Markdown file uploaded"}), 400

    md_file = request.files['md_file']
    if md_file.filename == '':
        return jsonify({'error': "No file selected"}), 400

    if md_file and md_file.filename.lower().endswith('.md'):
        try:
            # Extract text from the Markdown file
            md_text = md_file.read().decode('utf-8')  # Ensure UTF-8 decoding
            if not md_text.strip():
                return jsonify({'error': 'Markdown file has no extractable text.'}), 400

            # Analyze the Markdown content
            analysis_result = analyze_audit_report(md_text)
            if isinstance(analysis_result, tuple):  # Handle errors from `analyze_audit_report`
                return analysis_result

            return jsonify({'insights': analysis_result}), 200
        except Exception as e:
            print("Unexpected error:", str(e))
            print(traceback.format_exc())
            return jsonify({'error': f"Unexpected error: {e}"}), 500
    else:
        return jsonify({'error': "Invalid file format. Please upload a Markdown (.md) file."}), 400
    
@app.route('/api/analyze-directors-report', methods=['POST'])
def analyze_directors_report():
    if 'md_file' not in request.files:
        return jsonify({'error': "No Markdown file uploaded"}), 400

    md_file = request.files['md_file']
    if md_file.filename == '':
        return jsonify({'error': "No file selected"}), 400

    if not md_file.filename.lower().endswith('.md'):
        return jsonify({'error': "Invalid file format. Please upload a Markdown (.md) file."}), 400

    try:
        md_text = md_file.read().decode('utf-8')
        if not md_text.strip():
            return jsonify({'error': 'Markdown file is empty.'}), 400

        analysis = check_director_compliance_rules(md_text)
        return jsonify({
            'compliance_results': analysis['results'],
            'conclusion': analysis['conclusion']
        }), 200

    except Exception as e:
        print("Unexpected error:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': f"Unexpected error: {e}"}), 500


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Markdown Generator Backend is running!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
