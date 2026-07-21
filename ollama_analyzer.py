import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def create_session_with_retries():
    """Create requests session with automatic retry logic"""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    return session

def analyze_eo_with_ollama(eo_title, eo_full_text, country, product_category, sector=None):
    """
    Pass 2: Use local Ollama/Mistral to validate relevance and extract impacts
    """
    
    sector_mention = f"\n- Sector: {sector}" if sector else ""
    
    prompt = f"""You are analyzing a US Executive Order for relevance to trade/tariffs.

EXECUTIVE ORDER TITLE: {eo_title}

EXECUTIVE ORDER TEXT:
{eo_full_text[:5000]}

USER INTERESTS:
- Importing Country: {country}
- Product Category: {product_category}{sector_mention}

Your task:
1. Is this EO relevant to trade/tariffs affecting {country} imports of {product_category}? (Answer: YES or NO)
2. If YES, extract:
   - Specific tariff/import mechanisms mentioned
   - Cost impacts (explicit and inferred, labeled clearly)
   - Employment impacts (explicit and inferred, labeled clearly)
   - Effective dates and phase-in schedules
3. If NO, explain why it's not relevant

Return ONLY valid JSON in this exact format:
{{
  "relevant": true/false,
  "relevance_reason": "brief explanation",
  "tariff_mechanisms": ["mechanism 1", "mechanism 2"],
  "cost_impacts": {{
    "explicit": ["impact 1"],
    "inferred": ["impact 1"]
  }},
  "employment_impacts": {{
    "explicit": ["impact 1"],
    "inferred": ["impact 1"]
  }},
  "effective_dates": "date or schedule",
  "summary": "2-3 sentence summary of impacts"
}}
"""

    session = create_session_with_retries()
    max_retries = 5
    timeout_seconds = 180  # 3 minute timeout
    
    for attempt in range(max_retries):
        try:
            response = session.post(
                OLLAMA_API_URL,
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3
                },
                timeout=timeout_seconds
            )
            
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")
            
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                    return analysis
                else:
                    return {
                        "relevant": False,
                        "relevance_reason": "Could not parse response",
                        "error": response_text[:200]
                    }
            except json.JSONDecodeError as e:
                return {
                    "relevant": False,
                    "relevance_reason": "JSON parsing error",
                    "error": str(e)
                }
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"    Timeout (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    "relevant": False,
                    "relevance_reason": "Ollama timeout (EO too large or service slow)",
                    "error": "Failed after 5 attempts"
                }
        
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"    Connection error (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    "relevant": False,
                    "relevance_reason": "Cannot connect to Ollama. Make sure 'ollama serve' is running.",
                    "error": "Connection refused after 5 attempts"
                }
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"    Request error (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    "relevant": False,
                    "relevance_reason": "Ollama request failed",
                    "error": str(e)
                }
    
    return {
        "relevant": False,
        "relevance_reason": "Max retries exceeded",
        "error": "Unknown error"
    }

def analyze_filtered_eos(filtered_eos, country, product_category, sector=None):
    """
    Analyze all filtered EOs with user's country, product, and sector
    Returns list of relevant EOs with extracted impacts
    """
    
    results = []
    sector_str = f" ({sector})" if sector else ""
    
    print(f"\nAnalyzing {len(filtered_eos)} EOs for {country} - {product_category}{sector_str}...")
    print("=" * 80)
    
    for i, eo in enumerate(filtered_eos):
        title = eo.get("title", "")
        full_text = eo.get("full_text", "")
        
        print(f"\n[{i+1}/{len(filtered_eos)}] Analyzing: {title[:70]}...")
        
        analysis = analyze_eo_with_ollama(title, full_text, country, product_category, sector)
        
        time.sleep(2)  # Rate limiting between requests
        
        if analysis.get("relevant"):
            print(f"  ✓ RELEVANT")
            results.append({
                "title": title,
                "document_number": eo.get("document_number"),
                "publication_date": eo.get("publication_date"),
                "html_url": eo.get("html_url"),
                "analysis": analysis
            })
        else:
            print(f"  ✗ Not relevant: {analysis.get('relevance_reason', 'Unknown')}")
    
    return results

if __name__ == "__main__":
    from fed_register_fetcher import fetch_executive_orders
    from trade_filter import filter_executive_orders
    
    all_eos = fetch_executive_orders(months_back=6)
    filtered_eos = filter_executive_orders(all_eos)
    results = analyze_filtered_eos(filtered_eos, "China", "semiconductors", "automotive")
    
    print("\n" + "=" * 80)
    print(f"Final results: {len(results)} relevant EOs found\n")