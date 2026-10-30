# StockPilot AI — Phased Implementation Plan

This roadmap tracks the end-to-end development of StockPilot AI across 10 structured phases. Each phase has concrete acceptance criteria that must be verified before proceeding to subsequent work.

---

## Phase Status Summary

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | Repository Audit, System Architecture & Documentation | **COMPLETED** |
| **Phase 1** | Application Foundation & Core Analytics Dashboard | **COMPLETED** |
| **Phase 2** | Groww Market Data Integration & Normalization | **NEXT UP** |
| **Phase 3** | Financial News & Corporate Disclosures Pipeline | PENDING |
| **Phase 4** | Quantitative Feature Engineering & ML Training Pipeline | PENDING |
| **Phase 5** | Model Inference, Probability Calibration & Signal Engine | PENDING |
| **Phase 6** | Backtesting Engine & Model Evaluation UI | PENDING |
| **Phase 7** | Paper Trading Simulator & Virtual Portfolio | PENDING |
| **Phase 8** | AI Research Assistant & Evidence Grounding | PENDING |
| **Phase 9** | Production Hardening, CI/CD & Deployment | PENDING |

---

## Detailed Phase Breakdown

### Phase 0 — Repository Audit and System Design
- **Deliverables**:
  - `docs/SYSTEM_DESIGN.md`
  - `docs/API_SPEC.md`
  - `docs/DATABASE_SCHEMA.md`
  - `docs/ML_DESIGN.md`
  - `docs/DATA_SOURCES.md`
  - `docs/SECURITY.md`
  - `IMPLEMENTATION_PLAN.md`
  - `TASKS.md`
  - `.env.example`
  - `README.md`
- **Acceptance Criteria**:
  - Complete architecture, API contracts, ER diagrams, ML target definitions, and security boundaries documented and verified against official Groww and news documentation.
  - Zero fabricated endpoints or inaccurate authentication parameters.

---

### Phase 1 — Application Foundation and Dashboard
- **Deliverables**:
  - Monorepo folder structure: `apps/web` (Next.js, Tailwind, TypeScript) and `services/api` (FastAPI, SQLAlchemy, Pydantic).
  - Modern dark financial dashboard theme with high-contrast typography, restrained green/red indicators, compact data density.
  - Core navigation pages: Overview, Screener, Stock Details, AI Research, Model Performance, Backtesting, Paper Trading, Settings & System Health.
  - API `/health` endpoint returning system status, database connectivity, and provider modes.
  - Explicitly labeled demo/simulated dataset for local development without live credentials.
  - Unit and integration tests for API schemas, health, and navigation routes.
- **Acceptance Criteria**:
  - Frontend runs cleanly on `localhost:3000` and connects to backend on `localhost:8000`.
  - Database connects and tables initialize cleanly.
  - Loading, error, and empty states exist for all pages.
  - Automated tests pass.

---

### Phase 2 — Groww Market Data Integration [COMPLETED]
- **Deliverables**:
  - Verified Groww adapter using official REST endpoints (`/v1/historical/candle/range`, `/v1/live-data/quote`).
  - Candle ingestion pipeline with OHLC validation, timestamp checking, and duplicate prevention.
  - Database persistence for historical candles with idempotent upsert.
  - Real-time quote polling with caching and rate limit handling.
  - Transparent fallback to verified synthetic demo data when `GROWW_ACCESS_TOKEN` is unset or session expired.
- **Acceptance Criteria**:
  - Unit tests with mocked Groww responses pass (9/9 in `test_groww_integration.py`).
  - Invalid candle relationships (High < Low, Low > Close) raise validation errors and are safely dropped.
  - Ingestion run metrics and stats recorded.

---


### Phase 3 — Financial News Integration [COMPLETED]
- **Deliverables**:
  - News adapter interface with support for Drishti API, official exchange announcements, and RSS feeds.
  - Deduplication pipeline using canonical URL normalization and SHA-256 content hashing.
  - Entity matching to map articles to tracked NSE/BSE stock instruments with word-boundary regex and company alias matching.
  - Financial sentiment scoring (-1.0 to +1.0) and corporate event categorization (EARNINGS, CONTRACT_WIN, REGULATORY, etc.).
  - Prevention of look-ahead leakage by enforcing `published_at <= first_seen_at <= prediction_time`.
- **Acceptance Criteria**:
  - Duplicate articles correctly rejected (0 duplicates inserted on re-run).
  - News timeline displayed in dashboard and stock pages with verified source links and sentiment tags.
  - Automated test suite passes (27/27 tests passing across the project).

---

### Phase 4 — Machine-Learning Training Pipeline [COMPLETED]
- **Deliverables**:
  - Historical dataset construction with purged walk-forward cross-validation.
  - Feature engineering (technical indicators, returns, volatility, news sentiment features).
  - Baseline, Logistic Regression, and LightGBM models.
  - Controlled experiment: Model A (Price-Only) vs. Model B (Price + News).
  - Probability calibration (Isotonic Regression / Platt scaling).
  - Evaluation reports (Brier score, Log loss, ROC-AUC, Reliability diagrams).
- **Acceptance Criteria**:
  - Reproducible training command outputting versioned model artifacts.
  - Zero forward-looking leakage.
  - Model metrics and comparative charts persisted and accessible via API.

---

### Phase 5 — Prediction and Signal API [COMPLETED]
- **Deliverables**:
  - Real-time inference service assembling latest features and scoring via calibrated model (`prediction_service.py`).
  - Deterministic strategy engine evaluating probability, expected return, and risk limits.
  - Signal classification: `BUY`, `HOLD`, `SELL`, `NO_TRADE`.
  - Explainability factors (top positive and negative feature attributions).
  - Persistence of prediction history with verification of model version.
- **Acceptance Criteria**:
  - End-to-end prediction request returns typed JSON with model version and factor breakdown.
  - Stale data automatically triggers `NO_TRADE` with explicit warning reason.
  - Full automated test suite passes (40/40 tests passing).

---

### Phase 6 — Backtesting and Model Evaluation UI [COMPLETED]
- **Deliverables**:
  - Historical backtesting engine simulating trades based on model signals (`backtesting_engine.py`).
  - Realistic transaction cost modeling (brokerage, STT, exchange fees, slippage, stamp duty, GST).
  - Performance statistics: CAGR, Sharpe ratio, Sortino ratio, Max Drawdown, Win Rate, Profit Factor.
  - Benchmark comparison against Nifty 50 and stock buy-and-hold equity.
  - Interactive backtest configuration, strategy presets, and closed trade logs visualization.
- **Acceptance Criteria**:
  - Backtest simulations are deterministic and reproducible.
  - Look-ahead bias prevention verified by automated test cases.
  - Full test suite passing (44/44 tests passing).

---

### Phase 7 — Paper Trading Simulator [COMPLETED]
- **Deliverables**:
  - Virtual portfolio state management (cash, positions, unrealized/realized P&L).
  - Idempotent order placement (`POST /api/v1/paper/orders`).
  - Order execution simulator with slippage and commission deduction.
  - Position sizing, cash balance overdraft protection, and sandbox reset (`POST /api/v1/paper/reset`).
  - Trade execution history and performance chart.
- **Acceptance Criteria**:
  - No connection to live brokerage order placement.
  - Repeated order submissions with the same idempotency key reject duplicates safely.
  - Full automated test suite passes (48/48 tests passing).

---

### Phase 8 — AI Research Assistant [COMPLETED]
- **Deliverables**:
  - Grounded question-answering assistant citing stored database records and news articles (`research_service.py`).
  - Context retrieval for company announcements, historical performance, and prediction factors.
  - Prompt injection defenses isolating external text and command overrides.
- **Acceptance Criteria**:
  - All factual claims include verifiable source citations.
  - Model never hallucinates prices or invents predictions without database confirmation.
  - Automated test suite passes (52/52 tests passing).

---

### Phase 9 — Production Hardening and Deployment [COMPLETED]
- **Deliverables**:
  - Multi-stage Dockerfiles and `docker-compose.yml` for unified local/production run.
  - Health checks, structured logging, and error tracking (`GET /api/v1/health`).
  - Security headers and CORS lockdown.
  - Comprehensive operational runbook (`docs/RUNBOOK.md`).
- **Acceptance Criteria**:
  - `docker compose up` starts full stack cleanly from scratch.
  - All automated tests pass (52/52 tests passing).
  - Automated test suite passes with high coverage.
