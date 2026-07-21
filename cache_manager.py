import json
import os
from datetime import datetime, timedelta

CACHE_FILE = "eo_cache.json"
CACHE_EXPIRY_DAYS = 1  # Cache expires after 1 day

def save_to_cache(eos, start_date, end_date):
    """
    Save fetched EOs to local cache file
    """
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "start_date": start_date,
        "end_date": end_date,
        "eos": eos
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f)
    
    print(f"✓ Cached {len(eos)} EOs to {CACHE_FILE}")

def load_from_cache(start_date, end_date):
    """
    Load EOs from cache if it exists and matches date range
    Returns EOs if valid cache exists, None otherwise
    """
    
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is expired
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cache_time > timedelta(days=CACHE_EXPIRY_DAYS):
            print("Cache expired (older than 1 day)")
            return None
        
        # Check if date range matches
        if cache_data['start_date'] != start_date or cache_data['end_date'] != end_date:
            print("Cache date range doesn't match requested dates")
            return None
        
        print(f"✓ Loaded {len(cache_data['eos'])} EOs from cache")
        return cache_data['eos']
    
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None

def clear_cache():
    """
    Clear the cache file
    """
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print("✓ Cache cleared")

if __name__ == "__main__":
    # Test
    test_eos = [{"title": "Test EO", "full_text": "Test content"}]
    save_to_cache(test_eos, "2026-01-01", "2026-07-01")
    loaded = load_from_cache("2026-01-01", "2026-07-01")
    print(f"Loaded: {loaded}")
