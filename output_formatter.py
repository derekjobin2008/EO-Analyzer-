import json

def format_results(results, country, product_category):
    """
    Format analysis results into a readable report
    """
    
    print("\n" + "=" * 80)
    print(f"TRADE IMPACT ANALYSIS: {country.upper()} - {product_category.upper()}")
    print("=" * 80)
    
    if not results:
        print(f"\nNo relevant Executive Orders found affecting {country} imports of {product_category}.")
        return
    
    print(f"\nFound {len(results)} relevant Executive Order(s):\n")
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"[{i}] {result['title']}")
        print(f"{'='*80}")
        
        print(f"\nDocument Number: {result['document_number']}")
        print(f"Publication Date: {result['publication_date']}")
        print(f"URL: {result['html_url']}")
        
        # Handle both old and new format
        high_level = result.get('high_level_analysis', result.get('analysis', {}))
        structured = result.get('structured_impacts', {})
        
        # High-level relevance
        if high_level.get('relevance_reason'):
            print(f"\nRelevance: {high_level.get('relevance_reason', 'N/A')}")
        
        # Structured impacts
        if structured:
            print(f"\n--- STRUCTURED IMPACT DATA ---")
            
            # Tariff Mechanisms
            mechanisms = structured.get('tariff_mechanisms', [])
            if mechanisms:
                print(f"\nTariff/Import Mechanisms:")
                for mech in mechanisms:
                    print(f"  • Type: {mech.get('type', 'N/A')}")
                    if mech.get('rate'):
                        print(f"    Rate: {mech['rate']}%")
                    if mech.get('hts_codes'):
                        print(f"    HTS Codes: {', '.join(mech['hts_codes'])}")
                    print(f"    Description: {mech.get('description', 'N/A')}")
                    if mech.get('effective_date'):
                        print(f"    Effective: {mech['effective_date']}")
            
            # Impact Flags
            flags = structured.get('impact_flags', [])
            if flags:
                print(f"\nImpact Flags:")
                for flag in flags:
                    category = flag.get('category', 'N/A').upper()
                    flag_type = flag.get('type', 'unknown').upper()
                    severity = flag.get('severity', 'unknown').upper()
                    print(f"  • [{category}] ({flag_type}, {severity})")
                    print(f"    {flag.get('description', 'N/A')}")
                    if flag.get('affected_parties'):
                        print(f"    Affects: {', '.join(flag['affected_parties'])}")
            
            # Key Dates
            key_dates = structured.get('key_dates', {})
            if any(key_dates.values()):
                print(f"\nKey Dates:")
                if key_dates.get('effective_date'):
                    print(f"  • Effective: {key_dates['effective_date']}")
                if key_dates.get('implementation_deadline'):
                    print(f"  • Implementation Deadline: {key_dates['implementation_deadline']}")
                if key_dates.get('phase_in_schedule'):
                    print(f"  • Phase-in: {key_dates['phase_in_schedule']}")
            
            # Summary
            if structured.get('summary'):
                print(f"\nSummary: {structured['summary']}")
        
        # Fallback to high-level analysis if no structured data
        if not structured or not structured.get('has_trade_impacts'):
            analysis = high_level
            
            # Cost Impacts
            cost_impacts = analysis.get('cost_impacts', {})
            if cost_impacts.get('explicit') or cost_impacts.get('inferred'):
                print(f"\nCost Impacts:")
                
                explicit_costs = cost_impacts.get('explicit', [])
                if explicit_costs:
                    print(f"  EXPLICIT (directly stated):")
                    for cost in explicit_costs:
                        print(f"    • {cost}")
                
                inferred_costs = cost_impacts.get('inferred', [])
                if inferred_costs:
                    print(f"  INFERRED (implied by policy):")
                    for cost in inferred_costs:
                        print(f"    • {cost}")
            
            # Employment Impacts
            employment_impacts = analysis.get('employment_impacts', {})
            if employment_impacts.get('explicit') or employment_impacts.get('inferred'):
                print(f"\nEmployment Impacts:")
                
                explicit_emp = employment_impacts.get('explicit', [])
                if explicit_emp:
                    print(f"  EXPLICIT (directly stated):")
                    for emp in explicit_emp:
                        print(f"    • {emp}")
                
                inferred_emp = employment_impacts.get('inferred', [])
                if inferred_emp:
                    print(f"  INFERRED (implied by policy):")
                    for emp in inferred_emp:
                        print(f"    • {emp}")
            
            # Summary
            if analysis.get('summary'):
                print(f"\nSummary: {analysis['summary']}")
    
    print(f"\n{'='*80}")
    print(f"END OF REPORT")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    # Test with sample structured data
    test_results = [
        {
            "title": "Test EO",
            "document_number": "2026-00001",
            "publication_date": "2026-01-01",
            "html_url": "https://example.com",
            "high_level_analysis": {"relevant": True},
            "structured_impacts": {
                "has_trade_impacts": True,
                "tariff_mechanisms": [
                    {
                        "type": "ad_valorem_tariff",
                        "rate": 25,
                        "hts_codes": ["8471"],
                        "description": "25% tariff on semiconductors",
                        "effective_date": "2026-02-01",
                        "phase_in": "immediate"
                    }
                ],
                "impact_flags": [
                    {
                        "category": "import_cost",
                        "type": "explicit",
                        "severity": "high",
                        "description": "Direct 25% tariff increase",
                        "affected_parties": ["importers", "consumers"]
                    }
                ],
                "key_dates": {"effective_date": "2026-02-01"},
                "summary": "Direct tariff impact on semiconductors."
            }
        }
    ]
    
    format_results(test_results, "China", "semiconductors")