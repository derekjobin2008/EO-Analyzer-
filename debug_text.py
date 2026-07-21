from fed_register_fetcher import fetch_executive_orders

all_eos = fetch_executive_orders(months_back=6)

# Find the "Ending Certain Tariff Actions" EO
for eo in all_eos:
    if "tariff" in eo.get("title", "").lower():
        print(f"Title: {eo.get('title')}")
        print(f"Full text length: {len(eo.get('full_text', ''))}")
        print(f"First 500 characters of full_text:")
        print(eo.get('full_text', '')[:500])
        print("\n---\n")