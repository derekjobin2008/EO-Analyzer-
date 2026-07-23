# EO Import Impact Analyzer

A web application that analyzes US Executive Orders to identify impacts on costs and employment for import businesses. It fetches real Executive Orders from the Federal Register, filters them for trade relevance, and uses AI (local Ollama/Mistral) to extract structured tariff and impact data.

## What It Does

Enter your import details and the tool will:

1. Fetch Executive Orders from the Federal Register API for your date range
2. Filter them for trade/tariff relevance using regex patterns
3. Pre-filter with smart regex to identify obviously relevant vs ambiguous orders
4. Analyze ambiguous orders with local AI (Ollama/Mistral) for relevance and impact
5. Extract structured data: tariff mechanisms, HTS codes, effective dates, cost impacts, employment impacts
6. Display everything in a sleek dark-mode dashboard with risk scores, charts, and recommendations

## Architecture

| Component | File | Purpose |
|-----------|------|---------|
| Frontend | index.html | Dark-mode web UI with toggle switch for Fast/Full AI mode |
| API | api.py | FastAPI backend that orchestrates the pipeline |
| Fetcher | fed_register_fetcher.py | Pulls EOs from Federal Register API + PDF text extraction |
| Filter | trade_filter.py | Regex-based trade/tariff keyword filtering |
| Pre-filter | smart_prefilter.py | Classifies EOs as obvious yes/no/ambiguous |
| AI Analyzer | ollama_analyzer.py | Ollama/Mistral relevance and impact analysis |
| Impact Extractor | impact_extractor.py | Structured JSON extraction from EO text |
| Cache | cache_manager.py | Caches Federal Register data for 1 day |
| CLI | main.py | Original terminal interface (still works) |

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama installed with mistral model pulled
- pip install fastapi uvicorn requests pdfplumber pycountry

### 1. Start Ollama

```bash
ollama serve
```

### 2. Start the Backend

In a new terminal:

```bash
cd /path/to/EO-Analyzer
python api.py
```

Backend runs at http://localhost:8000

### 3. Start the Frontend

In another new terminal:

```bash
cd /path/to/EO-Analyzer
python -m http.server 3000
```

Open http://localhost:3000 in your browser.

## Usage

1. Enter your import details:
   - Country you are importing FROM (e.g., China, Vietnam, Mexico)
   - Product category (e.g., semiconductors, textiles, steel)
   - Optional sector/industry
   - Date range (auto = last 6 months)

2. Choose Analysis Mode:
   - Fast Mode (default): Uses regex pre-filter only. Results in ~5-10 seconds. Good for quick scans.
   - Full AI Mode: Runs Ollama/Mistral analysis on each ambiguous EO. Results in ~2-5 minutes. More thorough and accurate.

3. Click "Run Analysis"

4. Review the dashboard:
   - Risk score (0-100)
   - Relevant Executive Orders with tariff rates and descriptions
   - Cost impact projections with before/after comparisons
   - Employment impact modeling
   - Strategic recommendations

## Fast Mode vs Full AI Mode

| | Fast Mode | Full AI Mode |
|---|---|---|
| Speed | ~5-10 seconds | ~2-5 minutes |
| Method | Regex pre-filter only | Ollama/Mistral AI analysis |
| Accuracy | Good for obvious cases | Better for nuanced/ambiguous EOs |
| Use case | Quick scans, frequent checks | Deep analysis, critical decisions |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | Health check |
| /api/analyze | POST | Main analysis endpoint |
| /api/health | GET | Service health |

POST /api/analyze body:

```json
{
  "country": "China",
  "product_category": "semiconductors",
  "sector": "automotive",
  "date_range": "auto",
  "fast_mode": true
}
```

## Data Sources

- Federal Register API (federalregister.gov) — official source for all Presidential documents
- Ollama (ollama.com) — local LLM inference using Mistral model

## File Structure

```
EO-Analyzer/
├── index.html              # Frontend web app
├── api.py                  # FastAPI backend
├── main.py                 # Original CLI tool
├── fed_register_fetcher.py # Federal Register API client
├── trade_filter.py         # Trade keyword filter
├── smart_prefilter.py      # Regex pre-classifier
├── ollama_analyzer.py      # AI relevance analyzer
├── impact_extractor.py     # Structured data extractor
├── cache_manager.py        # JSON cache manager
├── user_input.py           # CLI input handler
├── output_formatter.py     # CLI output formatter
└── eo_cache.json           # Local cache file
```

## Notes

- The Federal Register API is rate-limited. The tool includes 1-second delays between requests.
- PDF text extraction uses pdfplumber — some complex PDF layouts may not extract perfectly.
- Ollama must be running before starting the backend. The tool will retry connections up to 5 times.
- Cache expires after 1 day. Delete eo_cache.json to force a fresh fetch.

## License

MIT — use at your own risk. Not legal advice. Always consult a trade attorney for compliance decisions.
