from fed_register_fetcher import fetch_executive_orders
from trade_filter import filter_executive_orders
from smart_prefilter import categorize_filtered_eos
from ollama_analyzer import analyze_filtered_eos
from impact_extractor import extract_structured_impacts
from user_input import get_user_inputs
from output_formatter import format_results
from cache_manager import save_to_cache, load_from_cache

def main():
    """
    Main orchestrator: runs the complete pipeline with caching and smart filtering
    """
    
    # Step 1: Get user inputs
    print("\n")
    country, product_category, sector, start_date, end_date = get_user_inputs()
    
    # Step 2: Try to load from cache
    print(f"\nStep 1: Checking cache...")
    cached_eos = load_from_cache(start_date, end_date)
    
    if cached_eos is None:
        # Step 3: Fetch executive orders
        print(f"Step 2: Fetching executive orders from {start_date} to {end_date}...")
        all_eos = fetch_executive_orders(start_date, end_date)
        save_to_cache(all_eos, start_date, end_date)
    else:
        all_eos = cached_eos
        print(f"Step 2: Skipped (using cache)")
    
    # Step 4: Pass 1 filter (keywords)
    print(f"\nStep 3: Filtering for trade/tariff-related orders...")
    filtered_eos = filter_executive_orders(all_eos)
    
    # Step 5: Smart pre-filter (obvious yes/no, ambiguous)
    print(f"\nStep 4: Smart pre-filtering...")
    obvious_yes, needs_ollama, obvious_no = categorize_filtered_eos(
        filtered_eos, country, product_category
    )
    
    # Step 6: Convert obvious_yes to results format (these are definitely relevant)
    obvious_results = []
    for eo in obvious_yes:
        obvious_results.append({
            "title": eo.get("title"),
            "document_number": eo.get("document_number"),
            "publication_date": eo.get("publication_date"),
            "html_url": eo.get("html_url"),
            "high_level_analysis": {
                "relevant": True,
                "relevance_reason": "Directly impacts tariffs/duties on imports",
            },
            "eo_object": eo  # Keep full EO for later extraction
        })
    
    # Step 7: Ollama analysis for ambiguous ones
    if needs_ollama:
        print(f"\nStep 5: Analyzing {len(needs_ollama)} ambiguous EOs with AI...")
        ollama_results = analyze_filtered_eos(needs_ollama, country, product_category, sector)
    else:
        print(f"\nStep 5: No ambiguous EOs to analyze")
        ollama_results = []
    
    # Step 8: Combine results
    all_results = obvious_results + ollama_results
    
    # Step 9: Extract structured impacts from all relevant EOs
    print(f"\nStep 6: Extracting structured impact data...")
    print("=" * 80)
    
    for i, result in enumerate(all_results):
        title = result['title']
        eo_obj = result.get('eo_object') or next((eo for eo in filtered_eos if eo['title'] == title), None)
        
        if eo_obj:
            print(f"\n[{i+1}/{len(all_results)}] Extracting impacts from: {title[:70]}...")
            structured_data = extract_structured_impacts(
                title,
                eo_obj.get('full_text', ''),
                country,
                product_category
            )
            result['structured_impacts'] = structured_data
            
            if structured_data.get('has_trade_impacts'):
                mechanisms = len(structured_data.get('tariff_mechanisms', []))
                flags = len(structured_data.get('impact_flags', []))
                print(f"  ✓ Found {mechanisms} mechanism(s), {flags} impact flag(s)")
            else:
                print(f"  ✗ No structured impacts extracted")
        
        import time
        time.sleep(1)
    
    # Step 10: Format and display results
    print(f"\nStep 7: Formatting results...")
    format_results(all_results, country, product_category)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user.")
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()