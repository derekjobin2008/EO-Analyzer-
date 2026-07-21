# derek test code for the fed reg
import requests
import json
from datetime import datetime, timedelta
import time
import pdfplumber
from io import BytesIO

def fetch_executive_orders(start_date, end_date):
    """
    Fetch executive orders from Federal Register API for a specific date range
    
    Args:
        start_date: string in format "YYYY-MM-DD"
        end_date: string in format "YYYY-MM-DD"
    
    Returns list of EO documents with their full text extracted from PDFs
    """
    
    url = "https://www.federalregister.gov/api/v1/documents"
    
    params = {
        "conditions[presidential_document_type]": "executive_order",
        "conditions[publication_date][gte]": start_date,
        "conditions[publication_date][lte]": end_date,
        "per_page": 100,
        "order": "newest"
    }
    
    print(f"Fetching executive orders from {start_date} to {end_date}...")
    
    all_eos = []
    page = 1
    
    while True:
        params["page"] = page
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                break
            
            all_eos.extend(data["results"])
            
            print(f"  Fetched page {page} ({len(data['results'])} orders)")
            time.sleep(1)
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
    
    print(f"Total EOs fetched: {len(all_eos)}\n")
    print("Extracting text from PDFs...")
    
    for i, eo in enumerate(all_eos):
        try:
            pdf_url = eo.get("pdf_url")
            if pdf_url:
                pdf_response = requests.get(pdf_url, timeout=10)
                pdf_response.raise_for_status()
                
                pdf_file = BytesIO(pdf_response.content)
                full_text = ""
                
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                
                eo["full_text"] = full_text
                print(f"  [{i+1}/{len(all_eos)}] Extracted {len(full_text)} chars from: {eo['title'][:60]}...")
            else:
                eo["full_text"] = ""
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error extracting PDF for {eo.get('title', 'Unknown')}: {e}")
            eo["full_text"] = ""
    
    return all_eos

if __name__ == "__main__":
    eos = fetch_executive_orders("2026-01-05", "2026-07-04")
    print(f"\nFirst EO title: {eos[0].get('title')}")
    print(f"Full text length: {len(eos[0].get('full_text', ''))} characters")