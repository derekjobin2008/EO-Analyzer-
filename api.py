from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os

# Import your existing modules
from fed_register_fetcher import fetch_executive_orders
from trade_filter import filter_executive_orders
from smart_prefilter import categorize_filtered_eos
from ollama_analyzer import analyze_filtered_eos
from impact_extractor import extract_structured_impacts
from cache_manager import save_to_cache, load_from_cache

app = FastAPI(title="EO Import Impact Analyzer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Data Models ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    country: str
    product_category: str
    sector: Optional[str] = ""
    date_range: Optional[str] = "auto"
    fast_mode: Optional[bool] = False

class TariffMechanism(BaseModel):
    type: str
    rate: Optional[float] = None
    hts_codes: List[str] = []
    description: str
    effective_date: Optional[str] = None
    phase_in: Optional[str] = None

class ImpactFlag(BaseModel):
    category: str
    type: str
    severity: str
    description: str
    affected_parties: List[str] = []

class KeyDates(BaseModel):
    effective_date: Optional[str] = None
    implementation_deadline: Optional[str] = None
    phase_in_schedule: Optional[str] = None

class StructuredImpacts(BaseModel):
    has_trade_impacts: bool
    tariff_mechanisms: List[TariffMechanism] = []
    impact_flags: List[ImpactFlag] = []
    key_dates: KeyDates
    summary: Optional[str] = ""
    error: Optional[str] = None

class AnalysisResult(BaseModel):
    title: str
    document_number: Optional[str] = None
    publication_date: Optional[str] = None
    html_url: Optional[str] = None
    relevance_reason: Optional[str] = None
    structured_impacts: Optional[StructuredImpacts] = None
    analysis: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    query: Dict[str, str]
    summary: str
    risk_score: float
    executive_orders: List[AnalysisResult]
    cost_impacts: List[Dict[str, Any]]
    employment_impacts: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: str

# ─── Helper Functions ───────────────────────────────────────

def get_date_range(date_range_str: str) -> tuple:
    end = datetime.now()
    if date_range_str == "auto" or not date_range_str:
        start = end - timedelta(days=180)
    else:
        try:
            parts = date_range_str.replace(" to ", " ").split()
            start = datetime.strptime(parts[0], "%Y-%m-%d")
            end = datetime.strptime(parts[1], "%Y-%m-%d")
        except:
            start = end - timedelta(days=180)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def calculate_risk_score(results: List[Dict]) -> float:
    """Calculate risk score 0-100 based on tariff rates and impact severity"""
    score = 10  # base score

    for result in results:
        structured = result.get("structured_impacts", {})
        if not structured or not structured.get("has_trade_impacts"):
            continue

        # Tariff mechanisms contribute to score
        for mech in structured.get("tariff_mechanisms", []):
            rate = mech.get("rate", 0) or 0
            if rate >= 50:
                score += 25
            elif rate >= 25:
                score += 15
            elif rate > 0:
                score += 8
            else:
                score += 3  # non-rate mechanisms still add risk

        # Impact flags contribute
        for flag in structured.get("impact_flags", []):
            severity = flag.get("severity", "low")
            if severity == "high":
                score += 10
            elif severity == "medium":
                score += 5
            else:
                score += 2

    return min(100, score)

def generate_summary(results: List[Dict], country: str, product: str) -> str:
    """Generate a human-readable summary"""
    if not results:
        return f"No relevant Executive Orders found affecting {country} imports of {product}."

    total_eos = len(results)
    high_impact = sum(1 for r in results 
                      if any(f.get("severity") == "high" 
                             for f in r.get("structured_impacts", {}).get("impact_flags", [])))

    max_rate = 0
    for r in results:
        for mech in r.get("structured_impacts", {}).get("tariff_mechanisms", []):
            rate = mech.get("rate", 0) or 0
            max_rate = max(max_rate, rate)

    summary = f"Found {total_eos} relevant Executive Order(s) affecting {country} imports of {product}."

    if max_rate > 0:
        summary += f" Maximum tariff rate identified: {max_rate}%."

    if high_impact > 0:
        summary += f" {high_impact} EO(s) flagged with HIGH severity impacts on costs or employment."

    return summary

def calculate_cost_impacts(results: List[Dict], country: str, product: str) -> List[Dict]:
    """Derive cost impacts from structured data"""
    impacts = []

    # Base cost estimate (simplified model)
    base_costs = {"semiconductors": 500000, "textiles": 200000, "steel": 350000}
    base = base_costs.get(product.lower(), 250000)

    # Find all tariff rates
    total_rate = 0
    for r in results:
        for mech in r.get("structured_impacts", {}).get("tariff_mechanisms", []):
            rate = mech.get("rate", 0) or 0
            total_rate = max(total_rate, rate)  # use highest rate

    if total_rate > 0:
        current = base
        projected = base * (1 + total_rate / 100)
        increase = ((projected - current) / current) * 100
        annual = (projected - current) * 12

        impacts.append({
            "category": "Import Duties & Tariffs",
            "current_cost": round(current, 2),
            "projected_cost": round(projected, 2),
            "increase_pct": round(increase, 1),
            "annual_impact": round(annual, 2)
        })

    # Compliance cost (always present if there are trade impacts)
    if results:
        impacts.append({
            "category": "Compliance & Certification",
            "current_cost": round(base * 0.03, 2),
            "projected_cost": round(base * 0.08, 2),
            "increase_pct": 166.7,
            "annual_impact": round(base * 0.05 * 12, 2)
        })

    return impacts

def calculate_employment_impacts(results: List[Dict], country: str, product: str) -> List[Dict]:
    """Derive employment impacts from structured data"""
    base_jobs = {"semiconductors": 45, "textiles": 120, "steel": 80}.get(product.lower(), 60)

    # Check if any high severity impacts exist
    has_high = any(
        f.get("severity") == "high"
        for r in results
        for f in r.get("structured_impacts", {}).get("impact_flags", [])
    )

    if has_high:
        return [
            {
                "category": "Procurement & Sourcing",
                "current_jobs": base_jobs,
                "projected_jobs": int(base_jobs * 0.7),
                "risk_level": "High",
                "description": "Tariff increases may force supplier diversification and volume reduction."
            },
            {
                "category": "Compliance & Legal",
                "current_jobs": 5,
                "projected_jobs": 18,
                "risk_level": "Low (Growth)",
                "description": "Increased need for trade compliance specialists and tariff classification experts."
            },
            {
                "category": "Logistics & Warehousing",
                "current_jobs": 30,
                "projected_jobs": 22,
                "risk_level": "Medium",
                "description": "Shift to alternative suppliers may reduce country-specific logistics roles."
            }
        ]
    else:
        return [
            {
                "category": "Procurement & Sourcing",
                "current_jobs": base_jobs,
                "projected_jobs": int(base_jobs * 0.9),
                "risk_level": "Medium",
                "description": "Trade policy changes create moderate pressure to diversify suppliers."
            },
            {
                "category": "Compliance & Legal",
                "current_jobs": 3,
                "projected_jobs": 8,
                "risk_level": "Low (Growth)",
                "description": "Increased documentation requirements under new trade regulations."
            }
        ]

def generate_recommendations(results: List[Dict], country: str, product: str) -> List[str]:
    """Generate strategic recommendations based on results"""
    recs = []

    # Extract key mechanisms
    has_tariff = False
    has_hts = False
    has_section_232 = False
    has_section_301 = False

    for r in results:
        for mech in r.get("structured_impacts", {}).get("tariff_mechanisms", []):
            has_tariff = True
            if mech.get("hts_codes"):
                has_hts = True
            desc = mech.get("description", "").lower()
            if "section 232" in desc or "232" in desc:
                has_section_232 = True
            if "section 301" in desc or "301" in desc:
                has_section_301 = True

    if has_tariff:
        recs.append("Review HTS code classifications for your products to ensure accurate tariff calculations.")

    if has_section_232:
        recs.append("Investigate Section 232 exemptions for your product category (e.g., US data center use, R&D, startup applications).")

    if has_section_301:
        recs.append("Monitor Section 301 investigation timelines — delayed tariffs may be implemented with short notice.")

    if country.lower() == "china":
        recs.append("Track the November 10, 2026 suspension deadline for reciprocal tariffs.")
        recs.append("Consider the Taiwan-US agreement for tariff exemptions on US-produced chips.")

    recs.append("Evaluate long-term supplier contracts with tariff escalation clauses.")
    recs.append("Document all trade compliance procedures for potential duty drawback claims.")

    return recs

# ─── API Endpoints ──────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "EO Import Impact Analyzer API", "version": "2.0.0", "status": "running"}

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_impact(req: AnalyzeRequest):
    country = req.country.strip()
    product = req.product_category.strip()
    sector = req.sector.strip() if req.sector else None
    start_date, end_date = get_date_range(req.date_range)

    print(f"\n{'='*80}")
    print(f"API REQUEST: {country} - {product} ({sector or 'no sector'})")
    print(f"Date range: {start_date} to {end_date}")
    print(f"{'='*80}\n")

    # Step 1: Try cache
    print("Step 1: Checking cache...")
    cached_eos = load_from_cache(start_date, end_date)

    if cached_eos is None:
        print("Step 2: Fetching from Federal Register...")
        all_eos = fetch_executive_orders(start_date, end_date)
        save_to_cache(all_eos, start_date, end_date)
    else:
        all_eos = cached_eos
        print("Step 2: Using cached EOs")

    # Step 2: Filter for trade/tariff EOs
    print(f"\nStep 3: Filtering {len(all_eos)} EOs for trade relevance...")
    filtered_eos = filter_executive_orders(all_eos)

    if not filtered_eos:
        return AnalysisResponse(
            query={"country": country, "product_category": product, "sector": sector or "", "date_range": f"{start_date} to {end_date}"},
            summary=f"No trade-related Executive Orders found for {country} - {product} in the specified date range.",
            risk_score=0,
            executive_orders=[],
            cost_impacts=[],
            employment_impacts=[],
            recommendations=["No trade-related EOs found. Consider broadening your date range or checking for very recent orders."],
            generated_at=datetime.now().isoformat()
        )

    # Step 3: Smart pre-filter
    print(f"\nStep 4: Smart pre-filtering {len(filtered_eos)} EOs...")
    obvious_yes, needs_ollama, obvious_no = categorize_filtered_eos(
        filtered_eos, country, product
    )

    # Step 4: Build results list
    all_results = []

    # Obvious yes EOs
    for eo in obvious_yes:
        all_results.append({
            "title": eo.get("title"),
            "document_number": eo.get("document_number"),
            "publication_date": eo.get("publication_date"),
            "html_url": eo.get("html_url"),
            "relevance_reason": "Directly impacts tariffs/duties on imports",
            "eo_object": eo
        })

    # Ollama analysis for ambiguous EOs
    if needs_ollama:
        print(f"\nStep 5: Analyzing {len(needs_ollama)} ambiguous EOs with Ollama...")
        ollama_results = analyze_filtered_eos(needs_ollama, country, product, sector)

        for result in ollama_results:
            all_results.append({
                "title": result["title"],
                "document_number": result["document_number"],
                "publication_date": result["publication_date"],
                "html_url": result["html_url"],
                "analysis": result.get("analysis", {}),
                "eo_object": next((eo for eo in filtered_eos if eo["title"] == result["title"]), None)
            })

    # Step 5: Extract structured impacts (SKIP in fast mode)
    if req.fast_mode:
        print(f"\nFAST MODE: Skipping Ollama impact extraction. Using pre-filter data only.")
        print("=" * 80)

        final_results = []
        for result in all_results:
            # Build synthetic structured data from pre-filter info
            clean_result = {k: v for k, v in result.items() if k != "eo_object"}

            # Add basic structured impacts based on pre-filter classification
            clean_result["structured_impacts"] = {
                "has_trade_impacts": True,
                "tariff_mechanisms": [
                    {
                        "type": "trade_restriction",
                        "rate": None,
                        "hts_codes": [],
                        "description": clean_result.get("relevance_reason", "Trade-related executive order identified by pre-filter"),
                        "effective_date": clean_result.get("publication_date"),
                        "phase_in": None
                    }
                ],
                "impact_flags": [
                    {
                        "category": "import_cost",
                        "type": "inferred",
                        "severity": "medium",
                        "description": f"Potential impact on {country} imports of {product}",
                        "affected_parties": ["importers", "manufacturers"]
                    }
                ],
                "key_dates": {
                    "effective_date": clean_result.get("publication_date"),
                    "implementation_deadline": None,
                    "phase_in_schedule": None
                },
                "summary": f"EO related to trade/tariffs affecting {country} - {product}. Full AI analysis disabled in fast mode."
            }
            final_results.append(clean_result)
    else:
        print(f"\nStep 6: Extracting structured impacts from {len(all_results)} EOs...")
        print("=" * 80)

        final_results = []
        for i, result in enumerate(all_results):
            title = result["title"]
            eo_obj = result.get("eo_object")

            if eo_obj:
                print(f"\n[{i+1}/{len(all_results)}] Extracting: {title[:70]}...")
                structured = extract_structured_impacts(
                    title,
                    eo_obj.get("full_text", ""),
                    country,
                    product
                )
                result["structured_impacts"] = structured

                if structured.get("has_trade_impacts"):
                    mechs = len(structured.get("tariff_mechanisms", []))
                    flags = len(structured.get("impact_flags", []))
                    print(f"  ✓ Found {mechs} mechanism(s), {flags} impact flag(s)")
                else:
                    print(f"  ✗ No structured impacts")

            # Clean up for response (remove eo_object)
            clean_result = {k: v for k, v in result.items() if k != "eo_object"}
            final_results.append(clean_result)

    # Step 6: Calculate derived metrics
    risk_score = calculate_risk_score(final_results)
    summary = generate_summary(final_results, country, product)
    cost_impacts = calculate_cost_impacts(final_results, country, product)
    employment_impacts = calculate_employment_impacts(final_results, country, product)
    recommendations = generate_recommendations(final_results, country, product)

    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE: Risk Score = {risk_score}/100")
    print(f"{'='*80}\n")

    return AnalysisResponse(
        query={
            "country": country,
            "product_category": product,
            "sector": sector or "",
            "date_range": f"{start_date} to {end_date}"
        },
        summary=summary,
        risk_score=risk_score,
        executive_orders=final_results,
        cost_impacts=cost_impacts,
        employment_impacts=employment_impacts,
        recommendations=recommendations,
        generated_at=datetime.now().isoformat()
    )

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)