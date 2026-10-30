# StockPilot AI — Tasks Checklist

This task board tracks the granular implementation steps across all project phases.

---

## Phase 0: Repository Audit & System Design
- [x] Inspect existing workspace, runtime versions, and system environment
- [x] Research official Groww Trading API documentation (historical candles, live quote endpoints, auth)
- [x] Research news provider documentation (Drishti API, exchange disclosures)
- [x] Author `docs/SYSTEM_DESIGN.md` with architecture, data flow, and subsystem breakdown
- [x] Author `docs/API_SPEC.md` with versioned REST endpoint contracts
- [x] Author `docs/DATABASE_SCHEMA.md` with ER diagrams, tables, indexes, and constraints
- [x] Author `docs/ML_DESIGN.md` with target definition, feature specs, walk-forward validation, and calibration
- [x] Author `docs/DATA_SOURCES.md` with Groww endpoints, news integrations, licensing, and quotas
- [x] Author `docs/SECURITY.md` with secret management, threat models, and prompt injection defense
- [x] Author `IMPLEMENTATION_PLAN.md` with phased roadmap and acceptance criteria
- [x] Author `.env.example` and `README.md`

---

## Phase 1: Application Foundation & Core Analytics Dashboard
- [x] Initialize repository structure (`apps/web`, `services/api`, `services/ml`, `infra`)
- [x] Set up Python environment and FastAPI project scaffolding
  - [x] `app/core/config.py` with environment variable loading
  - [x] `app/core/logging.py` with structured logging
  - [x] `app/db/session.py` with SQLAlchemy async session & SQLite/Postgres fallback
  - [x] `app/models/` declarative database models
  - [x] `app/schemas/` Pydantic v2 validation models
  - [x] `app/api/v1/` routes for health, market overview, stocks, predictions, paper trading
  - [x] Seed data service for verified demo stocks (Nifty 50 constituents: RELIANCE, TCS, INFY, HDFCBANK, etc.)
- [x] Set up Next.js frontend application (`apps/web`)
  - [x] Configure Tailwind CSS with dark financial palette
  - [x] Layout with sidebar navigation and header status indicators (market status, demo badge)
  - [x] Overview dashboard page (`/`)
  - [x] Stock screener page (`/screener`)
  - [x] Stock detail page (`/stocks/[symbol]`)
  - [x] AI Research page (`/research`)
  - [x] Model performance page (`/models`)
  - [x] Backtesting page (`/backtesting`)
  - [x] Paper trading page (`/paper-trading`)
  - [x] Settings & system health page (`/settings`)
- [x] Wire up API client and services
- [x] Write backend unit tests (pytest for health, stocks list, overview, seed data)
- [x] Run test suite and verify clean startup (FastAPI & Next.js production build pass 10/10 routes)

---

## Phase 2: Groww Market Data Integration
- [x] Implement `services/api/app/integrations/groww/client.py`
- [x] Implement historical candle fetcher with interval translation (`/v1/historical/candle/range`)
- [x] Implement live quote fetcher (`/v1/live-data/quote`)
- [x] Implement multi-symbol live quote streaming endpoint (`GET /api/v1/market/live-quotes`)
- [x] Implement OHLC relationship and timestamp validation (`CandleValidator`)
- [x] Implement candle ingestion and incremental sync worker (`CandleSyncService`)
- [x] Implement stateful random-walk micro-tick generator with NSE 0.05 tick size multiples (`mock_generator.py`)
- [x] Wire live market data polling loop (2.5s) with green/red tick-flash animations across Header indices (NIFTY 50, SENSEX, BANKNIFTY)
- [x] Connect Featured stock card, Top AI Picks, Market Movers, and My Watchlist to live quote stream
- [x] Implement dynamic paper portfolio evaluation based on live price ticks
- [x] Add live ticking IST seconds clock to sidebar and stock cards
- [x] Write integration unit tests with mocked responses (`test_groww_integration.py` - 17/17 passed)

---


## Phase 3: Financial News Integration [COMPLETED]
- [x] Implement news adapter interface `services/api/app/integrations/news/base.py`
- [x] Implement Drishti API and announcement adapters (`drishti_adapter.py`)
- [x] Implement financial RSS feed adapter for Indian business press (`rss_adapter.py`)
- [x] Implement article deduplication by canonical URL and SHA-256 content hash (`deduplicator.py`)
- [x] Implement entity matching for NSE/BSE symbols with company aliases and relevance scoring (`entity_matcher.py`)
- [x] Implement financial sentiment scoring and event categorization (`sentiment_engine.py`)
- [x] Implement end-to-end news ingestion pipeline with strict temporal leakage prevention (`pipeline.py`)
- [x] Implement REST API endpoints (`/api/v1/news/latest`, `/stock/{symbol}`, `/stats`, `/ingest`)
- [x] Wire live news feed and category filters into Next.js dashboard and stock detail pages
- [x] Write comprehensive unit & integration tests (`test_news_integration.py` - 10/10 passed, 27/27 total)

---

## Phase 4: Machine-Learning Training Pipeline [COMPLETED]
- [x] Implement dataset builder combining market candles and lag-aligned news features
- [x] Implement forward 5-day return target generator
- [x] Implement technical indicator calculations (RSI, MACD, Bollinger Bands, ATR)
- [x] Implement purged walk-forward cross-validation splitter
- [x] Implement Baseline Classifier, Logistic Regression, and LightGBM models
- [x] Implement Model A (Price-Only) vs Model B (Price + News) experiment
- [x] Implement probability calibration (Isotonic / Platt)
- [x] Implement model evaluation reporting (Brier score, Log loss, ROC-AUC)
- [x] Write tests for leakage prevention and reproducibility (33/33 tests passing)

---

## Phase 5: Prediction and Signal API [COMPLETED]
- [x] Implement real-time inference service in FastAPI (`services/api/app/services/prediction_service.py`)
- [x] Implement deterministic strategy rules (`BUY`, `HOLD`, `SELL`, `NO_TRADE`) with staleness and risk gates
- [x] Implement feature attribution / explainability factor generator (supporting and contradicting factors)
- [x] Persist prediction history to database (`predictions` table with model registry foreign keys)
- [x] Connect frontend dashboard and stock detail pages to live prediction endpoints and on-demand refresh
- [x] Write unit & integration tests for strategy rule thresholds, staleness gates, and endpoints (40/40 tests passing)

---

## Phase 6: Backtesting Engine & Model Evaluation UI [COMPLETED]
- [x] Implement event-driven backtesting simulator (`services/api/app/services/backtesting_engine.py`)
- [x] Implement realistic Indian regulatory fee and slippage models (Brokerage, STT, Exchange fees, GST, Stamp duty)
- [x] Calculate CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, Profit Factor
- [x] Implement equity curve and trade logs generation
- [x] Connect Backtesting UI with customizable strategy parameters and dynamic trade log table
- [x] Write accounting and simulation unit tests (`test_backtesting.py` - 4/4 passed)

---

## Phase 7: Paper Trading Simulator [COMPLETED]
- [x] Implement virtual portfolio manager with cash accounting (`app/api/v1/endpoints/paper.py`)
- [x] Implement idempotent simulated order placement (`POST /api/v1/paper/orders`)
- [x] Implement simulated trade execution and position tracking
- [x] Implement risk checks (overdraft prevention, position holding bounds, reset sandbox)
- [x] Connect Paper Trading UI with real-time portfolio updates and order execution logs
- [x] Write idempotency, overdraft, and duplicate submission tests (`test_paper_trading.py` - 4/4 passed)

---

## Phase 8: AI Research Assistant [COMPLETED]
- [x] Implement context retrieval service querying stored news, earnings, and predictions (`research_service.py`)
- [x] Implement prompt injection sanitization for external news text and user queries
- [x] Implement citation generator linking claims to database article IDs and exchange filings
- [x] Connect AI Research UI with structured answers and verifiable source references
- [x] Write prompt injection defense and grounded retrieval unit tests (`test_research.py` - 4/4 passed)

---

## Phase 9: Production Hardening and Deployment [COMPLETED]
- [x] Author production Dockerfiles and `docker-compose.yml` (`services/api/Dockerfile`, `apps/web/Dockerfile`)
- [x] Configure environment-specific configs and health probes (`GET /api/v1/health`)
- [x] Implement CORS hardening and standard security headers (`X-Content-Type-Options`, `X-Frame-Options`)
- [x] Add structured logging and error monitoring
- [x] Finalize operational runbooks and startup guides (`docs/RUNBOOK.md`)
- [x] Verify full project end-to-end test suite passes (52/52 tests passing)
