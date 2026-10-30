# StockPilot AI — Security Architecture & Threat Model

StockPilot AI handles sensitive market data API credentials, user portfolios, and automated prediction pipelines. This document details the security posture and controls.

---

## 1. Secrets Management & Credential Boundaries

- **Zero Client-Side Exposure**: External API secrets (`GROWW_API_KEY`, `GROWW_ACCESS_TOKEN`, `DRISHTI_API_KEY`, database credentials) are **strictly backend environment variables**. They are never passed to the frontend or included in `NEXT_PUBLIC_` prefixes.
- **Git Hygiene**: `.gitignore` strictly excludes `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`, and secret token artifacts.
- **Credential Masking in Logs**: Structured loggers (via Python standard `logging` / Loguru) automatically filter and redact tokens matching authorization header patterns or keys containing `TOKEN`, `KEY`, `SECRET`, `PASSWORD`.

---

## 2. API Security & Input Validation

- **Input Sanitization**: All endpoint inputs (query parameters, JSON request bodies) are validated through strict Pydantic v2 schemas with regex patterns on stock tickers (`^[A-Z0-9_\-\.]{1,20}$`) and date ranges.
- **Cross-Origin Resource Sharing (CORS)**: Configured via FastAPI `CORSMiddleware`. In production, origins are restricted to configured domain origins (`ALLOWED_ORIGINS`). In development, restricted to `http://localhost:3000`.
- **Rate Limiting**: Critical endpoints (backtests, model inference, paper order execution) implement leaky-bucket rate limiting to mitigate denial of service.

---

## 3. Defense Against Indirect Prompt Injection & Untrusted News

When integrating news text into language model summarization or analysis:
1. **News Text is Untrusted**: News headlines, body text, or corporate transcripts are treated as untrusted data inputs.
2. **Strict Delimiters & System Prompt Hardening**: News snippets are passed inside isolated data blocks (e.g. `<news_content>` XML tags).
3. **Control Flow Isolation**: LLMs are never granted tool execution capabilities or access to system commands based on instructions parsed from news articles.
4. **No Trading Execution via LLM**: Machine learning models calculate mathematical probabilities; paper orders and signal generation are strictly governed by deterministic Python strategy rules.

---

## 4. Paper Trading & Financial Safety Guardrails

- **No Live Brokerage Execution**: Live order placement via Groww or any broker is strictly disabled. The paper-trading engine writes simulated orders only to the internal database.
- **Idempotency Protection**: Every simulated order requires a client-generated `idempotency_key` (e.g. UUID). Repeated submissions within 60 seconds are safely rejected to prevent duplicate execution.
- **Capital & Risk Caps**: Virtual orders cannot exceed available virtual cash, and single-position exposure is capped (e.g., maximum 25% of virtual portfolio value).
