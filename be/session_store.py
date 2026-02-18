from typing import Optional, Dict, Any
import json
from pathlib import Path
from config import Config
from financial_analyzer import FinancialAnalyzer

class SessionStore:
    """Manages document analysis sessions."""
    
    def __init__(self, session_id: str, filepath: Optional[str] = None):
        self.session_id = session_id
        self.filepath = filepath
        self.config = Config()
        self._analyzer = FinancialAnalyzer()
        self._chain = None
        self._vectorstore = None
        self.balance_sheet_data = None
        self.balance_sheet_pdf = None

    def initialize(self):
        """Initialize or load the analysis session."""
        if not self.filepath:
            # Try to load from persisted session
            self._vectorstore, metadata = self._analyzer.load_analysis_state(self.session_id)
            if not self._vectorstore:
                raise ValueError("No document available for this session")
        else:
            # Process new document
            self._vectorstore, documents = self._analyzer.process_document(self.filepath)
            self._analyzer.save_analysis_state(self.session_id, self._vectorstore, documents)

        # Create conversation chain
        self._chain = self._analyzer.create_chain(self._vectorstore)

    def analyze(self, query: str) -> Dict[str, Any]:
        """Run an analysis query."""
        if not self._chain:
            self.initialize()
        return self._analyzer.analyze(self._chain, query)

    def get_section_analysis(self, section_type: str) -> Dict[str, Any]:
        """Get analysis for a specific section."""
        if not self._chain:
            self.initialize()
        return self._analyzer.get_section_analysis(self._chain, section_type)

    def get_director_report_compliance_check(self):
        """Get director report compliance check results."""
        if not self._chain:
            self.initialize()
        return self._analyzer.get_director_report_compliance_check()

    def save_state(self):
        """Persist session state to disk."""
        session_path = Config.SESSIONS_DIR / self.session_id
        session_path.mkdir(parents=True, exist_ok=True)
        
        state = {
            "session_id": self.session_id,
            "filepath": self.filepath,
            "balance_sheet_data": self.balance_sheet_data,
            "balance_sheet_pdf": self.balance_sheet_pdf
        }
        
        with open(session_path / "state.json", "w") as f:
            json.dump(state, f)

    @classmethod
    def load(cls, session_id: str) -> Optional['SessionStore']:
        """Load a session from disk."""
        session_path = Config.SESSIONS_DIR / session_id / "state.json"
        if not session_path.exists():
            return None
            
        try:
            with open(session_path) as f:
                state = json.load(f)
            
            session = cls(session_id)
            session.filepath = state.get("filepath")
            session.balance_sheet_data = state.get("balance_sheet_data")
            session.balance_sheet_pdf = state.get("balance_sheet_pdf")
            
            return session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None