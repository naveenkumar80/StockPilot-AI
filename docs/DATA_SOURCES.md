# StockPilot AI — Data Sources, Provider Integrations & Licensing

This document details verified external market data, news sources, credential requirements, rate limits, and fallback strategies.

---

## 1. Groww Trade API (Primary Market Data Provider)

Official Documentation:  
- Portal: [https://groww.in/trade-api/docs](https://groww.in/trade-api/docs)
- Historical Candles: [https://groww.in/trade-api/docs/curl/backtesting](https://groww.in/trade-api/docs/curl/backtesting)
- Live Market Data: [https://groww.in/trade-api/docs/curl/live-data](https://groww.in/trade-api/docs/curl/live-data)

### 1.1 Authentication & Configuration
- Groww utilizes Bearer Token authentication via standard HTTP headers:
  ```http
  Authorization: Bearer <GROWW_ACCESS_TOKEN>
  Accept: application/json
  X-API-VERSION: 1.0
  ```
- **Environment Variables**:
  ```bash
  GROWW_API_KEY=your_groww_api_key_here
  GROWW_ACCESS_TOKEN=your_groww_access_token_here
  GROWW_BASE_URL=https://api.groww.in/v1
  GROWW_TIMEOUT_SECONDS=15
  ```

### 1.2 Historical Candles Endpoint
- **URL**: `GET https://api.groww.in/v1/historical/candle/range` (or `/v1/historical/candles`)
- **Query Parameters**:
  - `exchange`: `NSE` or `BSE` (Required)
  - `segment`: `CASH` or `FNO` (Required)
  - `trading_symbol`: Instrument symbol e.g., `RELIANCE`, `TCS` (Required)
  - `start_time`: `yyyy-MM-dd HH:mm:ss` or epoch seconds (Required)
  - `end_time`: `yyyy-MM-dd HH:mm:ss` or epoch seconds (Required)
  - `interval_in_minutes`: Interval size e.g., `1`, `5`, `15`, `60`, `1440`
- **Response Structure**:
  ```json
  {
    "status": "SUCCESS",
    "payload": {
      "candles": [
        [1633072800, 150.10, 155.00, 145.00, 152.40, 10000]
      ],
      "start_time": "2025-01-01 09:15:00",
      "end_time": "2025-01-01 15:30:00",
      "interval_in_minutes": 1440
    }
  }
  ```
  *(Candle format: `[timestamp_epoch_sec, open, high, low, close, volume]`)*

### 1.3 Live Quote Snapshot Endpoint
- **URL**: `GET https://api.groww.in/v1/live-data/quote`
- **Query Parameters**:
  - `exchange`: `NSE` or `BSE`
  - `segment`: `CASH`
  - `trading_symbol`: e.g. `INFY`
- **Response Structure**:
  ```json
  {
    "status": "SUCCESS",
    "payload": {
      "last_price": 1820.50,
      "average_price": 1815.20,
      "day_change": 12.30,
      "day_change_perc": 0.68,
      "upper_circuit_limit": 2002.00,
      "lower_circuit_limit": 1638.00,
      "ohlc": "{open: 1810.00, high: 1835.00, low: 1805.00, close: 1820.50}",
      "depth": { "buy": [], "sell": [] },
      "last_trade_time": 1730112000000,
      "market_cap": 750000000000
    }
  }
  ```

### 1.4 Rate Limits & Quotas
- Live and historical APIs are accessible under Groww's Trade API subscription plan.
- Rate limit: Default 10 requests per second.
- **Demo Mode**: If `GROWW_ACCESS_TOKEN` is not provided, the adapter automatically activates a verified synthetic generator that produces realistic geometric Brownian motion candles with realistic NSE equity parameters and sets `"source": "demo_groww_mock"`.

---

## 2. Financial News & Regulatory Disclosures

### 2.1 Drishti (Manasija) API
- Documentation: [https://drishti.manasija.in/docs](https://drishti.manasija.in/docs)
- Specialization: Indian stock market earnings concall transcripts, corporate filings, results season tracking, and structured announcements for NSE/BSE companies.
- Environment Variable: `DRISHTI_API_KEY=your_drishti_key_here`

### 2.2 Exchange Announcements Feeds (NSE / BSE)
- Public regulatory filings under SEBI Listing Obligations and Disclosure Requirements (LODR).
- Types of filings: Board meetings, financial results, credit rating revisions, promoter pledge actions, litigations, contracts.

### 2.3 News Processing Rules
1. **Timestamp Separation**:
   - `published_at`: Stated publication time by provider/wire.
   - `first_seen_at`: Server timestamp when StockPilot AI first observed the item.
   - *Rule*: Features used for prediction at time $T$ must satisfy $\text{first\_seen\_at} \le T$.
2. **Entity Deduplication**:
   - Computes SHA-256 hash of normalized headline + publisher name.
   - Rejects duplicate stories within a 48-hour window.
3. **Sentiment & Event Taxonomy**:
   - Classification categories: `EARNINGS`, `DIVIDEND_OR_SPLIT`, `MANAGEMENT_CHANGE`, `CONTRACT_WIN`, `REGULATORY_PENALTY`, `MACRO_POLICY`, `GENERAL`.
