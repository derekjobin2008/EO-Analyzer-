from datetime import datetime, timedelta

def get_user_inputs():
    """
    Prompt user for:
    - Importing country
    - Product category
    - Optional sector
    - Optional date range
    Returns tuple of (country, product_category, sector, start_date, end_date)
    """
    
    print("\n" + "=" * 80)
    print("EXECUTIVE ORDER TRADE IMPACT ANALYZER")
    print("=" * 80)
    print("\nThis tool analyzes US Executive Orders to identify impacts on")
    print("costs and employment for your import business.\n")
    
    # Country
    country = input("What country are you importing FROM? (e.g., China, Vietnam, Mexico): ").strip()
    if not country:
        country = "China"
        print(f"  Using default: {country}")
    
    # Product category
    product = input("What product category are you importing? (e.g., semiconductors, textiles, steel): ").strip()
    if not product:
        product = "semiconductors"
        print(f"  Using default: {product}")
    
    # Sector (optional)
    sector = input("What sector/industry? (optional, e.g., automotive, consumer electronics, construction): ").strip()
    if sector:
        print(f"  Sector: {sector}")
    else:
        sector = None
    
    # Date range (optional)
    print("\nDate Range (optional - defaults to last 6 months):")
    date_input = input("  Enter 'auto' for last 6 months, or custom range (format: YYYY-MM-DD to YYYY-MM-DD): ").strip()
    
    if date_input.lower() == 'auto' or not date_input:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*6)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        print(f"  Using last 6 months: {start_str} to {end_str}")
    else:
        try:
            parts = date_input.split(' to ')
            if len(parts) == 2:
                start_str = parts[0].strip()
                end_str = parts[1].strip()
                # Validate dates
                datetime.strptime(start_str, "%Y-%m-%d")
                datetime.strptime(end_str, "%Y-%m-%d")
                print(f"  Custom date range: {start_str} to {end_str}")
            else:
                raise ValueError("Invalid format")
        except Exception as e:
            print(f"  Invalid date format: {e}. Using last 6 months instead.")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30*6)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
    
    return country, product, sector, start_str, end_str

if __name__ == "__main__":
    country, product, sector, start_date, end_date = get_user_inputs()
    print(f"\nSearch Parameters:")
    print(f"  Country: {country}")
    print(f"  Product: {product}")
    print(f"  Sector: {sector if sector else 'Not specified'}")
    print(f"  Date Range: {start_date} to {end_date}")