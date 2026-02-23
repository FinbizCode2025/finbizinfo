import requests
import xml.etree.ElementTree as ET
import json
import os

# Tally URL (default port 9000)
TALLY_URL = "http://localhost:9000"

# Target company from persistent memory
TARGET_COMPANY = "Maestro Engineering Pvt. Ltd 2024-25"

def get_tally_xml_request(company):
    """Generates the XML request for fetching the Balance Sheet from Tally."""
    return f"""
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>Balance Sheet</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>SysName:XML</SVEXPORTFORMAT>
                <SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
        </DESC>
    </BODY>
</ENVELOPE>
"""

def parse_tally_balance_sheet(xml_content):
    """
    Parses Tally XML response into a structured JSON-like list.
    Note: Tally XML structure for reports can be complex; this is a simplified parser.
    """
    try:
        root = ET.fromstring(xml_content)
        # Tally reports typically have rows in groups
        rows = []
        
        # This is a heuristic parser for Tally's Balance Sheet XML structure
        # In a real scenario, this would be highly specific to Tally's schema
        for line in root.findall(".//DSPACCNAME"):
            particulars = line.find("DSPDISPNAME").text if line.find("DSPDISPNAME") is not None else "Unknown"
            # Try to find associated amount
            # (Simplification: just getting names for demo if structure is unknown)
            rows.append({"Particulars": particulars, "Amount": 0})
            
        return rows
    except Exception as e:
        print(f"Error parsing Tally XML: {e}")
        return None

def fetch_and_print_balance_sheet():
    print(f"📡 Connecting to Tally at {TALLY_URL}...")
    print(f"🏢 Target Company: {TARGET_COMPANY}")
    
    xml_request = get_tally_xml_request(TARGET_COMPANY)
    
    try:
        # We use a short timeout as this is a local connection
        response = requests.post(TALLY_URL, data=xml_request, timeout=5)
        
        if response.status_code == 200:
            print("✅ Successfully connected to Tally!")
            data = parse_tally_balance_sheet(response.text)
            
            if data:
                print("\n📊 BALANCE SHEET TABLE JSON (from Tally):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print("⚠️ Could not parse the data from Tally response.")
        else:
            print(f"❌ Tally returned error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Tally. Ensure Tally is running and port 9000 is open.")
        
        # Provide Mock Data for the terminal as requested to see JSON
        print("\n--- [SIMULATED OUTPUT FOR DEMO] ---")
        mock_data = [
            {"Particulars": "Capital Account", "Amount": 1250000.00},
            {"Particulars": "Loans (Liability)", "Amount": 450000.00},
            {"Particulars": "Current Liabilities", "Amount": 320000.00},
            {"Particulars": "Fixed Assets", "Amount": 1500000.00},
            {"Particulars": "Current Assets", "Amount": 520000.00},
            {"Particulars": "Profit & Loss A/c", "Amount": 100000.00}
        ]
        print("\n📊 BALANCE SHEET TABLE JSON (MOCK):")
        print(json.dumps(mock_data, indent=2, ensure_ascii=False))
        print("--- [END SIMULATION] ---\n")

if __name__ == "__main__":
    fetch_and_print_balance_sheet()
