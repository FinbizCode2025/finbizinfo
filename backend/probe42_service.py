import os
import requests
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.orm import sessionmaker
from models import Base, Company, Financial, Director, Charge, engine

PROBE42_API_KEY = os.getenv("PROBE42_API_KEY")
BASE_URL = os.getenv("PROBE42_BASE_URL", "https://api.probe42.in")

# Initialize database session
Session = sessionmaker(bind=engine)

# ---------------------------------------------
# Base request helper with retry and error handling
# ---------------------------------------------
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def _get(url, params=None, timeout=30):
    headers = {
        "x-api-key": PROBE42_API_KEY,
        "Accept": "application/json",
        "x-api-version": "1.3"
    }
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON response from Probe42 API")
    return data

# ---------------------------------------------
# 1. Search company by name
# ---------------------------------------------
def search_company_by_name(name: str):
    """Search for companies by name. Returns list of company entities."""
    if not name or not isinstance(name, str):
        raise ValueError("Company name must be a non-empty string")

    url = f"{BASE_URL}/entities"
    filters = {
        "nameStartsWith": name.strip(),
        "entityType": ["company", "llp"]
    }
    params = {"limit": 10, "filters": json.dumps(filters)}

    try:
        data = _get(url, params)
        entities = data.get("entities", [])
        return entities if isinstance(entities, list) else []
    except Exception as e:
        print(f"Error searching company by name '{name}': {e}")
        return []

# ---------------------------------------------
# 2. Get company profile
# ---------------------------------------------
def get_company_profile(cin: str):
    """Get comprehensive company profile by CIN."""
    if not cin or not isinstance(cin, str):
        raise ValueError("CIN must be a non-empty string")

    # Validate CIN format
    if not re.match(r'^[A-Z0-9]{21}$', cin):
        raise ValueError("Invalid CIN format. Must be exactly 21 uppercase letters and digits")

    try:
        base_url = f"{BASE_URL}/companies/{cin}/base-details"
        comp_url = f"{BASE_URL}/companies/{cin}/comprehensive-details"

        base_data = _get(base_url)
        comp_data = _get(comp_url)

        profile = {**base_data, **comp_data}

        if not profile.get("cin"):
            raise ValueError("CIN not found in profile data")

        return profile
    except Exception as e:
        print(f"Error getting company profile for CIN '{cin}': {e}")
        raise

# ---------------------------------------------
# 3. Get peer comparison
# ---------------------------------------------
def get_peer_comparison(cin: str):
    """Get peer comparison data for a company by CIN."""
    main_profile = get_company_profile(cin)
    industry = main_profile.get("industry") or main_profile.get("primary_industry") or ""

    peers_raw = _fetch_peers(industry, exclude_cin=cin, limit=2)
    peer_data = []
    for peer in peers_raw:
        peer_cin = peer.get("cin")
        if peer_cin:
            try:
                peer_profile = get_company_profile(peer_cin)
                peer_data.append(peer_profile)
            except Exception as e:
                print(f"Error fetching peer profile for {peer_cin}: {e}")
                continue

    comparison_table = _build_comparison_table(main_profile, peer_data)
    return {
        "main_company": main_profile,
        "peers": peer_data,
        "comparison_table": comparison_table
    }

# ---------------------------------------------
# Helper functions
# ---------------------------------------------
def _fetch_peers(industry: str, exclude_cin: str, limit: int = 2):
    """Fetch peer companies from the same industry."""
    if not industry:
        return []

    url = f"{BASE_URL}/entities"
    filters = {
        "industry": industry,
        "entityType": ["company", "llp"]
    }
    params = {"limit": limit + 1, "filters": json.dumps(filters)}

    try:
        data = _get(url, params)
        entities = data.get("entities", [])
        peers = [e for e in entities if e.get("cin") != exclude_cin][:limit]
        return peers
    except Exception as e:
        print(f"Error fetching peers for industry '{industry}': {e}")
        return []

def _build_comparison_table(main_company: dict, peers: list):
    """Build comparison table structure."""
    def safe_get(d, key):
        return d.get(key, "-") if isinstance(d, dict) else "-"

    metrics = ["CIN", "Industry", "Turnover", "Net Profit/Loss", "Incorporation Year", "Directors"]
    table = {"Metric": metrics}

    table["Main Company"] = [
        safe_get(main_company, "cin"),
        safe_get(main_company, "industry"),
        safe_get(main_company, "turnover"),
        safe_get(main_company, "net_profit"),
        safe_get(main_company, "incorporation_year"),
        safe_get(main_company, "directors")
    ]

    for i, peer in enumerate(peers[:2]):
        table[f"Peer {i+1}"] = [
            safe_get(peer, "cin"),
            safe_get(peer, "industry"),
            safe_get(peer, "turnover"),
            safe_get(peer, "net_profit"),
            safe_get(peer, "incorporation_year"),
            safe_get(peer, "directors")
        ]

    return table

# ---------------------------------------------
# Database operations with upserts
# ---------------------------------------------
def save_company_data(profile: dict):
    """Save company profile data to database with upserts."""
    session = Session()
    try:
        cin = profile.get("cin")
        if not cin:
            return None

        # Upsert company
        company = session.query(Company).filter_by(cin=cin).first()
        if not company:
            company = Company(
                cin=cin,
                name=profile.get("name", ""),
                industry=profile.get("industry", ""),
                incorporation_year=profile.get("incorporation_year"),
                status=profile.get("status", ""),
                address=profile.get("address", "")
            )
            session.add(company)
            session.flush()
        else:
            company.name = profile.get("name", company.name)
            company.industry = profile.get("industry", company.industry)
            company.incorporation_year = profile.get("incorporation_year", company.incorporation_year)
            company.status = profile.get("status", company.status)
            company.address = profile.get("address", company.address)

        # Upsert financials
        year = profile.get("incorporation_year") or 2024
        financial = session.query(Financial).filter_by(company_id=company.id, year=year).first()
        if not financial:
            financial = Financial(company_id=company.id, year=year)
            session.add(financial)

        financial.turnover = profile.get("turnover", financial.turnover)
        financial.net_profit = profile.get("net_profit", financial.net_profit)
        financial.total_assets = profile.get("total_assets", financial.total_assets)
        financial.total_liabilities = profile.get("total_liabilities", financial.total_liabilities)

        # Upsert directors
        for dir_data in profile.get("directors", []):
            if isinstance(dir_data, dict):
                din = dir_data.get("din")
                if din:
                    director = session.query(Director).filter_by(company_id=company.id, din=din).first()
                    if not director:
                        director = Director(company_id=company.id, din=din)
                        session.add(director)
                    director.name = dir_data.get("name", director.name)
                    director.designation = dir_data.get("designation", director.designation)

        # Upsert charges
        for charge_data in profile.get("charges", []):
            if isinstance(charge_data, dict):
                charge_holder = charge_data.get("charge_holder")
                if charge_holder:
                    charge = session.query(Charge).filter_by(company_id=company.id, charge_holder=charge_holder).first()
                    if not charge:
                        charge = Charge(company_id=company.id, charge_holder=charge_holder)
                        session.add(charge)
                    charge.charge_amount = charge_data.get("charge_amount", charge.charge_amount)
                    charge.status = charge_data.get("status", charge.status)

        session.commit()
        return company.id
    except Exception as e:
        session.rollback()
        print(f"Error saving company data: {e}")
        raise
    finally:
        session.close()
