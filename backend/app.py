import os
import json
import traceback
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import google.generativeai as genai
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash
import re
import matplotlib.pyplot as plt
import requests
import time

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)  # Allow requests from your frontend origin

# MySQL Configuration
app.config['MYSQL_HOST'] = '194.164.151.51'
app.config['MYSQL_USER'] = 'finbizuser'
app.config['MYSQL_PASSWORD'] = 'Log!n123@1P'  # empty string for no password
app.config['MYSQL_DB'] = 'financial_analysis'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

# JWT Setup
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key!
jwt = JWTManager(app)

GOOGLE_API_KEY = ''
API_TOKEN = "d1f7038fdfc82142b3db85a185304e9fed459089"
PAPERLESS_URL = "http://194.164.151.51"

headers = {
    "Authorization": f"Token {API_TOKEN}"
}

# Add a global variable to allow updating the API key at runtime
google_api_key = GOOGLE_API_KEY

@app.route('/api/set-api-key', methods=['POST'])
def set_api_key():
    """
    Set the Google API key at runtime.
    Expects JSON: { "api_key": "YOUR_KEY" }
    """
    global google_api_key, model
    data = request.get_json()
    if not data or 'api_key' not in data:
        return jsonify({'error': 'API key is required.'}), 400

    google_api_key = data['api_key']
    try:
        genai.configure(api_key=google_api_key)
        MODEL_NAME = 'gemini-1.5-flash'
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"Google API key updated and model reconfigured.")
        return jsonify({'message': 'API key updated successfully.'}), 200
    except Exception as e:
        print("Failed to update Google API key:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': f"Failed to update API key: {e}"}), 500

@app.route('/api/get-api-key', methods=['GET'])
def get_api_key():
    """
    Get the current Google API key (for admin/debug only).
    """
    return jsonify({'api_key': google_api_key}), 200

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    MODEL_NAME = 'gemini-1.5-flash'  # Or 'gemini-2.0-flash' or 'gemini-pro'
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"Successfully configured Generative AI model: {MODEL_NAME}")
except Exception as e:
    raise RuntimeError(f"FATAL ERROR: Failed to configure Google Generative AI: {e}")

# --- Financial Ratio Definitions ---
RATIO_FORMULAS = """
Net Profit Margin = Net Profit After Tax / Revenue from Operations
Current Ratio = Current Assets / Current Liabilities
Quick Ratio = (Current Assets - Inventories - Prepaid Expenses) / Current Liabilities
Debt-to-Equity Ratio = (Short Term Borrowings + Long Term Borrowings) / Shareholders' Equity
Average Trade Receivables = (Opening Trade Receivables + Closing Trade Receivables) / 2
Total Sales = Revenue from Operations + Other Income
Gross Profit Margin = (Revenue from Operations - Cost of Goods Sold) / Revenue from Operations
Return on Equity (ROE) = (Net Profit After Tax) / ((sum of net worth of both years) / 2)
Inventory Turnover Ratio = Cost of Goods Sold / Average Inventory
Accounts Receivable Turnover Ratio = Net Credit Sales / Average Accounts Receivable
Asset Turnover Ratio = Net Sales / Average Total Assets
Return on Assets (ROA) = Net Profit After Tax / Average Total Assets
Earnings Per Share (EPS) = (Net Profit After Tax - Preference Dividend) / Weighted Average Number of Equity Shares Outstanding
Price-to-Earnings (P/E) Ratio = Market Price per Equity Share / Earnings Per Share (EPS)
Debt Ratio = Total Liabilities / Total Assets
EBIT = Profit/Loss Before Tax + Expense(Finance Costs)
EBITDA = EBIT + Depreciation and Amortization
EBIT Margin = EBIT / Revenue from Operations
EBITDA Margin = EBITDA / Revenue from Operations
Times Interest Earned (TIE) = EBIT / Finance Costs
Working Capital = Current Assets - Current Liabilities
Interest Coverage Ratio = EBIT / Interest Expense
Operating Profit Margin = Operating Profit / Revenue from Operations
Cash Ratio = (Cash and Cash Equivalents + Marketable Securities) / Current Liabilities
Dividend Payout Ratio = Dividend Declared / Net Profit After Tax
Book Value Per Share = (Shareholders' Equity - Preference Share Capital) / Number of Equity Shares Outstanding
Capital Gearing Ratio = Fixed Cost Bearing Capital / Equity Shareholders' Funds
Proprietary Ratio = Shareholders' Funds / Total Tangible Assets
Long-term Debt to Capitalization Ratio = Long-term Debt / (Long-term Debt + Shareholders' Equity)
"""

CARO_APPLICABLE_KEYWORDS = """
CARO 2020 is applicable for all statutory audits commencing on or after 1 April 2021 corresponding to the financial year 2020-21. Please read values carefully or calculate necessary values required to check CARO's Applicability. The order is applicable to all companies which were covered by CARO 2016. Thus, CARO 2020 applies to all the companies currently, including a foreign company. However, it does not apply to the following companies:

One person company.
Small companies (Companies with paidup share capital + reserve and surplus less than/equal to Rs 4 crore and with a preceding financial year's total revenue is less than/equal to Rs 40 crore).
Banking companies.
Companies registered for charitable purposes.
Insurance companies.
The following private companies are also exempt from the requirements of CARO, 2020: –
Whose gross receipts or revenue (including revenue from discontinuing operations) is less than or equal to Rs 10 crore in the financial year.
Whose paid up share capital + reserves and surplus is less than or equal to Rs 1 crore as on the balance sheet date (i.e. usually at the end of the FY).
Not a holding or subsidiary of a Public company.
Whose borrowings is less than or equal to Rs 1 crore throughout the entire FY.
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

CAUTIONARY_ANALYSIS = """
Objective: Search and analyze auditor reports strictly for instances of negligence, failure, or red flags in fulfilling professional responsibilities. ONLY report genuine cautionary points based on **explicit evidence in the report or annexed financials**. Do NOT infer or assume any issues without clear supporting evidence. DO NOT misinterpret standard or positive auditor actions as negative.

Examples of valid cautionary findings include:

1. Excessive reliance on management opinion without independent verification (must be clearly evident or stated).
2. Failure to highlight significant issues (e.g., extraordinary items or material misstatements) visible from the financials but not addressed in the audit opinion.
3. Missed or unreported fraud indicators (e.g., fictitious sales) that are reasonably inferable from annexed data or red flags.
4. Non-compliance with legal/regulatory mandates (e.g., CARO report omissions or deficiencies).
5. No qualified opinion or disclaimer issued despite conditions like negative net worth or going concern doubts.
6. Significant related party transactions (e.g., >25% of sales or >30% of advances) not addressed in audit remarks.
7. Failure to examine or disclose major contingent liabilities, provisions, or accounting estimates with significant financial impact.
8. Misleading or incomplete audit reports (e.g., vague scope, no mention of limitations, boilerplate language without disclosures).

Instructions:
- DO NOT fabricate red flags.
- DO NOT mark neutral or standard language as negative.
- ONLY highlight genuine, supported cautionary or negative points.
- Skip any section if no clear cautionary point is found.
- Be objective, accurate, and avoid assumptions.

If no valid negative point is found in a section, state clearly: “No cautionary point found in this area.”
"""

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

    if not md_text.strip():
        return jsonify({'error': 'Markdown file has no extractable text.'}), 400

    prompt = f"""
    As a Chartered Accountant, Analyse the following auditor's report markdown and provide insights in the following structured JSON format ONLY (no extra text), only read auditor's report text, not the financials or other sections.:

    1. "Qualified_opinion": Analyse and provide a detailed qualifications/qualified opinion paragraph (at least 100 words if present, else state "The Auditors have not provided any Qualification").
    2. "Emphasis_of_matter": Analyse the Emphasis of Matter paragraph(s) if present, else state "The Auditors have not drawn any attention to any Emphasis of Matter".
    3. "CARO_applicability": Based on the auditor's report and the following CARO applicability rules, determine if CARO 2020 is applicable. In the "reason" field, clearly state which specific CARO applicability criteria (from the keywords/rules below) were met or not met, and quote the relevant text or numbers from the report that support your conclusion.
    CARO Applicability Rules:
    {CARO_APPLICABLE_KEYWORDS}
    Respond in this JSON format:
    {{
      "is_applicable": true/false,
      "available_in_report": true/false,
      "reason": "State the exact CARO rule(s) or threshold(s) that apply, and quote the relevant supporting text or numbers from the auditor's report."
    }}
    4. "CARO_negative_points": Analyse and List only those CARO remarks with negative sentiment (prequisition) as a list of objects: {{ "rule": "...", "remarks": "..." }}. give me negative points if available, do not create positive and good information negative.
    5. "Cautionary_Analysis": '{CAUTIONARY_ANALYSIS}' - Analyse the auditor's report for any instances of negligence or failures in fulfilling professional responsibilities, and provide a list of cautionary points as strings.
    6. "Summary": '...(Summary of the auditor's report in concise paragraph, highlighting key points, qualifications, emphasis of matter, CARO applicability, and any cautionary points found.)'

    Auditor's Report Text:
    ```
    {md_text}
    ```

    Respond in the following JSON format:
    {{
      "Qualified_opinion": "...",
      "Emphasis_of_matter": "...",
      "CARO_applicability": {{
        "is_applicable": true/false,
        "available_in_report": true/false,
        "reason": "State the exact CARO rule(s) or threshold(s) that apply, and quote the relevant supporting text or numbers from the auditor's report."
      }},
      "CARO_negative_points": [
        {{"rule": "...", "remarks": "..."}},
        ...
      ],
      "Cautionary_Analysis": [
        "..."
      ]
    }}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        print("Gemini raw response:\n", response.text)

        json_start = response.text.find('{')
        json_end = response.text.rfind('}')
        if json_start == -1 or json_end == -1:
            raise ValueError("Gemini response did not include a valid JSON block.")

        json_text = response.text[json_start:json_end + 1]
        analysis_result = json.loads(json_text)

        # Ensure all required keys exist
        result = {
            "Qualified_opinion": analysis_result.get("Qualified_opinion", ""),
            "Emphasis_of_matter": analysis_result.get("Emphasis_of_matter", ""),
            "CARO_applicability": analysis_result.get("CARO_applicability", {
                "is_applicable": None,
                "available_in_report": None,
                "reason": ""
            }),
            "CARO_negative_points": analysis_result.get("CARO_negative_points", []),
            "Cautionary_Analysis": analysis_result.get("Cautionary_Analysis", []),
        }

        return result

    except Exception as e:
        print("Error in Gemini response processing:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': f"Gemini error: {str(e)}"}), 500
    
def check_director_compliance_rules(text):
    """
    Uses Gemini model to analyze the director's report text for compliance with updated COMPLIANCE_RULES.
    Returns a structured compliance result and conclusion.
    """
    try:
        # Build a detailed prompt for Gemini
        prompt = f"""
        You are a compliance expert. Carefully read the following director's report text and check for compliance with each of the rules listed below.
        if auditor's report has stated fraud instance in the company then director's report must have explanation on each instance of fraud otherwise no comments is required to be mentioned in the director's report.
        Voluntary Revision - S 131 should always be compliant.
        and a summary of overall compliance status should be provided at the end.
        For each rule, state:
        - "Compliant" if all required disclosures/keywords are present (even if phrased differently), Voluntary Revision should always compliant.
        - "Not Applicable" if company does not required to have this disclosure.
        - "Non-Compliant" if the disclosure is missing or insufficient.
        - In "Remarks", mention the matched keywords/phrases or what is missing, dont not include insignificient concerns.

        Rules to check (with keywords for reference):
        {json.dumps(COMPLIANCE_RULES, indent=2)}

        Director's Report Text:
        \"\"\"
        {text}
        \"\"\"
        Respond in the following JSON format:
        {{
        "results": 
            {{
            "rule": "...",
            "status": "Compliant" or "Non-Compliant",
            "remarks": "..."
            }},
        "conclusion": "Summary of overall compliance"
        }}

        "Summary of overall compliance" should be a short paragraph summarizing the compliance status of the report.
        """

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        print("Gemini compliance response:\n", response.text)

        json_start = response.text.find('{')
        json_end = response.text.rfind('}')
        if json_start == -1 or json_end == -1:
            raise ValueError("Gemini response did not include a valid JSON block.")

        json_text = response.text[json_start:json_end + 1]
        analysis = json.loads(json_text)

        return analysis

    except Exception as e:
        print("Error in Gemini compliance processing:", str(e))
        print(traceback.format_exc())
        return {
            "results": [],
            "conclusion": f"Gemini error: {str(e)}"
        }
    
def generate_automatic_ratio_analysis(markdown_content, ratio_formulas):
    """Generates response using AI to automatically calculate all possible ratios, and prints only the most critical missing information before the conclusion."""
    prompt = f"""
You are a financial analyst. Carefully analyze the following financial report (in Markdown format) and do the following:

Extract all available numerical data required for key financial ratios (specially ebit, ebitda, net sales, total assets, etc.) from the markdown content.:
Use ONLY the formulas provided below for all ratio calculations. Do NOT use any formula or definition not present in the list:
Net Sales (from operations)
Total Sales (including other income)
Net Income
Total Assets
Total Liabilities
Shareholders’ Equity
Current Assets
Current Liabilities
Inventory
EBIT
EBITDA
Average Trade Receivables
Number of Outstanding Shares (if available)`
Any other relevant figures
For each ratio in the list below, attempt to calculate it using the extracted data.
Use the exact formula provided.
Substitute the actual numbers from the markdown into the formula.
Show the calculation steps and the final value.
If any required data is missing or unclear, explicitly list what is missing for that ratio.
For each calculated ratio, provide:
The formula used (as provided below)
The calculation steps with actual numbers from the markdown
The final value
A short interpretation of what the ratio means for the business
Missing Information Section:
List up to 3 critical missing or unclear data points that prevented calculation.
Provide a clear, concise summary/conclusion at the end, ensuring that:
Revenue clarity is ensured, including after-tax figures.
If possible, compare with the previous year.
Highlight any mismatches or inconsistencies in financial data, particularly shareholder equity.
Rephrase unclear cost-related sections and remove unnecessary estimation notes.
Do not estimate or assume numbers not present in the markdown, and most importantly don't show not calculated ratios or values.

Financial Ratio Formulas (use these exactly):
{ratio_formulas}
MARKDOWN Content:
{markdown_content}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        if not response.parts:
            return f"Error: AI analysis failed. Reason: {response.prompt_feedback.block_reason.name if response.prompt_feedback.block_reason else 'No block reason provided.'}"
        return response.text.strip()
    except Exception as e:
        return f"Error: An unexpected error occurred while generating the analysis ({e})."

def clean_markdown_content(markdown: str) -> str:
    """
    Cleans the markdown content by removing garbage values, extra whitespace, and non-informative lines.
    - Removes lines with only special characters or random symbols.
    - Removes repeated empty lines.
    - Optionally, removes lines with very little alphanumeric content.
    """
    cleaned_lines = []
    for line in markdown.splitlines():
        # Remove lines that are only special characters or whitespace
        if not line.strip():
            continue
        # Remove lines with very little alphanumeric content (e.g., OCR noise)
        if len(re.sub(r'[^a-zA-Z0-9]', '', line)) < 2 and len(line.strip()) < 10:
            continue
        # Remove lines with only repeated special characters (e.g., "-----", "=====")
        if re.match(r'^([^\w\s])\1{2,}$', line.strip()):
            continue
        cleaned_lines.append(line)
    # Remove consecutive empty lines
    cleaned_markdown = "\n".join(cleaned_lines)
    cleaned_markdown = re.sub(r'\n{3,}', '\n\n', cleaned_markdown)
    return cleaned_markdown.strip()

def parse_pdf_with_paperless(pdf_path):
    if not os.path.isfile(pdf_path):
        return None, "File does not exist."

    if not pdf_path.lower().endswith(".pdf"):
        return None, "File is not a PDF."

    try:
        # Upload PDF to Paperless
        with open(pdf_path, "rb") as f:
            files = {
                "document": (os.path.basename(pdf_path), f.read(), "application/pdf")
            }
            res = requests.post(
                f"{PAPERLESS_URL}/api/documents/post_document/",
                headers=headers,
                files=files
            )

        if res.status_code != 200:
            return None, f"Upload failed: {res.status_code} - {res.text}"

        # Wait for Paperless to process the document
        time.sleep(50)

        # Search for the uploaded document by file name
        search_params = {"original_file_name": os.path.basename(pdf_path)}
        lookup = requests.get(f"{PAPERLESS_URL}/api/documents/", headers=headers, params=search_params)
        lookup.raise_for_status()

        results = sorted(
            lookup.json().get("results", []),
            key=lambda doc: doc.get("added", ""),
            reverse=True,
        )

        if not results:
            return None, "Uploaded document not found."

        # Get document ID
        latest_doc = results[0]
        doc_id = latest_doc["id"]

        # Poll for OCR content
        for _ in range(15):
            doc_info = requests.get(f"{PAPERLESS_URL}/api/documents/{doc_id}/", headers=headers).json()
            content = doc_info.get("content", "").strip()
            ocr_status = doc_info.get("ocr_status")

            if content:
                return content, None
            elif ocr_status == "failed":
                return None, "OCR failed."

            time.sleep(2)

        return None, "Timed out waiting for OCR content."

    except Exception as e:
        return None, f"Exception during Paperless processing: {e}"

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

    # Parse PDF using Paperless
    markdown_content, error = parse_pdf_with_paperless(pdf_file_path)

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

def generate_directors_report_summary(text):
    try:
        prompt = f"""
        Summarize the following director's report in a concise paragraph, highlighting the main points, key disclosures, business performace, and any significant events or statements. The summary should be suitable for a board or compliance officer to quickly understand the essence of the report.

        Director's Report Text:
        \"\"\"
        {text}
        \"\"\"
        Respond with only the summary text, no JSON or formatting.
        """
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        summary = response.text.strip()
        return summary
    except Exception as e:
        print("Error generating director's report summary:", str(e))
        print(traceback.format_exc())
        return "Summary generation failed."

@app.route('/api/summary-directors-report', methods=['POST'])
def summary_directors_report():
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

        summary = generate_directors_report_summary(md_text)
        return jsonify({'summary': summary}), 200

    except Exception as e:
        print("Unexpected error:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': f"Unexpected error: {e}"}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Markdown Generator Backend is running!"})

# --- User Registration, Login, and Profile with MySQL Database ---

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            cur.close()
            return jsonify({'error': 'User already exists'}), 409

        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                    (username, hashed_password, email))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        print("Registration error:", str(e))
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # <-- Use DictCursor
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    username = get_jwt_identity()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # <-- Use DictCursor
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()

    if not user:
        cur.close()
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'GET':
        cur.close()
        return jsonify({'username': user['username'], 'email': user['email']})

    if request.method == 'PUT':
        data = request.get_json()
        new_username = data.get('username', username)
        email = data.get('email', user['email'])

        # Prevent username change to an existing username
        if new_username != username:
            cur.execute("SELECT id FROM users WHERE username=%s", (new_username,))
            if cur.fetchone():
                cur.close()
                return jsonify({'error': 'Username already exists'}), 409

        cur.execute("UPDATE users SET username=%s, email=%s WHERE username=%s",
                    (new_username, email, username))
        mysql.connection.commit()
        cur.close()
        return jsonify({'username': new_username, 'email': email})

def gemini_summarize_text(text):
    """
    Uses Gemini model to summarize any long text into a concise paragraph.
    """
    try:
        prompt = f"""
        Write me a Formal Summary report of this text.
        Text:
        \"\"\"
        {text}
        \"\"\"
        To know me:
        - Director Financial
        - Important Ratios (e.g., \tCurrent Ratio, \tDebt-to-Equity Ratio, \tNet Profit, \tGross Profit)
        - Area of concerns (bad ratios)
        - Auditor report concerns (don not pick concern from director's report and only provide concerns from auditor's report)
        - Business performance
        - Variance reasons
        - Qualitative insights

        in short and points wise,
        thanks.
        """
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        summary = response.text.strip()
        return summary
    except Exception as e:
        print("Error generating summary:", str(e))
        print(traceback.format_exc())
        return "Summary generation failed."

@app.route('/api/summarize-text', methods=['POST'])
def summarize_text():
    """
    Summarize a long text using Gemini AI.
    Expects JSON: { "text": "your long text here" }
    Returns: { "summary": "..." }
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided.'}), 400

    long_text = data['text']
    if not long_text.strip():
        return jsonify({'error': 'Text is empty.'}), 400

    summary = gemini_summarize_text(long_text)
    return jsonify({'summary': summary}), 200

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    user_email = None
    if 'user' in session:
        user_email = session['user'].get('email')
    if not user_email:
        user_email = data.get('user')
    feedback_text = data.get('feedback', '').strip()

    if not user_email or not feedback_text:
        return jsonify({'error': 'User and feedback are required.'}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO feedback (user_email, feedback) VALUES (%s, %s)",
            (user_email, feedback_text)
        )
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("Feedback DB error:", str(e))
        return jsonify({'error': 'Failed to save feedback.'}), 500

    return jsonify({'message': 'Feedback submitted successfully.'}), 200

@app.route('/api/summarize-markdown', methods=['POST'])
def summarize_markdown():
    """
    Summarize markdown content in a very short, concise way.
    Expects JSON: { "markdown": "..." }
    Returns: { "summary": "..." }
    """
    data = request.get_json()
    markdown = data.get('markdown', '')
    if not markdown or not markdown.strip():
        return jsonify({'error': 'No markdown content provided.'}), 400

    try:
        prompt = f"""
        Summarize the following markdown content in 2-3 sentences, focusing only on the most important financial highlights and key points. Be extremely concise.

        Markdown Content:
        \"\"\"
        {markdown}
        \"\"\"
        Respond with only the summary text, no formatting.
        """
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        summary = response.text.strip()
        return jsonify({'summary': summary}), 200
    except Exception as e:
        print("Error generating markdown summary:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': 'Summary generation failed.'}), 500

def ai_extract_ratios_json(markdown_content, ratio_formulas):
    """
    Uses Gemini AI to extract and calculate all possible ratios from markdown,
    and returns a JSON object suitable for charting.
    """
    prompt = f"""
You are a financial analyst. Carefully analyze the following financial report (in Markdown format) and do the following:

Extract all available numerical data required for key financial ratios (especially ebit, ebitda, net sales, total assets, etc.) from the markdown content.
Use ONLY the formulas provided below for all ratio calculations. Do NOT use any formula or definition not present in the list.
For each ratio, attempt to calculate it for each year available (e.g., 2024, 2023).
Respond ONLY in this JSON format (no extra text):

{{
  "Current Ratio": {{"2024": value, "2023": value}},
  "Debt-to-Equity Ratio": {{"2024": value, "2023": value}},
  ...
}}

If a ratio or year cannot be calculated, omit it from the JSON.
Do not include explanations or extra text.

Financial Ratio Formulas (use these exactly):
{ratio_formulas}
MARKDOWN Content:
{markdown_content}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
            }
        )
        if not response.parts:
            return {}
        # Extract JSON from response
        json_start = response.text.find('{')
        json_end = response.text.rfind('}')
        if json_start == -1 or json_end == -1:
            return {}
        json_text = response.text[json_start:json_end + 1]
        return json.loads(json_text)
    except Exception as e:
        print("AI ratio extraction error:", e)
        return {}

def extract_expenses_from_markdown(markdown):
    """
    Extracts all expenses for all years from markdown.
    Returns: { year: { category: value, ... }, ... }
    """
    exp_regex = re.compile(r'Expenses\s*\((\d{4})\):\s*([^\n]+)', re.IGNORECASE)
    result = {}
    for match in exp_regex.finditer(markdown):
        year = match.group(1)
        cats = match.group(2).split(',')
        result[year] = {}
        for cat in cats:
            parts = cat.split('=')
            if len(parts) == 2:
                name = parts[0].strip()
                try:
                    value = float(parts[1].strip())
                    result[year][name] = value
                except ValueError:
                    continue
    return result

@app.route('/api/ai-ratios-graph', methods=['POST'])
def ai_ratios_graph():
    """
    Use AI to extract ratios from markdown and return JSON for frontend charting.
    Expects JSON: { "markdown": "..." }
    Returns: { "ratios": ..., "expenses": ... }
    """
    data = request.get_json()
    markdown = data.get('markdown', '')
    if not markdown or not markdown.strip():
        return jsonify({'error': 'No markdown content provided.'}), 400

    ratios = ai_extract_ratios_json(markdown, RATIO_FORMULAS)
    if not ratios:
        return jsonify({'error': 'No ratios could be extracted from markdown.'}), 400

    # Only keep ratios with at least 2 years for charting
    filtered_ratios = {k: v for k, v in ratios.items() if len(v) >= 2}
    if not filtered_ratios:
        return jsonify({'error': 'No valid ratios with both years found in markdown.'}), 400

    # Extract all expenses for all years
    expenses = extract_expenses_from_markdown(markdown)

    return jsonify({'ratios': filtered_ratios, 'expenses': expenses}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
