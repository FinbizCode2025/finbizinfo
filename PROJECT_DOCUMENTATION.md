# FinBiz Info - Financial Analysis & Intelligence Platform

## 📌 Project Overview
**FinBiz Info** is a comprehensive financial intelligence platform designed to automate the extraction, analysis, and interpretation of financial data from various sources. It specializes in processing PDF financial statements (Balance Sheets, P&L, Notes), integrating with Tally ERP, and providing AI-powered insights through a multi-agent orchestration system.

---

## 🚀 Key Features

### 1. **Financial Document Processing**
- **PDF Extraction**: Uses `PyMuPDF` (fitz) for high-performance text extraction from financial reports.
- **OCR Support**: Integrated OCR capabilities (formerly Tesseract, now moving towards GLM/Ollama-based OCR) for processing scanned documents.
- **Table Reconstruction**: Custom logic in `app.py` to cluster text spans by vertical and horizontal positions to reconstruct tabular data from PDFs.
- **Notes Selection**: Intelligent logic to identify and extract key metrics from "Notes to Accounts".

### 2. **Automated Financial Analysis**
- **40+ Financial Ratios**: Calculates a wide range of ratios across categories:
  - **Liquidity**: Current Ratio, Quick Ratio, Cash Ratio, Working Capital.
  - **Profitability**: Gross/Net/Operating Margins, ROA, ROE, EBITDA Margin.
  - **Solvency**: Debt-to-Equity, Interest Coverage, Assets-to-Liabilities.
  - **Efficiency**: Asset Turnover, Inventory/Receivables Turnover, DSO.
  - **DuPont Analysis**: 3-step breakdown of Return on Equity.
- **Heuristic Extraction**: Robust logic to find numeric candidates and map them to financial line items using fuzzy keyword matching.

### 3. **AI & Multi-Agent Orchestration**
- **Multi-Agent System**: A sophisticated execution flow using specialized agents:
  - **FinancialRatioAgent**: Focuses on calculating and interpreting ratios.
  - **DataValidationAgent**: Verifies the internal consistency of extracted data.
  - **QualityCheckAgent**: Assesses the reliability of the analysis results.
  - **FactCheckingAgent**: Cross-references findings against the source document.
- **RAG (Retrieval-Augmented Generation)**: Powered by `LangChain`, `FAISS` (vector store), and `Google Gemini`. Allows users to ask natural language questions about their financial documents.
- **LLM Extraction**: Uses `Kimi` (via `kimi_client.py`) and `Gemini` for advanced extraction of structured financial data from unstructured text.

### 4. **ERP & External Integrations**
- **Tally Integration**: Direct XML-based communication with Tally ERP (`localhost:9000`) to fetch real-time Balance Sheets.
- **Probe42 Service**: Integration with the Probe42 API to fetch official corporate data (CIN, Shareholders, Directors, Charges).
- **Tavily Search**: AI-powered web search integration for gathering additional market context.

### 5. **Data Management**
- **Database Architecture**: SQLite database managed via SQLAlchemy.
  - `Company`: Core company details (CIN, Name, Industry).
  - `Financials`: Historical financial performance records.
  - `Director`: Information on company leadership.
  - `Charge`: Documented financial charges/liens on company assets.

---

## 🛠️ Technology Stack & Tools

### **Backend (Python/Flask)**
- **Web Framework**: `Flask` (with `flask-cors` for cross-origin frontend requests).
- **Orchestration**: `LangChain` & `LangGraph` for managing complex LLM workflows and stateful agent interactions.
- **LLMs (Large Language Models)**:
  - **Google Gemini**: Primary model for RAG and general analysis.
  - **Kimi (Moonshot AI)**: Specialized extraction of balance sheet and P&L items using the `moonshot-v1-32k` model.
  - **Mistral**: Alternative LLM used for specific financial extraction tasks.
- **Vector Intelligence**:
  - `FAISS`: High-performance local vector store for document indexing.
  - `Sentence Transformers` / `Gemini Embeddings`: For generating semantic embeddings for RAG.
  - `Tiktoken`: Used for precise token measurement and cost tracking.
- **Data & Extraction**:
  - `PyMuPDF (fitz)`: Fast and accurate text/layout extraction from PDFs.
  - `Pytesseract` & `pdf2image`: Traditional OCR fallback for scanned documents.
  - `Pandas` & `NumPy`: For complex financial calculations and data structuring.
  - `SQLAlchemy`: ORM for managing the SQLite database (`finbiz.db`).
- **External Services**:
  - `Tavily`: AI search engine used by agents to find real-world market data and peer info.
  - `Probe42`: Corporate data API for retrieving official MCA (Ministry of Corporate Affairs) records.
  - `Tally ERP 9 / TallyPrime`: Integration via local XML server (Port 9000).

---

## 📂 Project Structure

```text
/anshu
├── be/                       # Backend Source Code
│   ├── app.py                # Main Flask entry point (Endpoints, PDF parsing, Ratio logic)
│   ├── agents.py             # Multi-agent specialized logic (Ratio, Validation, Quality, Fact-Check)
│   ├── financial_analyzer.py  # LangChain-based RAG system and Document Analysis
│   ├── kimi_client.py        # Integration with Moonshot's Kimi LLM
│   ├── tally_balance_sheet.py # XML connector for Tally ERP
│   ├── probe42_service.py    # Service layer for Probe42 corporate data API
│   ├── models.py             # Database Schema (Company, Financials, Directors, Charges)
│   ├── session_store.py      # Persistence for user sessions and document state
│   └── run_multi_agent_session.py # CLI tool to execute the agentic workflow on a session
├── fe/                       # Frontend Source Code (React/Vite)
│   ├── src/
│   │   ├── App.tsx           # Multi-functional Dashboard with routing
│   │   ├── Home.tsx          # Landing and file upload portal
│   │   ├── PeerComparison.jsx# Comparative analysis visualization
│   │   ├── components/       # UI Library (Chat, Tables, Charts, FileUpload)
│   │   └── context/          # State management (Auth, Theme)
│   └── tailwind.config.js    # Design system configuration
└── PROJECT_DOCUMENTATION.md  # You are here!
```

---

## 🧠 Core Logic & Algorithms

### 1. **Table Extraction Heuristics**
The system doesn't just read text; it reconstructs tables. 
- **Vertical Clustering**: Text spans are grouped into "rows" if their Y-coordinates are within a small threshold (`y_tolerance=4`).
- **Horizontal Mapping**: Columns are identified by analyzing the X-coordinates of text blocks, helping to distinguish between 'Particulars' and 'Numeric values'.

### 2. **Financial Ratio Engine**
Located primarily in `app.py` and `financial_analyzer.py`, this engine implements:
- **Safe Math**: All calculations use helper functions like `safe_div` and `safe_gt` to handle missing data or zeros gracefully without crashing.
- **Currency Normalization**: Input values like "1,23.45 Lakhs" or "2.5 Crores" are automatically converted to absolute units for calculation.
- **Benchmark-based Interpretation**: Ratios are not just numbers; they are compared against industry standards to provide qualitative labels (e.g., "Current Ratio > 2.0" → "Excellent").

### 3. **The Multi-Agent Workflow**
When a data integrity check is requested, `AgentOrchestrator` spawns:
1. **Verification**: `DataValidationAgent` checks if `Total Assets = Equity + Liabilities`.
2. **Analysis**: `FinancialRatioAgent` computes the 40+ metrics.
3. **Cross-Reference**: `FactCheckingAgent` finds the exact sentence in the PDF that supports a specific financial claim.
4. **Summary**: `QualityCheckAgent` provides a consolidated reliability score.

### 4. **Tally Connector**
Uses an `HTTP POST` with a custom-built `<ENVELOPE>` XML structure. It tells Tally to export the "Balance Sheet" report in XML format for a specific company, which is then parsed into the app's internal format.

---

## 🚦 Getting Started

1. **Environment Setup**:
   - Rename `.env.example` to `.env` and provide your API keys (Google, Probe42, etc.).
   - Run `pip install -r be/requirements.txt` for backend.
   - Run `npm install` in the `fe` directory for frontend.

2. **Execution**:
   - Start the backend: `python be/app.py`
   - Start the frontend: `npm run dev`
   - For Tally integration, ensure Tally is running with ODBC/XML enabled on port 9000.

---

## 📝 Authors & Credits
Developed as an advanced financial analysis solution for **FinBiz Code 2025**.
Target Company for Tally Operations: *Maestro Engineering Pvt. Ltd 2024-25*.
