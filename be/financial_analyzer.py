from typing import Dict, List, Optional, Any
from pathlib import Path
import re
import json
import os

"""
LangChain imports using the latest package structure.
"""
# Core functionality
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tracers import LangChainTracer
from langchain_core.callbacks import CallbackManager

# Document handling
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader

# Vector operations
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from config import Config

class FinancialAnalyzer:
    """Main class for financial document analysis using LangChain."""
    
    def __init__(self):
        self.config = Config()
        
        # Set up LangChain tracing
        if self.config.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = self.config.LANGCHAIN_ENDPOINT
            os.environ["LANGCHAIN_API_KEY"] = self.config.LANGCHAIN_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = self.config.LANGCHAIN_PROJECT
            
            tracer = LangChainTracer(
                project_name=self.config.LANGCHAIN_PROJECT
            )
            self.callback_manager = CallbackManager([tracer])
        else:
            self.callback_manager = None
            
        self.embeddings = self._initialize_embeddings()
        self.llm = self._initialize_llm()
        self.text_splitter = self._initialize_text_splitter()
        self.filepath = None
        self._chat_chain = None
        self._retriever = None  # Store the retriever at class level
        # Track token usage estimates (input/output/total)
        # These are best-effort estimates based on character counts when the LLM
        # client does not provide usage metadata.
        self.token_stats = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        # Per-request token tracking (most recent request)
        self.last_request = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "prompt_text": None,
            "completion_text": None,
            "usage": None,
        }

        # Director's Report Compliance Checkpoints
        self.DIRECTOR_COMPLIANCE_RULES = [
            {"rule": "Financial Highlights & Change Business", "keywords": ["financial highlights", "change in the nature of business"]},
            {"rule": "Web Link of Annual Return", "keywords": ["web address", "annual return", "section 92"]},
            {"rule": "Number Of Board Meetings", "keywords": ["board meetings held", "date of board meetings", "committee meeting", "director attendance"]},
            {"rule": "Director Responsibility Statement", "keywords": ["directors' responsibility", "accounting standards", "internal financial control", "going concern"]},
            {"rule": "Fraud Reporting by Auditor", "keywords": ["fraud reported by auditor", "section 143(12)"]},
            {"rule": "Declaration by Independent Director", "keywords": ["independent director", "declaration of independence"]},
            {"rule": "Risk Management Policy", "keywords": ["risk management policy", "elements of risk"]},
            {"rule": "Explanation on Auditor Qualification", "keywords": ["auditor qualification", "auditor remarks", "board comments on audit"]},
            {"rule": "Inter-Corporate Loans & Investments", "keywords": ["section 186", "loan", "investment", "guarantee"]},
            {"rule": "Related Party Transactions", "keywords": ["related party transaction", "section 188", "form AOC-2"]},
            {"rule": "State of Company’s Affairs", "keywords": ["state of affairs", "company’s performance", "business overview"]},
            {"rule": "Transfer to Reserves", "keywords": ["transfer to reserve", "general reserve"]},
            {"rule": "Dividends", "keywords": ["dividend recommended", "rate of dividend"]},
            {"rule": "Post Balance Sheet Events", "keywords": ["material changes and commitments", "post balance sheet events"]},
            {"rule": "Energy, Tech, & Foreign Exchange", "keywords": ["conservation of energy", "technology absorption", "foreign exchange earnings and outgo"]},
            {"rule": "Auditor Appointment/Reappointment", "keywords": ["auditor appointment", "auditor reappointment"]},
            {"rule": "Subsidiaries, JVs, Associates", "keywords": ["subsidiary", "joint venture", "associate company performance"]},
            {"rule": "Directors/KMP Changes", "keywords": ["appointment of director", "resignation of director", "appointment of KMP"]},
            {"rule": "Sexual Harassment Committee", "keywords": ["sexual harassment of women at workplace", "prevention of sexual harassment"]},
            {"rule": "Internal Financial Controls", "keywords": ["internal financial controls", "adequacy of internal controls"]},
            {"rule": "Details of Deposits", "keywords": ["deposits accepted", "unpaid deposits"]},
            {"rule": "Cost Records Compliance", "keywords": ["cost records", "maintenance of cost records"]},
            {"rule": "Insolvency Proceedings", "keywords": ["insolvency and bankruptcy code", "IBC application"]},
        ]

    def _parse_compliance_answer(self, answer: str) -> Dict[str, str]:
        """Parses the LLM's free-text answer into a structured dictionary."""
        answer_lower = answer.lower()
        status = "Not Found"
        if "complied" in answer_lower:
            status = "Complied"
        elif "not complied" in answer_lower:
            status = "Not Complied"
        
        # Extract reasoning by splitting at "Reasoning:" and cleaning up.
        reasoning_part = re.split(r"reasoning:", answer, flags=re.IGNORECASE)
        reasoning = reasoning_part[1].strip() if len(reasoning_part) > 1 else "No specific reasoning provided."
        
        return {
            "status": status,
            "reasoning": reasoning
        }

    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        """Initialize the embedding model."""
        return HuggingFaceEmbeddings(model_name=self.config.EMBEDDING_MODEL)

    def _initialize_llm(self) -> GoogleGenerativeAI:
        """Initialize the language model."""
        if not self.config.GOOGLE_API_KEY:
            raise ValueError("Google API key not set. Please set the API key first.")
            
        kwargs = {
            "model": self.config.LLM_MODEL,
            "google_api_key": self.config.GOOGLE_API_KEY,
            "temperature": 0.2
        }
        
        if self.callback_manager:
            kwargs["callbacks"] = self.callback_manager
            
        return GoogleGenerativeAI(**kwargs)

    def _initialize_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Initialize the text splitter with financial document optimized settings."""
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens from text length using a conservative chars-per-token heuristic.

        This is a rough estimate: 4 characters per token (English) is commonly used.
        If a real tokenizer is available in the environment, replace this with an
        actual token counter (e.g., tiktoken.encode).
        """
        # Prefer tiktoken if it's available for accurate token counts
        try:
            import tiktoken
            # Map some common model names to tiktoken encoders; fallback to cl100k_base
            model_name = getattr(self.config, 'LLM_MODEL', None) or 'gpt-4'
            try:
                enc = tiktoken.encoding_for_model(model_name)
            except Exception:
                try:
                    enc = tiktoken.get_encoding('cl100k_base')
                except Exception:
                    enc = None

            if enc and text:
                return len(enc.encode(text))
        except Exception:
            pass

        # Fallback heuristic (chars per token)
        try:
            if text is None:
                return 0
            l = len(text)
            return max(0, int(l / 4))
        except Exception:
            return 0

    def set_last_request_tokens(self, prompt_tokens: int, completion_tokens: int, prompt_text: str = None, completion_text: str = None, usage: dict = None):
        """Record per-request token counts and optional text/usage metadata."""
        try:
            self.last_request['prompt_tokens'] = int(prompt_tokens or 0)
            self.last_request['completion_tokens'] = int(completion_tokens or 0)
            self.last_request['total_tokens'] = int((prompt_tokens or 0) + (completion_tokens or 0))
            if prompt_text is not None:
                self.last_request['prompt_text'] = prompt_text
            if completion_text is not None: 
                self.last_request['completion_text'] = completion_text
            if usage is not None:
                self.last_request['usage'] = usage
        except Exception:
            pass

    def refresh_llm(self):
        """Reinitialize the LLM with current API key."""
        self.llm = self._initialize_llm()

    def process_document(self, file_path: str) -> tuple[FAISS, List[Document]]:
        """
        Process a financial document and create a vector store.
        
        Args:
            file_path: Path to the PDF document
            
        Returns:
            tuple: (vector_store, documents)
        """
        print(f"Processing document: {file_path}")
        self.filepath = file_path  # Store the filepath for later use
        
        try:
            loader = PyMuPDFLoader(file_path)
            print("Document loaded successfully")
            documents = loader.load()
            print(f"Loaded {len(documents)} pages from document")
            
            # Add source metadata
            print("Adding source metadata...")
            for doc in documents:
                doc.metadata["source"] = Path(file_path).name
            
            print("Splitting text...")
            texts = self.text_splitter.split_documents(documents)
            print(f"Created {len(texts)} text chunks")
            
            print("Creating vector store...")
            vectorstore = FAISS.from_documents(texts, self.embeddings)
            print("Vector store created successfully")
            
            return vectorstore, documents
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            raise

    def create_chain(self, vectorstore: FAISS):
        """Create a retrieval chain for the document using the new LangChain API."""
        
        # Define the financial analysis prompt template
        financial_prompt = PromptTemplate(
            template="""You are an expert financial analyst. Use the provided context to answer questions about the financial document.
            Focus on accuracy, quantitative analysis, and clear explanations.

            Context: {context}
            Question: {question}

            Provide your analysis in this structure:
            1. Direct answer
            2. Key financial metrics and data points
            3. Analysis and implications
            4. Recommendations (if applicable)

            Answer:""",
            input_variables=["context", "question"]
        )

        # Create a retriever with similarity search
        self._retriever = vectorstore.as_retriever(
            search_kwargs={"k": 6}
        )

        # Format retriever output
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Build the RAG chain using the new API
        rag_chain = (
            {
                "context": self._retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | financial_prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

    def analyze(self, chain, query: str) -> Dict[str, Any]:
        """Run an analysis query through the chain."""
        try:
            print(f"Starting analysis with query: {query}")
            
            if not self._retriever:
                raise ValueError("Retriever not initialized. Please process a document first.")
            
            print("Getting relevant documents...")
            docs = self._retriever.invoke(query)
            if isinstance(docs, list):
                print(f"Found {len(docs)} relevant documents")
            else:
                # For newer versions that might return a different structure
                docs = self._retriever.get_relevant_documents(query)
                print(f"Found {len(docs)} relevant documents (legacy method)")
            
            # Run the query through the chain
            print("Running query through chain...")
            # Estimate input tokens for accounting
            estimated_in = self._estimate_tokens(query)
            result = chain.invoke(query)
            # Estimate output tokens from result (if string) or from returned dict
            est_out = 0
            if isinstance(result, str):
                est_out = self._estimate_tokens(result)
            elif isinstance(result, dict):
                # try to extract textual 'answer' if present
                ans = result.get('answer') if isinstance(result.get('answer'), str) else None
                if ans:
                    est_out = self._estimate_tokens(ans)

            # Update cumulative token stats
            try:
                # Record per-request token usage
                try:
                    # result may be a string or dict
                    completion_text = result if isinstance(result, str) else (result.get('answer') if isinstance(result, dict) else None)
                    self.set_last_request_tokens(estimated_in, est_out, prompt_text=query, completion_text=completion_text)
                except Exception:
                    pass

                self.token_stats['input_tokens'] += estimated_in
                self.token_stats['output_tokens'] += est_out
                self.token_stats['total_tokens'] = self.token_stats['input_tokens'] + self.token_stats['output_tokens']
            except Exception:
                pass

            print(f"Query result: {result}")
            
            # Extract page numbers from source documents
            sources = []
            for doc in docs:
                source = {
                    "page": doc.metadata.get("page", 0) + 1,
                    "content": doc.page_content[:200] + "..."  # Preview
                }
                sources.append(source)
            
            return {
                "answer": result,
                "sources": sources
            }
        except ChatGoogleGenerativeAIError as e:
            print(f"API Key / Permission Error in analyze: {str(e)}")
            # Return a specific error for API key issues
            return {"error": f"API Key Error: {str(e)}"}
        except Exception as e:
            print(f"Error in analyze method: {str(e)}")
            # Try alternative retrieval method if first one fails
            try:
                print("Attempting alternative document retrieval method...")
                docs = self._retriever.get_docs_and_similarities(query)[0]
                print(f"Found {len(docs)} documents using alternative method")
                
                # Run the query through the chain
                result = chain.invoke(query)
                
                # Extract page numbers from source documents
                sources = []
                for doc in docs:
                    source = {
                        "page": doc.metadata.get("page", 0) + 1,
                        "content": doc.page_content[:200] + "..."  # Preview
                    }
                    sources.append(source)
                
                return {
                    "answer": result,
                    "sources": sources
                }
            except Exception as e2:
                print(f"Error in alternative method: {str(e2)}")
                return {"error": f"Failed to retrieve documents: {str(e)}"}

    def save_analysis_state(self, session_id: str, vectorstore: FAISS, documents: List[Document]):
        """Save the analysis state for the session."""
        session_dir = Config.SESSIONS_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Save vectorstore
        vectorstore.save_local(str(session_dir / "vectorstore"))
        
        # Save document metadata
        docs_metadata = [{
            "page": doc.metadata.get("page", 0),
            "source": doc.metadata.get("source", ""),
            "content_preview": doc.page_content[:100]
        } for doc in documents]
        
        with open(session_dir / "metadata.json", "w") as f:
            json.dump(docs_metadata, f)

    def load_analysis_state(self, session_id: str) -> tuple[Optional[FAISS], List[Dict]]:
        """Load the analysis state for the session."""
        session_dir = Config.SESSIONS_DIR / session_id
        
        if not session_dir.exists():
            return None, []
        
        try:
            vectorstore = FAISS.load_local(str(session_dir / "vectorstore"), self.embeddings)
            
            with open(session_dir / "metadata.json", "r") as f:
                docs_metadata = json.load(f)
            
            return vectorstore, docs_metadata
        except Exception as e:
            print(f"Error loading analysis state: {e}")
            return None, []

    def _format_ratios_as_table(self, ratios: Dict[str, Any]) -> str:
        """Format financial ratios as a human-readable table.
        
        Handles both old flat structure and new nested category structure.
        Organizes ratios by category and presents them in a clean tabular format.
        """
        # Handle new nested structure
        if any(key in ratios for key in ['liquidity_ratios', 'profitability_ratios', 'solvency_ratios', 'efficiency_ratios']):
            return self._format_organized_ratios_as_table(ratios)
        
        # Fallback for old flat structure
        categories = {
            "Liquidity Ratios": [
                ("Current Ratio", "current_ratio"),
                ("Quick Ratio", "quick_ratio"),
                ("Cash Ratio", "cash_ratio"),
            ],
            "Profitability Ratios": [
                ("Gross Profit", "gross_profit"),
                ("Gross Margin (%)", "gross_margin"),
                ("Operating Profit", "operating_profit"),
                ("Operating Margin (%)", "operating_margin"),
                ("Net Margin (%)", "net_margin"),
                ("Return on Assets (ROA) (%)", "roa"),
                ("Return on Equity (ROE) (%)", "roe"),
            ],
            "Leverage / Solvency Ratios": [
                ("Debt Ratio", "debt_ratio"),
                ("Debt to Equity Ratio", "debt_to_equity"),
                ("Equity Ratio", "equity_ratio"),
                ("Interest Coverage Ratio", "interest_coverage"),
            ],
            "Efficiency Ratios": [
                ("Asset Turnover", "asset_turnover"),
                ("Inventory Turnover", "inventory_turnover"),
                ("Receivables Turnover", "receivables_turnover"),
                ("Payables Turnover", "payables_turnover"),
            ],
        }

        lines = []
        lines.append("=" * 80)
        lines.append("FINANCIAL RATIOS ANALYSIS".center(80))
        lines.append("=" * 80)
        lines.append("")

        for category, ratio_list in categories.items():
            lines.append(f"\n{category}:")
            lines.append("-" * 80)
            lines.append(f"{'Metric':<40} {'Value':<30} {'Status':<10}")
            lines.append("-" * 80)

            for label, key in ratio_list:
                value = ratios.get(key)
                
                if value is None:
                    value_str = "N/A"
                    status = "—"
                else:
                    # Format the value appropriately
                    if key in ["gross_margin", "operating_margin", "net_margin", "roa", "roe"]:
                        # For percentages, multiply by 100
                        value_str = f"{value * 100:.2f}%"
                    else:
                        value_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                    
                    # Provide status / interpretation
                    if key == "current_ratio":
                        status = "✓ Good" if 1.5 <= value <= 3.0 else ("⚠ Warning" if value < 1.0 else "→ Review")
                    elif key == "quick_ratio":
                        status = "✓ Good" if value >= 1.0 else "⚠ Warning"
                    elif key == "debt_to_equity":
                        status = "✓ Good" if value <= 1.5 else "⚠ High"
                    elif key == "roe":
                        status = "✓ Good" if value >= 0.15 else "→ Monitor"
                    elif key == "roa":
                        status = "✓ Good" if value >= 0.05 else "→ Monitor"
                    else:
                        status = "—"

                lines.append(f"{label:<40} {value_str:<30} {status:<10}")

            lines.append("")

        # Add extracted numbers as a footer reference
        extracted = ratios.get("_extracted_numbers", {})
        if extracted and any(v is not None for v in extracted.values()):
            lines.append("\n" + "=" * 80)
            lines.append("BASE FINANCIAL DATA (Extracted from Document)".center(80))
            lines.append("=" * 80)
            lines.append(f"{'Item':<40} {'Amount':<40}")
            lines.append("-" * 80)

            for key, value in extracted.items():
                if value is not None and key != "_extracted_numbers":
                    display_key = key.replace("_", " ").title()
                    if isinstance(value, (int, float)):
                        value_str = f"{value:,.2f}"
                    else:
                        value_str = str(value)
                    lines.append(f"{display_key:<40} {value_str:<40}")

        lines.append("=" * 80)
        lines.append("")

        return "\n".join(lines)

    def _format_organized_ratios_as_table(self, ratios: Dict[str, Any]) -> str:
        """Format organized category ratios as a human-readable table."""
        lines = []
        lines.append("=" * 80)
        lines.append("FINANCIAL RATIOS ANALYSIS".center(80))
        lines.append("=" * 80)
        lines.append("")

        category_metadata = {
            'liquidity_ratios': {
                'display_name': 'Liquidity Ratios',
                'metrics': {
                    'current_ratio': ('Current Ratio', 'ratio', 0.5, 3.0),
                    'quick_ratio': ('Quick Ratio', 'ratio', 1.0, 2.0),
                    'cash_ratio': ('Cash Ratio', 'ratio', 0.2, 1.0),
                    'working_capital': ('Working Capital', 'amount', None, None),
                }
            },
            'profitability_ratios': {
                'display_name': 'Profitability Ratios',
                'metrics': {
                    'gross_profit': ('Gross Profit', 'amount', None, None),
                    'gross_margin': ('Gross Margin', 'percentage', 0.2, 0.5),
                    'operating_profit': ('Operating Profit', 'amount', None, None),
                    'operating_margin': ('Operating Margin', 'percentage', 0.1, 0.3),
                    'net_profit': ('Net Profit', 'amount', None, None),
                    'net_margin': ('Net Margin', 'percentage', 0.05, 0.2),
                    'return_on_assets': ('Return on Assets (ROA)', 'percentage', 0.05, 0.2),
                    'return_on_equity': ('Return on Equity (ROE)', 'percentage', 0.1, 0.3),
                }
            },
            'solvency_ratios': {
                'display_name': 'Solvency/Leverage Ratios',
                'metrics': {
                    'debt_ratio': ('Debt Ratio', 'ratio', 0.0, 0.6),
                    'equity_ratio': ('Equity Ratio', 'ratio', 0.4, 1.0),
                    'debt_to_equity': ('Debt to Equity Ratio', 'ratio', 0.0, 1.5),
                    'equity_to_debt': ('Equity to Debt Ratio', 'ratio', 0.67, 10.0),
                    'interest_coverage': ('Interest Coverage Ratio', 'ratio', 2.5, 10.0),
                    'debt_service_coverage': ('Debt Service Coverage', 'ratio', 1.0, 5.0),
                }
            },
            'efficiency_ratios': {
                'display_name': 'Efficiency/Activity Ratios',
                'metrics': {
                    'asset_turnover': ('Asset Turnover', 'ratio', 0.5, 3.0),
                    'inventory_turnover': ('Inventory Turnover', 'ratio', 2.0, 20.0),
                    'receivables_turnover': ('Receivables Turnover', 'ratio', 4.0, 12.0),
                    'payables_turnover': ('Payables Turnover', 'ratio', 4.0, 12.0),
                    'days_sales_outstanding': ('Days Sales Outstanding', 'days', 20.0, 60.0),
                    'inventory_holding_period': ('Inventory Holding Period', 'days', 20.0, 100.0),
                }
            }
        }

        for category_key in ['liquidity_ratios', 'profitability_ratios', 'solvency_ratios', 'efficiency_ratios']:
            if category_key not in ratios:
                continue

            category_data = ratios[category_key]
            if not category_data or all(v is None for v in category_data.values()):
                continue

            metadata = category_metadata[category_key]
            lines.append(f"\n{metadata['display_name']}:")
            lines.append("-" * 80)
            lines.append(f"{'Metric':<40} {'Value':<30} {'Status':<10}")
            lines.append("-" * 80)

            for metric_key, (label, val_type, good_min, good_max) in metadata['metrics'].items():
                value = category_data.get(metric_key)

                if value is None:
                    value_str = "N/A"
                    status = "—"
                else:
                    # Format based on type
                    if val_type == 'percentage':
                        value_str = f"{value * 100:.2f}%"
                    elif val_type == 'days':
                        value_str = f"{value:.1f} days"
                    elif val_type == 'amount':
                        value_str = f"{value:,.2f}"
                    else:  # ratio
                        value_str = f"{value:.4f}"

                    # Determine status
                    if good_min is not None and good_max is not None:
                        if good_min <= value <= good_max:
                            status = "✓ Good"
                        elif value < good_min:
                            status = "⚠ Low"
                        else:
                            status = "⚠ High"
                    else:
                        status = "—"

                lines.append(f"{label:<40} {value_str:<30} {status:<10}")

            lines.append("")

        # Add extracted numbers as a footer reference
        extracted = ratios.get("_extracted_numbers", {})
        if extracted and any(v is not None for v in extracted.values()):
            lines.append("\n" + "=" * 80)
            lines.append("BASE FINANCIAL DATA (Extracted from Document)".center(80))
            lines.append("=" * 80)
            lines.append(f"{'Item':<40} {'Amount':<40}")
            lines.append("-" * 80)

            for key, value in extracted.items():
                if value is not None and key != "_extracted_numbers":
                    display_key = key.replace("_", " ").title()
                    if isinstance(value, (int, float)):
                        value_str = f"{value:,.2f}"
                    else:
                        value_str = str(value)
                    lines.append(f"{display_key:<40} {value_str:<40}")

        lines.append("=" * 80)
        lines.append("")

        return "\n".join(lines)

    def get_section_analysis(self, chain, section_type: str) -> Dict[str, Any]:
        """Get analysis for specific sections of the financial document."""
        SECTION_PROMPTS = {
            "financial_ratios": """Analyze all financial ratios in the document. Include:
                1. Profitability ratios
                2. Liquidity ratios
                3. Solvency ratios
                4. Efficiency ratios
                Provide calculations, interpretations, and industry comparisons where possible.""",
            
            "compliance": """Review the document for compliance aspects. Cover:
                1. Regulatory compliance status
                2. Any violations or concerns
                3. Required disclosures
                4. Recommendations for improvement""",
            
            "auditor_report": """Analyze the auditor's report in detail. Your analysis should be structured and cover the following points:
                1.  **Audit Opinion**: State the type of opinion issued (e.g., Unqualified, Qualified, Adverse, Disclaimer of Opinion).
                2.  **Basis for Opinion**: Briefly summarize the basis for the auditor's opinion, especially if it is not unqualified.
                3.  **Key Audit Matters (KAMs)**: Summarize the most significant matters communicated to those charged with governance.
                4.  **Emphasis of Matter & Other Matter Paragraphs**: Identify and explain any 'Emphasis of Matter' or 'Other Matter' paragraphs.
                5.  **Red Flags & Cautionary Analysis**: Highlight any potential red flags, inconsistencies, or areas of concern mentioned by the auditor. This includes any cautionary language used.
                6.  **Auditor's Key Findings and Recommendations**: List any specific findings, qualifications, or recommendations made by the auditor for management.
                """,
            
            "director_report": """Summarize the director's report. Focus on:
                1. Strategic overview
                2. Key business developments
                3. Future outlook
                4. Major decisions and their rationale""",
            
            "risk_analysis": """Identify and analyze key risks. Include:
                1. Financial risks
                2. Operational risks
                3. Market risks
                4. Risk mitigation strategies"""
        }
        
        prompt = SECTION_PROMPTS.get(section_type)
        if not prompt:
            return {"error": "Invalid section type"}
            
        # For financial ratios, prefer a deterministic extractor + calculator
        if section_type == "financial_ratios":
            try:
                # Try to gather relevant documents (balance sheet / income statement)
                if not self._retriever:
                    raise ValueError("Retriever not initialized. Please process a document first.")

                keywords = [
                    "balance sheet",
                    "statement of financial position",
                    "statement of profit and loss",
                    "income statement",
                    "profit and loss",
                    "statement of profit",
                    "notes to accounts",
                    "financial statements",
                ]

                collected = []
                for kw in keywords:
                    try:
                        docs = self._retriever.get_relevant_documents(kw)
                    except Exception:
                        try:
                            docs = self._retriever.invoke(kw)
                        except Exception:
                            docs = []

                    if isinstance(docs, list):
                        collected.extend(docs)

                # Fallback: if no docs found, use the retriever to run a general search
                if not collected:
                    try:
                        collected = self._retriever.get_relevant_documents("")
                    except Exception:
                        collected = []

                # Combine the text content for extraction
                combined_text = "\n\n".join([d.page_content for d in collected]) if collected else ""

                # If we still have no text, fall back to LLM analysis
                if not combined_text.strip():
                    return self.analyze(chain, prompt)

                ratios = self.calculate_financial_ratios_from_text(combined_text)

                # Return BOTH formatted table and structured data
                # The frontend will use structured data for table display
                answer = self._format_ratios_as_table(ratios)
                return {
                    "answer": answer,
                    "ratios": ratios.get("ratios", ratios),
                    "_extracted_numbers": ratios.get("_extracted_numbers", {}),
                    "status": "success"
                }
            except Exception as e:
                # If anything fails, fallback to LLM prompt to avoid total failure
                print(f"Deterministic ratio extraction failed: {e}")
                return self.analyze(chain, prompt)

        return self.analyze(chain, prompt)

    def _find_amount(self, text: str, keywords: list[str]) -> Optional[float]:
        """Search the text for a numeric amount associated with any of the keywords.

        Returns the first matched numeric value (float) or None.
        """
        # Normalize common currency symbols and non-breaking spaces
        norm_text = text.replace('\u00A0', ' ')
        # Search for patterns like (1,234.56) as negative, or -1,234.56, or ₹1,234
        for kw in keywords:
            # Try to find a line containing the keyword and a number (handles currency symbols and parentheses)
            pattern = rf"{re.escape(kw)}[^\n\r\d\-\(\)]*([\(\-]?[\$₹Rs\.\s]*[\d,]+(?:\.\d+)?[\)]?)"
            m = re.search(pattern, norm_text, flags=re.IGNORECASE)
            if m:
                raw = m.group(1)
                # Remove currency symbols and spaces
                cleaned = re.sub(r"[\$₹Rs\.\s]", '', raw)
                # Handle parentheses negative
                if cleaned.startswith('(') and cleaned.endswith(')'):
                    cleaned = '-' + cleaned[1:-1]
                cleaned = cleaned.replace(',', '')
                try:
                    return float(cleaned)
                except Exception:
                    continue

        # As a secondary approach, search line-by-line for keyword in line
        lines = norm_text.splitlines()
        for i, line in enumerate(lines):
            for kw in keywords:
                if kw.lower() in line.lower():
                    m = re.search(r"([\(\-]?[\$₹Rs\.\s]*[\d,]+(?:\.\d+)?[\)]?)", line)
                    if m:
                        raw = m.group(1)
                        cleaned = re.sub(r"[\$₹Rs\.\s]", '', raw)
                        if cleaned.startswith('(') and cleaned.endswith(')'):
                            cleaned = '-' + cleaned[1:-1]
                        try:
                            return float(cleaned.replace(',', ''))
                        except Exception:
                            pass
                    # Look at following lines (values sometimes on next line)
                    if i + 1 < len(lines):
                        m2 = re.search(r"([\(\-]?[\$₹Rs\.\s]*[\d,]+(?:\.\d+)?[\)]?)", lines[i+1])
                        if m2:
                            raw2 = m2.group(1)
                            cleaned2 = re.sub(r"[\$₹Rs\.\s]", '', raw2)
                            if cleaned2.startswith('(') and cleaned2.endswith(')'):
                                cleaned2 = '-' + cleaned2[1:-1]
                            try:
                                return float(cleaned2.replace(',', ''))
                            except Exception:
                                pass

        return None

    def _extract_financial_numbers(self, text: str) -> Dict[str, Optional[float]]:
        """Attempt to extract core financial line-items from the combined text.

        The extraction is heuristic-based and looks for common labels; it returns
        a dict of possible values (None when not found).
        """
        t = text
        values: Dict[str, Optional[float]] = {}

        values['current_assets'] = self._find_amount(t, [
            'total current assets', 'current assets', 'total current assets and loans', 'currents assets'
        ])

        values['inventory'] = self._find_amount(t, [
            'inventory', 'stock', 'inventories'
        ])

        values['cash_and_cash_equivalents'] = self._find_amount(t, [
            'cash and cash equivalents', 'cash and cash equivalents', 'cash & cash equivalents', 'cash and bank balances', 'cash in hand'
        ])

        values['current_liabilities'] = self._find_amount(t, [
            'total current liabilities', 'current liabilities', 'liabilities- current', 'current portion of'
        ])

        values['total_assets'] = self._find_amount(t, [
            'total assets', 'assets total', 'total non-current and current assets'
        ])

        values['total_equity'] = self._find_amount(t, [
            'total equity', 'shareholders funds', "total equity and liabilities", 'equity and liabilities', 'total shareholders\' funds'
        ])

        values['total_liabilities'] = self._find_amount(t, [
            'total liabilities', 'liabilities total'
        ])

        values['revenue'] = self._find_amount(t, [
            'total revenue', 'revenue', 'net sales', 'sales', 'turnover'
        ])

        values['cogs'] = self._find_amount(t, [
            'cost of goods sold', 'cost of sales', 'cost of materials', 'direct expenses', 'cost of revenue'
        ])

        values['gross_profit'] = self._find_amount(t, [
            'gross profit', 'gross margin'
        ])

        values['operating_income'] = self._find_amount(t, [
            'operating profit', 'operating income', 'profit from operations'
        ])

        values['ebit'] = self._find_amount(t, [
            'profit before finance costs and tax', 'ebit', 'earnings before interest and tax', 'profit before interest and tax'
        ])

        values['interest_expense'] = self._find_amount(t, [
            'finance costs', 'interest expense', 'interest paid'
        ])

        values['net_income'] = self._find_amount(t, [
            'profit for the year', 'net profit', 'profit after tax', 'net income'
        ])

        values['receivables'] = self._find_amount(t, [
            'trade receivables', 'receivables', 'accounts receivable', 'debtors'
        ])

        values['payables'] = self._find_amount(t, [
            'trade payables', 'payables', 'accounts payable', 'creditors'
        ])

        return values

    def calculate_financial_ratios_from_text(self, text: str) -> Dict[str, Optional[float]]:
        """Deterministically calculate a comprehensive set of financial ratios from text.

        Organizes ratios into categories:
        - Liquidity: current_ratio, quick_ratio, cash_ratio, working_capital
        - Profitability: margins, returns
        - Solvency/Leverage: debt ratios, equity ratios
        - Efficiency: turnover ratios
        - Activity: receivables, inventory, payables metrics

        Returns a dict with organized ratio categories.
        """
        nums = self._extract_financial_numbers(text)

        def safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
            try:
                if a is None or b is None:
                    return None
                if b == 0:
                    return None
                return a / b
            except Exception:
                return None

        ratios_raw: Dict[str, Optional[float]] = {}

        # ============ LIQUIDITY RATIOS ============
        ratios_raw['current_ratio'] = safe_div(nums.get('current_assets'), nums.get('current_liabilities'))
        quick_assets = None
        if nums.get('current_assets') is not None and nums.get('inventory') is not None:
            quick_assets = nums['current_assets'] - nums['inventory']
        ratios_raw['quick_ratio'] = safe_div(quick_assets, nums.get('current_liabilities'))
        ratios_raw['cash_ratio'] = safe_div(nums.get('cash_and_cash_equivalents'), nums.get('current_liabilities'))
        
        # Working capital
        working_capital = None
        if nums.get('current_assets') is not None and nums.get('current_liabilities') is not None:
            working_capital = nums['current_assets'] - nums['current_liabilities']
        ratios_raw['working_capital'] = working_capital

        # ============ PROFITABILITY RATIOS ============
        # Gross profit and margin
        if nums.get('gross_profit') is not None:
            ratios_raw['gross_profit'] = nums.get('gross_profit')
        elif nums.get('revenue') is not None and nums.get('cogs') is not None:
            ratios_raw['gross_profit'] = nums['revenue'] - nums['cogs']
        else:
            ratios_raw['gross_profit'] = None

        ratios_raw['gross_margin'] = None
        if nums.get('revenue') is not None and nums.get('revenue') != 0:
            if ratios_raw.get('gross_profit') is not None:
                ratios_raw['gross_margin'] = ratios_raw['gross_profit'] / nums['revenue']

        # Operating profit and margin
        if nums.get('operating_income') is not None:
            ratios_raw['operating_profit'] = nums.get('operating_income')
        else:
            ratios_raw['operating_profit'] = None

        ratios_raw['operating_margin'] = safe_div(ratios_raw.get('operating_profit'), nums.get('revenue'))

        # Net profit and margin
        ratios_raw['net_profit'] = nums.get('net_income')
        ratios_raw['net_margin'] = safe_div(nums.get('net_income'), nums.get('revenue'))

        # Returns on assets and equity
        ratios_raw['return_on_assets'] = safe_div(nums.get('net_income'), nums.get('total_assets'))
        ratios_raw['return_on_equity'] = safe_div(nums.get('net_income'), nums.get('total_equity'))

        # ============ SOLVENCY / LEVERAGE RATIOS ============
        ratios_raw['debt_ratio'] = safe_div(nums.get('total_liabilities'), nums.get('total_assets'))
        ratios_raw['equity_ratio'] = safe_div(nums.get('total_equity'), nums.get('total_assets'))
        ratios_raw['debt_to_equity'] = safe_div(nums.get('total_liabilities'), nums.get('total_equity'))
        ratios_raw['equity_to_debt'] = safe_div(nums.get('total_equity'), nums.get('total_liabilities'))
        
        # Interest coverage
        ratios_raw['interest_coverage'] = safe_div(nums.get('ebit') or nums.get('operating_income'), nums.get('interest_expense'))
        
        # Debt service coverage (simplified - using net income)
        ratios_raw['debt_service_coverage'] = safe_div(nums.get('net_income'), nums.get('total_liabilities'))

        # ============ EFFICIENCY / ACTIVITY RATIOS ============
        ratios_raw['asset_turnover'] = safe_div(nums.get('revenue'), nums.get('total_assets'))
        ratios_raw['inventory_turnover'] = safe_div(nums.get('cogs'), nums.get('inventory'))
        ratios_raw['receivables_turnover'] = safe_div(nums.get('revenue'), nums.get('receivables'))
        ratios_raw['payables_turnover'] = safe_div(nums.get('cogs'), nums.get('payables'))
        
        # Days metrics
        if ratios_raw.get('receivables_turnover') and ratios_raw['receivables_turnover'] != 0:
            ratios_raw['days_sales_outstanding'] = 365 / ratios_raw['receivables_turnover']
        else:
            ratios_raw['days_sales_outstanding'] = None
            
        if ratios_raw.get('inventory_turnover') and ratios_raw['inventory_turnover'] != 0:
            ratios_raw['inventory_holding_period'] = 365 / ratios_raw['inventory_turnover']
        else:
            ratios_raw['inventory_holding_period'] = None

        # ============ ROUND RATIOS ============
        for k, v in list(ratios_raw.items()):
            if v is None:
                continue
            try:
                # Keep absolute monetary values unrounded. Round ratios (fractions) to 4 decimals.
                if k in ['gross_profit', 'operating_profit', 'net_profit', 'working_capital']:
                    ratios_raw[k] = v
                else:
                    ratios_raw[k] = round(v, 4)
            except Exception:
                ratios_raw[k] = v

        # ============ ORGANIZE BY CATEGORY ============
        ratios: Dict[str, Dict[str, Optional[float]]] = {
            'liquidity_ratios': {
                'current_ratio': ratios_raw.get('current_ratio'),
                'quick_ratio': ratios_raw.get('quick_ratio'),
                'cash_ratio': ratios_raw.get('cash_ratio'),
                'working_capital': ratios_raw.get('working_capital'),
            },
            'profitability_ratios': {
                'gross_profit': ratios_raw.get('gross_profit'),
                'gross_margin': ratios_raw.get('gross_margin'),
                'operating_profit': ratios_raw.get('operating_profit'),
                'operating_margin': ratios_raw.get('operating_margin'),
                'net_profit': ratios_raw.get('net_profit'),
                'net_margin': ratios_raw.get('net_margin'),
                'return_on_assets': ratios_raw.get('return_on_assets'),
                'return_on_equity': ratios_raw.get('return_on_equity'),
            },
            'solvency_ratios': {
                'debt_ratio': ratios_raw.get('debt_ratio'),
                'equity_ratio': ratios_raw.get('equity_ratio'),
                'debt_to_equity': ratios_raw.get('debt_to_equity'),
                'equity_to_debt': ratios_raw.get('equity_to_debt'),
                'interest_coverage': ratios_raw.get('interest_coverage'),
                'debt_service_coverage': ratios_raw.get('debt_service_coverage'),
            },
            'efficiency_ratios': {
                'asset_turnover': ratios_raw.get('asset_turnover'),
                'inventory_turnover': ratios_raw.get('inventory_turnover'),
                'receivables_turnover': ratios_raw.get('receivables_turnover'),
                'payables_turnover': ratios_raw.get('payables_turnover'),
                'days_sales_outstanding': ratios_raw.get('days_sales_outstanding'),
                'inventory_holding_period': ratios_raw.get('inventory_holding_period'),
            },
            '_extracted_numbers': nums,
        }

        return ratios

    def chat_answer(self, prompt: str) -> str:
        """Process a chat query and return an answer."""
        try:
            print("Processing chat query...")
            self.refresh_llm()  # Ensure we have the latest API key
            
            # Create a new chain for this chat if needed
            if not hasattr(self, '_chat_chain'):
                if not self.filepath:
                    raise ValueError("No document filepath set. Please upload a document first.")
                vectorstore, _ = self.process_document(self.filepath)
                self._chat_chain = self.create_chain(vectorstore)
            
            # Use the existing analyze method
            result = self.analyze(self._chat_chain, prompt)
            return result.get("answer", "Sorry, I couldn't find a relevant answer.")
        except Exception as e:
            print(f"Error in chat_answer: {str(e)}")
            return f"Error processing chat query: {str(e)}"

    def get_compliance_gap_report(self) -> str:
        """Generate a compliance gap report."""
        try:
            print(f"Starting compliance gap report generation. Filepath: {self.filepath}")
            self.refresh_llm()  # Ensure we have the latest API key
            
            if not hasattr(self, '_chat_chain') or self._chat_chain is None:
                print("Creating new chat chain...")
                if not self.filepath:
                    raise ValueError("No document filepath set. Please upload a document first.")
                vectorstore, _ = self.process_document(self.filepath)
                self._chat_chain = self.create_chain(vectorstore)
                print("Chat chain created successfully")
            
            print("Getting section analysis for compliance...")
            result = self.get_section_analysis(self._chat_chain, "compliance")
            print(f"Analysis result: {result}")
            return result.get("answer", "Could not generate compliance gap report.")
        except Exception as e:
            print(f"Error in get_compliance_gap_report: {str(e)}")
            return f"Error generating compliance gap report: {str(e)}"

    def get_auditor_report_summary(self) -> str:
        """Generate an auditor report summary."""
        try:
            print("Generating auditor report summary...")
            self.refresh_llm()

            if not hasattr(self, '_chat_chain') or self._chat_chain is None:
                print("Creating new chat chain for auditor report...")
                if not self.filepath:
                    raise ValueError("No document filepath set. Please upload a document first.")
                vectorstore, _ = self.process_document(self.filepath)
                self._chat_chain = self.create_chain(vectorstore)
                print("Chat chain created successfully.")

            result = self.get_section_analysis(self._chat_chain, "auditor_report")
            return result.get("answer", "Could not generate auditor report summary.")
        except Exception as e:
            print(f"Error in get_auditor_report_summary: {str(e)}")
            return f"Error generating auditor report summary: {str(e)}"

    def get_director_report_highlights(self) -> str:
        """Generate director report highlights."""
        try:
            print("Generating director report highlights...")
            self.refresh_llm()

            if not hasattr(self, '_chat_chain') or self._chat_chain is None:
                print("Creating new chat chain for director report...")
                if not self.filepath:
                    raise ValueError("No document filepath set. Please upload a document first.")
                vectorstore, _ = self.process_document(self.filepath)
                self._chat_chain = self.create_chain(vectorstore)
                print("Chat chain created successfully.")

            result = self.get_section_analysis(self._chat_chain, "director_report")
            return result.get("answer", "Could not generate director report highlights.")
        except Exception as e:
            print(f"Error in get_director_report_highlights: {str(e)}")
            return f"Error generating director report highlights: {str(e)}"

    def _extract_directors_report(self) -> str:
        """
        Extract Director's Report related content comprehensively from the document.
        Searches for board information, governance, management discussion, and related content.
        """
        try:
            print("Extracting Director's Report related content...")
            
            if not self._retriever:
                raise ValueError("Retriever not initialized. Please process a document first.")
            
            # Comprehensive list of search queries to find director's report and related governance content
            search_queries = [
                # Direct searches
                "director's report",
                "directors report",
                "board of directors report",
                "report of the board",
                "director report section",
                
                # Board and governance information
                "board meetings held",
                "number of meetings",
                "board of directors",
                "independent directors",
                "director appointments",
                "director changes",
                "director resignation",
                
                # Financial highlights and business overview
                "financial highlights",
                "change in business",
                "state of affairs",
                "company performance",
                "business overview",
                "management discussion",
                
                # Compliance and disclosures
                "directors responsibility",
                "responsibility statement",
                "related party transactions",
                "inter-corporate loans",
                "investments guarantee",
                "section 186",
                "section 188",
                
                # Audit and governance
                "auditor report",
                "fraud reported",
                "auditor remarks",
                "auditor appointment",
                "auditor reappointment",
                
                # Dividends and reserves
                "dividend recommended",
                "dividend rate",
                "transfer to reserves",
                "general reserve",
                
                # Specific compliance items
                "board meetings",
                "committee meetings",
                "director attendance",
                "internal controls",
                "risk management",
                "sexual harassment committee",
                "deposits accepted",
                "cost records",
                "energy consumption",
                "technology absorption",
                "foreign exchange",
                "subsidiaries",
                "joint venture",
                "associate company",
                "key managerial personnel",
                "post balance sheet events",
                "material changes",
                "insolvency proceedings",
                "web address",
                "annual return",
            ]
            
            print(f"Running {len(search_queries)} comprehensive searches for Director's Report content...")
            all_docs = []
            
            for query in search_queries:
                try:
                    docs = self._retriever.invoke(query)
                    if isinstance(docs, list):
                        all_docs.extend(docs)
                except Exception as e:
                    print(f"Warning: Search for '{query}' failed: {str(e)}")
                    pass
            
            # Remove duplicates based on content hash
            seen = set()
            unique_docs = []
            for doc in all_docs:
                # Create a hash of the first 100 characters and page number
                content_signature = (hash(doc.page_content[:100]), doc.metadata.get("page", 0))
                if content_signature not in seen:
                    seen.add(content_signature)
                    unique_docs.append(doc)
            
            print(f"Found {len(unique_docs)} unique documents from {len(all_docs)} total matches")
            
            # Sort by page number to maintain proper order
            unique_docs.sort(key=lambda x: x.metadata.get("page", 0))
            
            # Combine all relevant content
            director_report_content = "\n\n".join([doc.page_content for doc in unique_docs])
            
            if not director_report_content.strip():
                print("Warning: No content found for Director's Report analysis")
                raise ValueError("Could not extract any relevant content for Director's Report")
            
            print(f"Extracted and combined {len(unique_docs)} documents ({len(director_report_content)} characters)")
            return director_report_content
            
        except Exception as e:
            print(f"Error extracting Director's Report: {str(e)}")
            raise

    def get_director_report_compliance_check(self) -> iter:
        """
        Performs a compliance check on the Director's Report against predefined rules
        and yields structured results for streaming. This is a generator function.
        """
        try:
            print("Starting Director's Report compliance check...")
            self.refresh_llm()

            if not hasattr(self, '_chat_chain') or self._chat_chain is None:
                print("Creating new chat chain for compliance check...")
                if not self.filepath:
                    raise ValueError("No document filepath set. Please upload a document first.")
                vectorstore, _ = self.process_document(self.filepath)
                self._chat_chain = self.create_chain(vectorstore)
                print("Chat chain created successfully.")

            # Extract the Director's Report section first
            director_report_content = self._extract_directors_report()
            
            if not director_report_content.strip():
                yield {"error": "Director's Report section not found in the document"}
                return

            # Process each rule individually
            for item in self.DIRECTOR_COMPLIANCE_RULES:
                rule = item["rule"]
                keywords = ", ".join(item["keywords"])
                
                # Create a targeted query for each rule
                query = f"""You are an expert financial auditor. Analyze the following content from a company's Director's Report to check for compliance with a specific rule.

                **Content to Analyze:**
                {director_report_content[:8000]} 

                **Rule to Check:**
                "{rule}" - Keywords: {keywords}

                **Instructions:**
                1. Determine if the content complies with the rule.
                2. Provide a brief reasoning for your decision (max 40 words).
                3. Respond with "Complied", "Not Complied", or "Not Found".

                **Format your answer as:**
                Status: [Complied/Not Complied/Not Found]
                Reasoning: [Your reasoning here]
                """

                try:
                    # Use the chain to get an answer for the specific rule
                    raw_answer = self._chat_chain.invoke(query)
                    
                    # Parse the free-text answer
                    parsed_result = self._parse_compliance_answer(raw_answer)
                    
                    yield {
                        "rule": rule,
                        "status": parsed_result["status"],
                        "reasoning": parsed_result["reasoning"]
                    }
                except Exception as e:
                    yield {
                        "rule": rule,
                        "status": "Not Found",
                        "reasoning": f"An error occurred during analysis: {str(e)}",
                        "error": str(e)
                    }

        except Exception as e:
            print(f"Error in get_director_report_compliance_check: {str(e)}")
            yield {"error": f"An error occurred during the compliance check: {e}"}



    def get_overall_summary(self) -> str:
        """Generate an overall summary of the financial document."""
        try:
            print("Generating overall summary...")
            self.refresh_llm()

            if not hasattr(self, '_chat_chain') or self._chat_chain is None:
                print("Creating new chat chain for overall summary...")
                if not self.filepath:
                    raise ValueError("No document filepath set. Please upload a document first.")
                vectorstore, _ = self.process_document(self.filepath)
                self._chat_chain = self.create_chain(vectorstore)
                print("Chat chain created successfully.")

            summary_prompt = """Provide a comprehensive summary of the financial document covering:
                1. Key financial highlights
                2. Business performance
                3. Major developments
                4. Future outlook
                5. Any significant concerns or risks"""
            
            result = self.analyze(self._chat_chain, summary_prompt)
            return result.get("answer", "Could not generate overall summary.")
        except Exception as e:
            print(f"Error in get_overall_summary: {str(e)}")
            return f"Error generating overall summary: {str(e)}"

    def analyze_financial_text(self, prompt_text: str):
        """
        Analyzes a given financial text using the LLM and a specific prompt.

        Args:
            prompt_text: The text to be analyzed.

        Returns:
            The raw response from the language model.
        """
        try:
            # Ensure the LLM is initialized with the latest API key
            self.refresh_llm()
            
            # Invoke the LLM with the provided text
            # Estimate input tokens
            try:
                est_in = self._estimate_tokens(prompt_text)
            except Exception:
                est_in = 0

            response = self.llm.invoke(prompt_text)

            # Estimate output tokens
            est_out = 0
            try:
                if isinstance(response, str):
                    est_out = self._estimate_tokens(response)
                elif isinstance(response, dict):
                    # Some LLM clients may return usage metadata or 'answer' text
                    if 'usage' in response and isinstance(response['usage'], dict):
                        # try to honor actual usage if present
                        u = response['usage']
                        est_in = int(u.get('prompt_tokens', est_in)) if u.get('prompt_tokens') else est_in
                        est_out = int(u.get('completion_tokens', est_out)) if u.get('completion_tokens') else est_out
                    else:
                        ans = response.get('answer') if isinstance(response.get('answer'), str) else None
                        if ans:
                            est_out = self._estimate_tokens(ans)
            except Exception:
                est_out = 0

            try:
                # Record per-request usage
                try:
                    completion_text = None
                    usage = None
                    if isinstance(response, str):
                        completion_text = response
                    elif isinstance(response, dict):
                        usage = response.get('usage')
                        completion_text = response.get('answer') if isinstance(response.get('answer'), str) else None
                    self.set_last_request_tokens(est_in, est_out, prompt_text=prompt_text, completion_text=completion_text, usage=usage)
                except Exception:
                    pass

                self.token_stats['input_tokens'] += est_in
                self.token_stats['output_tokens'] += est_out
                self.token_stats['total_tokens'] = self.token_stats['input_tokens'] + self.token_stats['output_tokens']
            except Exception:
                pass

            return response
        except Exception as e:
            print(f"Error during financial text analysis: {e}")
            raise

    def get_balance_sheet(self, text: str) -> str:
        """
        Generates a prompt for extracting the balance sheet from text.

        Args:
            text: The text containing the balance sheet.

        Returns:
            A formatted prompt string.
        """
        return f'''
        Extract the Balance Sheet from the following text. The values may be spread across multiple lines.
        Provide the output in a clean, valid JSON format. The JSON should have keys for "Assets" and "Equity and Liabilities".
        Each key should contain a list of items, where each item has "particulars" and "amount".

        Text to analyze:
        {text}
        '''