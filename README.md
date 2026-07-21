EO Import Impact Analyzer
A web application that analyzes US Executive Orders to identify impacts on costs and employment for import businesses. It fetches real Executive Orders from the Federal Register, filters them for trade relevance, and uses AI (local Ollama/Mistral) to extract structured tariff and impact data.
What It Does
Enter your import details — country, product category, sector, and date range — and the tool will:
Fetch Executive Orders from the Federal Register API for your date range
Filter them for trade/tariff relevance using regex patterns
Pre-filter with smart regex to identify obviously relevant vs. ambiguous orders
Analyze ambiguous orders with local AI (Ollama/Mistral) for relevance and impact
Extract structured data: tariff mechanisms, HTS codes, effective dates, cost impacts, employment impacts
Display everything in a sleek dark-mode dashboard with risk scores, charts, and recommendations
Architecture
Table
Component	File	Purpose
Frontend	index.html	Dark-mode web UI with toggle switch for Fast/Full AI mode
API	api.py	FastAPI backend that orchestrates the pipeline
Fetcher	fed_register_fetcher.py	Pulls EOs from Federal Register API + PDF text extraction
Filter	trade_filter.py	Regex-based trade/tariff keyword filtering
Pre-filter	smart_prefilter.py	Classifies EOs as obvious yes/no/ambiguous
AI Analyzer	ollama_analyzer.py	Ollama/Mistral relevance and impact analysis
Impact Extractor	impact_extractor.py	Structured JSON extraction from EO text
Cache	cache_manager.py	Caches Federal Register data for 1 day
CLI	main.py	Original terminal interface (still works)
Quick Start
Prerequisites
Python 3.11+
Ollama installed with mistral model pulled
pip install fastapi uvicorn requests pdfplumber pycountry
1. Start Ollama
bash
ollama serve
2. Start the Backend
In a new terminal:
bash
cd /path/to/EO-Analyzer
python api.py
Backend runs at http://localhost:8000
3. Start the Frontend
In another new terminal:
bash
cd /path/to/EO-Analyzer
python -m http.server 3000
Open http://localhost:3000 in your browser.
