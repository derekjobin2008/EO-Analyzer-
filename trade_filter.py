import re
import pycountry

def get_all_country_patterns():
    """
    Generate regex patterns for ALL countries (195+)
    Includes country names, demonyms, and common variations
    """
    patterns = []
    
    # Get all countries from pycountry
    for country in pycountry.countries:
        name = country.name.lower()
        # Add the country name
        patterns.append(rf'\b{name}\b')
        
        # Add common demonyms (British, French, Chinese, etc.)
        demonym_map = {
            'China': 'chinese',
            'Japan': 'japanese',
            'India': 'indian',
            'Russia': ['russian', 'soviet'],
            'United States': ['american', 'us', 'usa'],
            'United Kingdom': ['british', 'uk'],
            'France': 'french',
            'Germany': 'german',
            'Spain': 'spanish',
            'Italy': 'italian',
            'Brazil': 'brazilian',
            'Mexico': 'mexican',
            'Canada': 'canadian',
            'South Korea': 'korean',
            'Vietnam': 'vietnamese',
            'Thailand': 'thai',
            'Turkey': 'turkish',
            'Iran': 'iranian',
        }
        
        if country.name in demonym_map:
            demonym = demonym_map[country.name]
            if isinstance(demonym, list):
                patterns.extend([rf'\b{d}\b' for d in demonym])
            else:
                patterns.append(rf'\b{demonym}\b')
    
    return patterns

def is_trade_tariff_eo(eo_title, eo_full_text, country_patterns):
    """
    Pass 1 filter: Lightweight keyword/regex screening for trade/tariff focus
    Returns True if EO appears to be trade/tariff related
    """
    
    if not eo_full_text:
        return False
    
    combined_text = (eo_title + " " + eo_full_text).lower()
    
    # Trade/tariff keywords
    trade_keywords = [
        r'\btariff',
        r'\bduty',
        r'\bimport',
        r'\bexport',
        r'\btrade',
        r'\bquota',
        r'\bcommercial',
        r'\btrading\s+partner',
        r'\bhts\s+code',
        r'\bsection\s+301',
        r'\bsection\s+232',
        r'\bsection\s+201',
        r'\bustr',
        r'\btrade\s+agreement',
        r'\btariff\s+rate',
        r'\bad\s+valorem',
        r'\bcustoms',
        r'\bcommerce\s+department',
        r'\bgoods\s+classification',
        r'\bnon-market\s+economy',
        r'\bdumping',
        r'\bcountervailing',
        r'\bsafeguard',
        r'\bnon-tariff\s+barrier',
        r'\bde\s+minimis',
    ]
    
    # Count keyword matches
    trade_matches = sum(1 for keyword in trade_keywords if re.search(keyword, combined_text))
    country_matches = sum(1 for pattern in country_patterns if re.search(pattern, combined_text))
    
    # Threshold: at least 2 trade keywords OR 1 trade keyword + 1 country mention
    is_trade_focused = trade_matches >= 2 or (trade_matches >= 1 and country_matches >= 1)
    
    return is_trade_focused

def filter_executive_orders(all_eos):
    """
    Filter EOs for trade/tariff focus
    Returns filtered list of EOs
    """
    
    print("Generating comprehensive country list...")
    country_patterns = get_all_country_patterns()
    print(f"  Found {len(country_patterns)} country/demonym patterns\n")
    
    filtered_eos = []
    
    for eo in all_eos:
        title = eo.get("title", "")
        full_text = eo.get("full_text", "")
        
        if is_trade_tariff_eo(title, full_text, country_patterns):
            filtered_eos.append(eo)
            print(f"✓ MATCH: {title[:70]}")
    
    print(f"\n{len(filtered_eos)}/{len(all_eos)} EOs are trade/tariff focused\n")
    
    return filtered_eos

if __name__ == "__main__":
    from fed_register_fetcher import fetch_executive_orders
    
    all_eos = fetch_executive_orders("2026-01-05", "2026-07-04")
    filtered = filter_executive_orders(all_eos)