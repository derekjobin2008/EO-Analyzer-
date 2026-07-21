import re

def smart_prefilter_eo(eo_title, eo_full_text, country, product_category):
    """
    Smart pre-filter: Use regex to identify OBVIOUSLY relevant EOs
    Returns (confidence_level, reason) where:
    - "high" = send to Ollama (ambiguous)
    - "obvious_yes" = skip Ollama, mark as relevant
    - "obvious_no" = skip Ollama, mark as not relevant
    """
    
    if not eo_full_text:
        return "obvious_no", "No full text available"
    
    combined_text = (eo_title + " " + eo_full_text).lower()
    country_lower = country.lower()
    product_lower = product_category.lower()
    
    # Check 1: STRICT - Direct country + tariff/duty mentions = OBVIOUS YES
    if re.search(rf'\b{country_lower}\b', combined_text) and \
       re.search(r'\b(tariff|duties|duty rate|ad valorem|tariff rate)\b', combined_text):
        return "obvious_yes", f"Explicitly mentions {country} + tariffs"
    
    # Check 2: STRICT - De minimis suspension (always about tariffs, always China-relevant) = OBVIOUS YES
    if re.search(r'de minimis', combined_text) and \
       re.search(r'\bsuspend\b', combined_text):
        return "obvious_yes", "De minimis duty suspension (direct tariff impact)"
    
    # Check 3: STRICT - HTS codes + China mention = OBVIOUS YES
    if re.search(r'\bhts\s*code', combined_text) and \
       re.search(rf'\b{country_lower}\b', combined_text):
        return "obvious_yes", f"HTS codes mentioned with {country}"
    
    # Check 4: STRICT - Section 301 actions ONLY if country is mentioned
    if re.search(r'\bsection\s+301\b', combined_text) and \
       re.search(rf'\b{country_lower}\b', combined_text):
        return "obvious_yes", "Section 301 trade action with explicit country mention"
    
    # Check 5: STRICT - "Ending Certain Tariff Actions" type title = OBVIOUS YES
    if re.search(r'\b(ending|continuing|modifying)\b.*\btariff', eo_title.lower()) or \
       re.search(r'\btariff.*\b(ending|continuing|modifying)\b', eo_title.lower()):
        return "obvious_yes", f"Title explicitly about tariff actions"
    
    # Check 6: STRICT - Clearly NOT about trade = OBVIOUS NO
    if re.search(r'\b(vaccine|medical|health|disease|pandemic|covid|sports|athletics|ncaa|college)\b', combined_text) and \
       not re.search(r'\b(tariff|duty|import|export|trade)\b', combined_text):
        return "obvious_no", "Medical/health/sports-focused, not trade-related"
    
    # Check 7: STRICT - Federal HR/personnel policy = OBVIOUS NO
    if re.search(r'\b(schedule\s+policy|career|excepted service|federal.*employee|civil service)\b', combined_text) and \
       not re.search(r'\b(tariff|duty|import|export|trade|customs)\b', combined_text):
        return "obvious_no", "Federal HR policy, not trade-related"
    
    # Check 8: STRICT - Arms/defense strategy but not import-specific = SEND TO OLLAMA
    if re.search(r'\b(arms transfer|defense.*strategy|military|weapons)\b', combined_text) and \
       not re.search(r'\b(tariff|duty|import|export|trade)\b', combined_text):
        return "high", "Defense-related but unclear trade impact"
    
    # Default: send to Ollama for analysis
    return "high", "Ambiguous - needs AI analysis"

def categorize_filtered_eos(filtered_eos, country, product_category):
    """
    Categorize EOs into three buckets:
    - obvious_yes: Skip Ollama, mark as relevant
    - high: Send to Ollama for analysis
    - obvious_no: Skip Ollama, mark as not relevant
    """
    
    obvious_yes = []
    needs_ollama = []
    obvious_no = []
    
    print(f"\nSmart pre-filtering {len(filtered_eos)} EOs for {country} - {product_category}...")
    print("=" * 80)
    
    for eo in filtered_eos:
        title = eo.get("title", "")
        full_text = eo.get("full_text", "")
        
        confidence, reason = smart_prefilter_eo(title, full_text, country, product_category)
        
        if confidence == "obvious_yes":
            obvious_yes.append(eo)
            print(f"✓✓ OBVIOUS YES: {title[:70]}")
            print(f"   Reason: {reason}\n")
        elif confidence == "obvious_no":
            obvious_no.append(eo)
            print(f"✗✗ OBVIOUS NO: {title[:70]}")
            print(f"   Reason: {reason}\n")
        else:
            needs_ollama.append(eo)
            print(f"? AMBIGUOUS: {title[:70]}")
            print(f"   Reason: {reason}\n")
    
    print("=" * 80)
    print(f"\nCategorization Results:")
    print(f"  Obvious YES (skip Ollama): {len(obvious_yes)}")
    print(f"  Needs Ollama analysis: {len(needs_ollama)}")
    print(f"  Obvious NO (skip Ollama): {len(obvious_no)}")
    print(f"  Total Ollama calls needed: {len(needs_ollama)}\n")
    
    return obvious_yes, needs_ollama, obvious_no

if __name__ == "__main__":
    from fed_register_fetcher import fetch_executive_orders
    from trade_filter import filter_executive_orders
    
    all_eos = fetch_executive_orders("2026-01-05", "2026-07-04")
    filtered_eos = filter_executive_orders(all_eos)
    
    obvious_yes, needs_ollama, obvious_no = categorize_filtered_eos(
        filtered_eos, "China", "semiconductors"
    )