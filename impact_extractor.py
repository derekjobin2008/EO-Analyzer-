import requests
import json
import time
import re

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def extract_structured_impacts(eo_title, eo_full_text, country, product_category):
    """
    Extract structured impact data from an EO using Ollama
    Returns JSON with specific tariff rates, HTS codes, dates, and impact categories
    """
    
    prompt = f"""You are extracting structured trade impact data from a US Executive Order.

EXECUTIVE ORDER TITLE: {eo_title}

EXECUTIVE ORDER TEXT (first 6000 chars):
{eo_full_text[:6000]}

USER CONTEXT:
- Importing Country: {country}
- Product Category: {product_category}

Extract the following structured data. Return ONLY valid JSON, no other text.

IMPORTANT: "has_trade_impacts" should be TRUE if the EO:
- Mentions tariffs, duties, suspensions, quotas, or trade restrictions
- Affects import costs or customs procedures
- Impacts supply chains or trade flows
- References countries or trade agreements

For tariff_mechanisms, identify:
- type: "ad_valorem_tariff", "specific_tariff", "quota", "duty_suspension", "duty_continuation", "duty_increase", "customs_enforcement", "compliance_requirement", etc.
- rate: numeric rate if specified (e.g., 25 for 25%), or null if not quantified
- hts_codes: list of HTS codes affected if mentioned (e.g., ["8471", "8517"]), empty list if not specified
- description: what the mechanism does
- effective_date: YYYY-MM-DD if mentioned, null otherwise
- phase_in: "immediate", "gradual", timeline, or null

For impact_flags, include ANY impacts mentioned:
- category: "revenue", "manufacturing_cost", "cogs", "employment", "supply_chain", "compliance_cost", "import_cost", "market_access"
- type: "explicit" if directly stated, "inferred" if implied by policy
- severity: "high", "medium", or "low"
- description: the specific impact
- affected_parties: list of who is affected ["importers", "manufacturers", "consumers", "workers", "exporters", etc.]

Return this JSON structure:
{{
  "has_trade_impacts": true/false,
  "tariff_mechanisms": [
    {{
      "type": "string",
      "rate": number or null,
      "hts_codes": [],
      "description": "string",
      "effective_date": "YYYY-MM-DD or null",
      "phase_in": "string or null"
    }}
  ],
  "impact_flags": [
    {{
      "category": "string",
      "type": "explicit or inferred",
      "severity": "high or medium or low",
      "description": "string",
      "affected_parties": []
    }}
  ],
  "key_dates": {{
    "effective_date": "YYYY-MM-DD or null",
    "implementation_deadline": "YYYY-MM-DD or null",
    "phase_in_schedule": "string or null"
  }},
  "summary": "2-3 sentence summary of quantifiable impacts"
}}
"""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2
            },
            timeout=180
        )
        
        response.raise_for_status()
        result = response.json()
        response_text = result.get("response", "")
        
        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            structured_data = json.loads(json_str)
            return structured_data
        else:
            return {
                "has_trade_impacts": False,
                "error": "Could not parse response",
                "raw_response": response_text[:500]
            }
    
    except json.JSONDecodeError as e:
        return {
            "has_trade_impacts": False,
            "error": f"JSON parsing error: {str(e)}"
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "has_trade_impacts": False,
            "error": f"Ollama connection error: {str(e)}"
        }
def extract_from_relevant_eos(relevant_eos, country, product_category):
    """
    Extract structured impact data from all relevant EOs
    Returns list of EOs with structured impact data
    """
    
    results = []
    
    print(f"\nExtracting structured impacts from {len(relevant_eos)} EOs...")
    print("=" * 80)
    
    for i, eo in enumerate(relevant_eos):
        title = eo.get("title", "")
        full_text = eo.get("full_text", "")
        
        print(f"\n[{i+1}/{len(relevant_eos)}] Extracting: {title[:70]}...")
        
        structured_data = extract_structured_impacts(title, full_text, country, product_category)
        
        results.append({
            "title": title,
            "document_number": eo.get("document_number"),
            "publication_date": eo.get("publication_date"),
            "html_url": eo.get("html_url"),
            "structured_impacts": structured_data
        })
        
        if structured_data.get("has_trade_impacts"):
            mechanisms = len(structured_data.get("tariff_mechanisms", []))
            flags = len(structured_data.get("impact_flags", []))
            print(f"  ✓ Found {mechanisms} tariff mechanism(s), {flags} impact flag(s)")
        else:
            print(f"  ✗ No structured impacts found")
        
        time.sleep(2)  # Rate limiting
    
    return results

if __name__ == "__main__":
    # Test with a sample
    test_eo = {
        "title": "Continuing the Suspension of Duty-Free De Minimis Treatment for All Countries",
        "full_text": "By the authority vested in me as President by the Constitution and the laws of the United States of America, including the International Emergency Economic Powers Act (50 U.S.C. 1701 et seq.) (IEEPA), the National Emergencies Act (50 U.S.C. 1601 et seq.), section 604 of the Trade Act of 1974, as amended (19 U.S.C. 1862), and section 301 of the Trade Act of 1974, as amended (19 U.S.C. 1241), I hereby order that the suspension of duty-free de minimis treatment for all countries, as implemented in the Proclamation of February 20, 2026, shall continue in effect.",
        "document_number": "2026-03829",
        "publication_date": "2026-02-25",
        "html_url": "https://example.com"
    }
    
    result = extract_structured_impacts(
        test_eo["title"],
        test_eo["full_text"],
        "China",
        "semiconductors"
    )
    
    print("\nStructured Impact Data:")
    print(json.dumps(result, indent=2))
