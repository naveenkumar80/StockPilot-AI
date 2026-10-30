# StockPilot AI — Operational Runbook & Deployment Guide

This document contains standard operating procedures, startup routines, model training schedules, and troubleshooting workflows for the StockPilot AI platform.

---

## 1. Quickstart & Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for containerized deployment)

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Key environment variables:
| Variable | Description | Default / Example |
|---|---|---|
| `ENVIRONMENT` | Runtime environment | `development` / `production` |
| `DATABASE_URL` | SQLite / PostgreSQL connection string | `sqlite:///./stockpilot.db` |
| `GROWW_API_KEY` | Groww API client key | Unset for verified demo mode |
| `GROWW_ACCESS_TOKEN` | Bearer token for authenticated Groww calls | Optional |
| `MODEL_ARTIFACTS_DIR` | Directory containing trained joblib models | `./services/ml/artifacts` |
| `ACTIVE_MODEL_VERSION`| Model identifier used for inference | `v1.0.0-lgbm` |

---

## 2. Running Services Locally

### One-Command Runner (Recommended)
Run any of the following from the workspace root to launch both the FastAPI backend and Next.js frontend concurrently with unified logs and automatic graceful shutdown on `Ctrl+C`:

```bash
# Python runner
python start.py

# Windows Command Prompt or File Explorer double-click
.\start.bat

# PowerShell script
.\start.ps1

# npm root script
npm run dev
```

To automatically launch the browser when ready:
```bash
python start.py --open
```

---

### Running Services Separately (Two Terminals)

#### Terminal 1: FastAPI Backend
```bash
# From workspace root
$env:PYTHONPATH = ".;services/api"
python -m uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000 --reload
```
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### Terminal 2: Next.js Frontend
```bash
cd apps/web
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 3. Containerized Deployment (Docker Compose)

Run the entire stack (PostgreSQL + FastAPI + Next.js):
```bash
docker compose up --build -d
```
Check container status:
```bash
docker compose ps
docker compose logs -f api
```

---

## 4. Machine Learning Retraining Pipeline

To retrain the LightGBM classifier with walk-forward cross-validation and probability calibration:
```bash
$env:PYTHONPATH = ".;services/api"
python services/ml/run_train.py --lookback-days 90 --splits 3 --output-version v1.0.0-lgbm
```

The script will:
1. Extract 90 days of verified candle data and lag-aligned news sentiment features.
2. Run purged walk-forward cross-validation with a 5-day embargo window (zero lookahead leakage).
3. Evaluate Baseline vs. Model A (Price-Only) vs. Model B (Price + News).
4. Calibrate probabilities via Isotonic Regression.
5. Save artifact to `services/ml/artifacts/v1.0.0-lgbm.joblib` and metrics to `_metrics.json`.
6. Update `models_registry` table in the database.

---

## 5. Automated Testing & Verification

Run the full automated test suite (52 tests covering all modules):
```bash
$env:PYTHONPATH = ".;services/api"
python -m pytest services/api/tests -v
```

Test breakdown:
- `test_api.py`: Core endpoints, health, market overview, instruments screener.
- `test_groww_integration.py`: Groww client, live quote parsing, candle validation, synchronization.
- `test_news_integration.py`: RSS adapter, Drishti adapter, URL deduplication, entity matcher, temporal leakage barrier.
- `test_ml_pipeline.py`: Technical indicators, news feature alignment, walk-forward CV, LightGBM training.
- `test_predictions.py`: Prediction service, staleness gates, deterministic strategy rules, explainability.
- `test_backtesting.py`: Historical simulation, Indian equity cost model (STT, GST, brokerage), Sharpe/CAGR.
- `test_paper_trading.py`: Idempotent order placement, cash balance, position tracking, sandbox reset.
- `test_research.py`: Prompt injection sanitization, grounded context retrieval, citation generation.

---

## 6. Operational Troubleshooting & Runbook

### Problem: Stale Quotes Warning (`NO_TRADE` Signal)
- **Cause**: Stock data hasn't updated for > 4 trading days.
- **Remedy**: Trigger an on-demand market candle sync:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/market/sync/RELIANCE?lookback_days=90"
  ```
  Or refresh prediction:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/predictions/RELIANCE/refresh"
  ```

### Problem: Reset Virtual Paper Trading Sandbox
To restore the virtual portfolio to ₹10,00,000 cash balance and clear all positions:
```bash
curl -X POST "http://localhost:8000/api/v1/paper/reset"
```
Or click the "Reset Sandbox (₹10L)" button on the Paper Trading UI page.

