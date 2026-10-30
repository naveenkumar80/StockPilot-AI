# StockPilot AI — REST API Specification

Version: **1.0.0**  
Base Path: `/api/v1`  
Protocol: `HTTP/1.1`, `HTTP/2` over TLS  
Content Type: `application/json`

---

## 1. Authentication & Common Headers

### Headers
| Header | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `Authorization` | `Bearer <token>` | Session / API token for protected routes | Conditional |
| `X-Request-Id` | `UUID` | Request tracing identifier | Optional |
| `Content-Type` | `application/json` | Request payload format | Required for POST/PUT |

### Standard Error Response Format
All 4xx and 5xx responses conform to RFC 7807 problem details:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Stock with symbol 'UNKNOWN' not found in universe.",
    "details": {},
    "timestamp": "2026-10-28T14:30:00Z",
    "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
  }
}
```

---

## 2. Core Endpoints Overview

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service and provider health status | Public |
| `GET` | `/market/overview` | Macro market overview, indices, active signals count | Public |
| `GET` | `/stocks` | Searchable and filterable stock universe screener | Public |
| `GET` | `/stocks/{symbol}` | Deep details for a single stock | Public |
| `GET` | `/stocks/{symbol}/candles` | Historical OHLCV candles | Public |
| `GET` | `/stocks/{symbol}/news` | Verified company-related news & announcements | Public |
| `GET` | `/stocks/{symbol}/prediction`| Real-time or latest ML prediction for a stock | Public |
| `GET` | `/predictions` | Historical predictions feed with pagination | Public |
| `GET` | `/models/status` | Registered models status and training metadata | Public |
| `GET` | `/models/metrics` | Out-of-sample evaluation metrics & calibration | Public |
| `POST`| `/backtests` | Launch a reproducible historical strategy backtest | User |
| `GET` | `/backtests/{id}` | Retrieve backtest execution results & equity curve | User |
| `GET` | `/watchlists` | Get user watchlists | User |
| `POST`| `/watchlists` | Create a new watchlist | User |
| `POST`| `/watchlists/{id}/items` | Add stock to a watchlist | User |
| `GET` | `/paper/portfolio` | Get virtual portfolio balance, positions, & P&L | User |
| `POST`| `/paper/orders` | Place idempotent simulated order | User |
| `GET` | `/paper/orders` | Retrieve simulated order history | User |
| `GET` | `/paper/trades` | Retrieve simulated executions history | User |

---

## 3. Detailed Endpoint Contracts

### 3.1 Health Check
**`GET /api/v1/health`**
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-10-28T14:30:00Z",
  "environment": "development",
  "integrations": {
    "database": { "status": "connected", "latency_ms": 1.2 },
    "groww_api": { "status": "ready", "authenticated": false, "mode": "demo" },
    "news_provider": { "status": "ready", "provider": "drishti_rss", "last_ingest": "2026-10-28T12:00:00Z" },
    "model_engine": { "status": "loaded", "active_version": "v1.0.0-lgbm" }
  }
}
```

---

### 3.2 Market Overview
**`GET /api/v1/market/overview`**
- **Response `200 OK`**:
```json
{
  "as_of": "2026-10-28T14:30:00Z",
  "market_status": "CLOSED",
  "monitored_stocks_count": 50,
  "data_source_mode": "demo",
  "last_successful_market_update": "2026-10-28T10:00:00Z",
  "latest_model_training": "2026-10-27T18:00:00Z",
  "active_signals_summary": {
    "BUY": 14,
    "HOLD": 22,
    "SELL": 8,
    "NO_TRADE": 6
  },
  "paper_portfolio_snapshot": {
    "total_value": 1054200.00,
    "cash_balance": 642100.00,
    "unrealized_pnl": 54200.00,
    "unrealized_pnl_pct": 5.42
  },
  "recent_predictions": [
    {
      "symbol": "RELIANCE",
      "signal": "BUY",
      "probability_up": 0.68,
      "expected_return": 0.024,
      "horizon": "5d",
      "as_of": "2026-10-28T09:15:00Z"
    }
  ]
}
```

---

### 3.3 Stock Screener Universe
**`GET /api/v1/stocks`**
- **Query Parameters**:
  - `query` (string, optional): Search symbol or company name
  - `exchange` (string, optional): `NSE` or `BSE`
  - `signal` (string, optional): `BUY`, `HOLD`, `SELL`, `NO_TRADE`
  - `min_probability` (float, optional): e.g. `0.60`
  - `sort_by` (string, optional): `probability_up`, `momentum`, `volatility`, `symbol`, `price`
  - `sort_order` (string, optional): `asc` or `desc`
  - `page` (int, default: 1): Page number
  - `page_size` (int, default: 20): Items per page

- **Response `200 OK`**:
```json
{
  "items": [
    {
      "symbol": "TCS",
      "company_name": "Tata Consultancy Services Ltd",
      "exchange": "NSE",
      "last_price": 4120.50,
      "change_24h": 1.25,
      "volume_24h": 1845200,
      "signal": "BUY",
      "probability_up": 0.71,
      "expected_return": 0.031,
      "volatility_20d": 0.14,
      "momentum_5d": 0.022,
      "news_sentiment_score": 0.42,
      "risk_level": "LOW",
      "as_of": "2026-10-28T14:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

### 3.4 Historical Candles
**`GET /api/v1/stocks/{symbol}/candles`**
- **Query Parameters**:
  - `interval` (string, default: `1d`): `5m`, `15m`, `60m`, `1d`
  - `start_date` (string, ISO-8601): e.g. `2026-01-01`
  - `end_date` (string, ISO-8601): e.g. `2026-10-28`

- **Response `200 OK`**:
```json
{
  "symbol": "TCS",
  "exchange": "NSE",
  "interval": "1d",
  "source": "demo_groww_normalized",
  "candles": [
    {
      "timestamp": "2026-10-27T03:45:00Z",
      "open": 4080.00,
      "high": 4145.00,
      "low": 4072.00,
      "close": 4120.50,
      "volume": 1284500
    }
  ]
}
```

---

### 3.5 Prediction Engine Output
**`GET /api/v1/stocks/{symbol}/prediction`**
- **Response `200 OK`**:
```json
{
  "symbol": "TCS",
  "exchange": "NSE",
  "as_of": "2026-10-28T14:30:00Z",
  "forecast_horizon": "5_trading_sessions",
  "model_version": "v1.0.0-lgbm-price-news",
  "probability_up": 0.71,
  "probability_down": 0.29,
  "expected_return": 0.031,
  "expected_return_interval": [0.008, 0.054],
  "signal": "BUY",
  "risk_level": "LOW",
  "supporting_factors": [
    "5-session momentum is +2.2% with RSI at 54.2 (constructive consolidation)",
    "Recent Q3 earnings announcement sentiment score +0.65",
    "Trading above 20-day and 50-day EMAs"
  ],
  "contradicting_factors": [
    "Sector IT index showing slight divergence over past 2 sessions"
  ],
  "data_quality_status": "VERIFIED_FRESH",
  "news_summary": "TCS reported high double-digit cloud order pipeline growth and announced a new multi-year transformation engagement.",
  "limitations": [
    "Evaluated on historical walk-forward windows; forward returns are probabilistic estimates, not guarantees."
  ]
}
```

---

### 3.6 Backtesting Execution
**`POST /api/v1/backtests`**
- **Request Body**:
```json
{
  "symbol": "TCS",
  "start_date": "2025-01-01",
  "end_date": "2026-09-30",
  "initial_capital": 1000000.0,
  "model_version": "v1.0.0-lgbm",
  "strategy_params": {
    "buy_threshold": 0.65,
    "sell_threshold": 0.40,
    "stop_loss_pct": 0.03,
    "take_profit_pct": 0.06,
    "transaction_cost_pct": 0.0003,
    "slippage_pct": 0.0005
  }
}
```

- **Response `201 Created`**:
```json
{
  "backtest_id": "bkt-9f201e7a-3341-43e5",
  "status": "COMPLETED",
  "summary": {
    "total_return_pct": 24.8,
    "annualized_return_pct": 18.2,
    "benchmark_return_pct": 12.4,
    "max_drawdown_pct": -6.4,
    "sharpe_ratio": 1.84,
    "win_rate_pct": 62.5,
    "total_trades": 32,
    "profit_factor": 1.95,
    "total_fees_paid": 3240.00
  },
  "equity_curve": [
    { "date": "2025-01-01", "equity": 1000000.0, "benchmark_equity": 1000000.0 }
  ]
}
```

---

### 3.7 Paper Trading Simulated Order
**`POST /api/v1/paper/orders`**
- **Request Body**:
```json
{
  "idempotency_key": "ord-20261028-tcs-001",
  "symbol": "TCS",
  "side": "BUY",
  "quantity": 25,
  "order_type": "MARKET"
}
```

- **Response `201 Created`**:
```json
{
  "order_id": "ord-883a-4421",
  "idempotency_key": "ord-20261028-tcs-001",
  "symbol": "TCS",
  "side": "BUY",
  "quantity": 25,
  "executed_price": 4122.50,
  "transaction_fee": 30.92,
  "status": "FILLED",
  "executed_at": "2026-10-28T14:30:05Z"
}
```
