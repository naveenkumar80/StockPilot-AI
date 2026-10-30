# StockPilot AI 🚀
### Production-Minded AI-Powered Stock Analysis, Prediction & Paper Trading for Indian Equities (NSE/BSE)

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 1. Overview & Core Philosophy

StockPilot AI combines verified market data from the **Groww Trade API**, structured Indian corporate announcements/news, rigorous walk-forward machine learning models, deterministic strategy and risk management rules, and a virtual paper trading simulator.

> **Core Principle**: Machine learning generates numerical forecasts and calibrated probabilities. Language models (LLMs) summarize verified evidence and explain results, but **never invent market figures or fabricate predictions**.

---

## 2. Key Capabilities

- **Market Overview**: Macro status of Indian benchmarks (Nifty 50, Sensex), monitored equities, active signal distributions, and data freshness health indicators.
- **Stock Screener**: Real-time filtering across NSE/BSE equities by signal (`BUY`, `HOLD`, `SELL`, `NO_TRADE`), calibrated ML probability, 5-day expected return, volatility, and news sentiment score.
- **Stock Deep-Dive**: Interactive candlestick charts, technical indicators (RSI, MACD, Bollinger Bands), lag-aligned corporate news timeline, explainability factor attributions, and risk assessment.
- **Machine Learning Engine**: Forward 5-day return probability estimation with walk-forward validation, purging, embargoing, and probability calibration.
- **Deterministic Strategy Rules**: Separation of statistical probabilities from execution decisions. Signals respect risk caps, volatility limits, and minimum edge requirements.
- **Backtesting & Simulation**: Reproducible historical bar replay modeling realistic brokerage fees, STT, and slippage.
- **Paper Trading**: Virtual portfolio with cash balance accounting, idempotent simulated order placement, and position tracking.

---

## 3. Architecture & Repository Structure

```
stockpilot-ai/
├── apps/
│   └── web/                   # Next.js 15+ App Router, Tailwind CSS, TypeScript
│       ├── app/               # Pages: overview, screener, stock detail, backtesting, paper trading
│       ├── components/        # Reusable financial components, charts, navigation
│       └── lib/               # API clients, TanStack Query hooks, formatting utils
├── services/
│   ├── api/                   # FastAPI REST backend
│   │   ├── app/
│   │   │   ├── api/v1/        # Versioned route endpoints
│   │   │   ├── core/          # App settings, logging, middleware
│   │   │   ├── db/            # Database session, base model
│   │   │   ├── models/        # SQLAlchemy database models
│   │   │   ├── schemas/       # Pydantic v2 schemas
│   │   │   ├── services/      # Business logic: market data, predictions, paper trading
│   │   │   └── integrations/  # Groww API & News Provider adapters
│   │   └── tests/             # Automated test suite
│   └── ml/                    # Machine learning pipeline
│       ├── features/          # Technical indicators & news feature engineering
│       ├── training/          # Walk-forward cross validation & model trainers
│       └── artifacts/         # Model weights, schemas, and metrics
├── docs/                      # Architectural & design specifications
│   ├── SYSTEM_DESIGN.md
│   ├── API_SPEC.md
│   ├── DATABASE_SCHEMA.md
│   ├── ML_DESIGN.md
│   ├── DATA_SOURCES.md
│   └── SECURITY.md
├── IMPLEMENTATION_PLAN.md
├── TASKS.md
└── docker-compose.yml
```

---

## 4. Getting Started

### Prerequisites
- **Python**: 3.11+ (or Python 3.14)
- **Node.js**: v18+ (or v20+, v22+)
- **Docker & Docker Compose** (optional for containerized run)

### One-Command Runner (Starts Frontend + Backend Concurrently)
Run any one of the following commands from the project root:

```bash
# Option A: Python unified runner
python start.py

# Option B: Windows batch / double-click
.\start.bat

# Option C: PowerShell script
.\start.ps1

# Option D: npm root script
npm run dev
```

Options:
- Pass `--open` or `-o` to automatically open `http://localhost:3000` in your default browser once the backend health probe passes.
- Press **`Ctrl+C`** at any time to gracefully stop both services cleanly without leaving zombie background processes.

---

### Running Services Separately (Manual Option)
```bash
# Navigate to API service
cd services/api

# Install dependencies (or use active environment)
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at:  
- Interactive Swagger: `http://localhost:8000/docs`  
- OpenAPI Specification: `http://localhost:8000/openapi.json`

### Frontend Setup (`apps/web`)
```bash
# Navigate to web app
cd apps/web

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Dashboard will be accessible at `http://localhost:3000`.

---

## 5. External Credentials Configuration

If live credentials are provided in `.env`:
- `GROWW_ACCESS_TOKEN`: Enables live market quotes and candle data from Groww Trade API.
- `DRISHTI_API_KEY`: Enables Indian corporate disclosures and concall transcripts.

**Demo Mode**: When external credentials are not set, StockPilot AI seamlessly and transparently runs in **Demo Mode**, displaying verified synthetic market data and clearly labeling every response with `data_source: "demo"` so development and testing proceed without external blockers.

---

## 6. Safety & Risk Disclaimer

StockPilot AI is designed strictly for research, quantitative analysis, educational purposes, and paper trading. It **never connects to live brokerage order execution** and does not provide financial or investment advice.
