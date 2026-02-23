
import os
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

# Try to import Apryse
try:
    from PDFNetPython3 import PDFNet, PDFDoc, DataExtractionModule
    APRYSE_AVAILABLE = True
except ImportError:
    try:
        from apryse_sdk import PDFNet, PDFDoc, DataExtractionModule
        APRYSE_AVAILABLE = True
    except ImportError:
        APRYSE_AVAILABLE = False

# Try to import LeadTools
try:
    import leadtools
    # LeadTools usually requires specific initialization and multiple modules
    LEADTOOLS_AVAILABLE = True
except ImportError:
    LEADTOOLS_AVAILABLE = False

class AdvancedPDFService:
    """
    Service for high-fidelity PDF extraction using Apryse (PDFTron) or LEADTOOLS.
    These tools are professional-grade and typically handle complex tables better 
    than open-source alternatives.
    """
    
    @staticmethod
    def is_apryse_available():
        return APRYSE_AVAILABLE and Config.APRYSE_LICENSE_KEY is not None

    @staticmethod
    def is_leadtools_available():
        return LEADTOOLS_AVAILABLE and Config.LEADTOOLS_DEV_LICENSE_FILE is not None

    @classmethod
    def extract_with_apryse(cls, pdf_path: str, output_json_path: str = None):
        """
        Extract structured data using Apryse Data Extraction Module.
        """
        if not cls.is_apryse_available():
            logger.warning("Apryse SDK not available or license key missing.")
            return None

        try:
            PDFNet.Initialize(Config.APRYSE_LICENSE_KEY)
            doc = PDFDoc(pdf_path)
            
            # Use Data Extraction Module for tabular data
            # Engine options: e_tabular, e_form, e_doc_structure
            if not output_json_path:
                output_json_path = pdf_path.replace(".pdf", "_apryse.json")
                
            DataExtractionModule.ExtractData(doc, output_json_path, DataExtractionModule.e_tabular)
            
            with open(output_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return data
        except Exception as e:
            logger.error(f"Apryse extraction failed: {e}")
            return None
        finally:
            PDFNet.Terminate()

    @classmethod
    def extract_with_leadtools(cls, pdf_path: str):
        """
        Extract structured data using LEADTOOLS.
        (Implementation placeholder - requires specific LeadTools license and modules)
        """
        if not cls.is_leadtools_available():
            logger.warning("LEADTOOLS not available or license missing.")
            return None
            
        try:
            # LeadTools initialization logic would go here
            # leadtools.RasterSupport.set_license(Config.LEADTOOLS_DEV_LICENSE_FILE, Config.LEADTOOLS_DEV_KEY)
            logger.info(f"Triggering LEADTOOLS extraction for {pdf_path}")
            # Real implementation would use LeadTools Document Analyzer or Form Recognition
            return {"status": "LEADTOOLS implementation placeholder"}
        except Exception as e:
            logger.error(f"LEADTOOLS extraction failed: {e}")
            return None

    @classmethod
    def smart_extract(cls, pdf_path: str):
        """
        Automated selection of the best available tool.
        """
        if cls.is_apryse_available():
            logger.info("Using Apryse for smart extraction...")
            return cls.extract_with_apryse(pdf_path)
        elif cls.is_leadtools_available():
            logger.info("Using LEADTOOLS for smart extraction...")
            return cls.extract_with_leadtools(pdf_path)
        else:
            logger.info("No advanced SDKs available, falling back to open-source processors.")
            return None
