import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.models.prediction import ModelRegistry, Prediction
from app.models.paper_trading import PaperPortfolio, PaperPosition, PaperOrder

# Representative Indian Equities (Nifty 50 constituents across key sectors)
SAMPLE_STOCKS = [
    {"symbol": "RELIANCE", "company_name": "Reliance Industries Ltd", "sector": "Energy / Conglomerate", "price": 2845.50, "signal": "BUY", "prob": 0.72, "ret": 0.034, "vol": 0.16, "mom": 0.028, "risk": "LOW"},
    {"symbol": "TCS", "company_name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "price": 4120.25, "signal": "BUY", "prob": 0.69, "ret": 0.026, "vol": 0.14, "mom": 0.019, "risk": "LOW"},
    {"symbol": "INFY", "company_name": "Infosys Ltd", "sector": "Information Technology", "price": 1825.80, "signal": "HOLD", "prob": 0.54, "ret": 0.008, "vol": 0.18, "mom": -0.004, "risk": "MEDIUM"},
    {"symbol": "HDFCBANK", "company_name": "HDFC Bank Ltd", "sector": "Financial Services", "price": 1740.00, "signal": "BUY", "prob": 0.67, "ret": 0.029, "vol": 0.15, "mom": 0.021, "risk": "LOW"},
    {"symbol": "ICICIBANK", "company_name": "ICICI Bank Ltd", "sector": "Financial Services", "price": 1260.40, "signal": "BUY", "prob": 0.74, "ret": 0.038, "vol": 0.17, "mom": 0.032, "risk": "LOW"},
    {"symbol": "BHARTIARTL", "company_name": "Bharti Airtel Ltd", "sector": "Telecommunications", "price": 1690.10, "signal": "BUY", "prob": 0.68, "ret": 0.025, "vol": 0.13, "mom": 0.018, "risk": "LOW"},
    {"symbol": "ITC", "company_name": "ITC Ltd", "sector": "Consumer Goods / FMCG", "price": 485.60, "signal": "HOLD", "prob": 0.51, "ret": 0.004, "vol": 0.11, "mom": 0.002, "risk": "LOW"},
    {"symbol": "LT", "company_name": "Larsen & Toubro Ltd", "sector": "Capital Goods / Infrastructure", "price": 3610.00, "signal": "BUY", "prob": 0.71, "ret": 0.032, "vol": 0.19, "mom": 0.027, "risk": "MEDIUM"},
    {"symbol": "HINDUNILVR", "company_name": "Hindustan Unilever Ltd", "sector": "Consumer Goods / FMCG", "price": 2410.50, "signal": "SELL", "prob": 0.36, "ret": -0.018, "vol": 0.12, "mom": -0.015, "risk": "LOW"},
    {"symbol": "SBIN", "company_name": "State Bank of India", "sector": "Public Sector Banking", "price": 815.30, "signal": "HOLD", "prob": 0.58, "ret": 0.012, "vol": 0.21, "mom": 0.009, "risk": "MEDIUM"},
    {"symbol": "TATAMOTORS", "company_name": "Tata Motors Ltd", "sector": "Automobile", "price": 880.20, "signal": "NO_TRADE", "prob": 0.49, "ret": 0.001, "vol": 0.28, "mom": -0.022, "risk": "HIGH"},
    {"symbol": "BAJFINANCE", "company_name": "Bajaj Finance Ltd", "sector": "Financial Services / NBFC", "price": 6940.00, "signal": "BUY", "prob": 0.65, "ret": 0.022, "vol": 0.22, "mom": 0.017, "risk": "MEDIUM"},
    {"symbol": "SUNPHARMA", "company_name": "Sun Pharmaceutical Industries Ltd", "sector": "Healthcare / Pharma", "price": 1890.00, "signal": "BUY", "prob": 0.70, "ret": 0.028, "vol": 0.15, "mom": 0.024, "risk": "LOW"},
    {"symbol": "MARUTI", "company_name": "Maruti Suzuki India Ltd", "sector": "Automobile", "price": 11450.00, "signal": "HOLD", "prob": 0.53, "ret": 0.006, "vol": 0.16, "mom": 0.003, "risk": "LOW"},
    {"symbol": "WIPRO", "company_name": "Wipro Ltd", "sector": "Information Technology", "price": 540.80, "signal": "SELL", "prob": 0.38, "ret": -0.015, "vol": 0.19, "mom": -0.018, "risk": "MEDIUM"}
]


def seed_database_if_empty(db: Session):
    existing_count = db.query(Instrument).count()
    if existing_count > 0:
        return

    # 1. Create Model Registry record
    model_reg = ModelRegistry(
        model_version="v1.0.0-lgbm",
        algorithm="LIGHTGBM",
        features_schema_version="schema_v1",
        training_start_date=datetime.utcnow() - timedelta(days=730),
        training_end_date=datetime.utcnow() - timedelta(days=30),
        artifact_path="./services/ml/artifacts/v1.0.0-lgbm.pkl",
        calibration_method="ISOTONIC",
        roc_auc=0.6420,
        brier_score=0.2180,
        log_loss=0.6210,
        is_active=1
    )
    db.add(model_reg)
    db.flush()

    # 2. Create Default Virtual Portfolio
    portfolio = PaperPortfolio(
        name="StockPilot Sandbox Virtual Fund",
        initial_capital=1000000.00,
        cash_balance=645000.00,
        total_equity=1054200.00
    )
    db.add(portfolio)
    db.flush()

    random.seed(42)

    for item in SAMPLE_STOCKS:
        inst = Instrument(
            symbol=item["symbol"],
            exchange="NSE",
            company_name=item["company_name"],
            sector=item["sector"],
            is_active=True
        )
        db.add(inst)
        db.flush()

        # Seed 90 daily candles using realistic geometric walk
        base_price = item["price"]
        current_p = base_price * 0.85
        now = datetime.utcnow().replace(hour=15, minute=30, second=0, microsecond=0)

        candles_to_insert = []
        for d in range(90, 0, -1):
            c_date = now - timedelta(days=d)
            if c_date.weekday() >= 5:  # skip weekends
                continue
            ret = random.gauss(0.0008, item["vol"] / 16.0)
            current_p = max(5.0, current_p * (1.0 + ret))
            day_high = current_p * (1.0 + abs(random.gauss(0.005, 0.004)))
            day_low = current_p * (1.0 - abs(random.gauss(0.005, 0.004)))
            day_open = day_low + (day_high - day_low) * random.random()
            vol = int(random.lognormvariate(14, 0.5))

            candles_to_insert.append(MarketCandle(
                instrument_id=inst.id,
                timestamp=c_date,
                interval="1d",
                open=round(day_open, 2),
                high=round(day_high, 2),
                low=round(day_low, 2),
                close=round(current_p, 2),
                volume=vol,
                source="demo_groww_mock"
            ))
        db.bulk_save_objects(candles_to_insert)

        # Seed realistic news item
        article = NewsArticle(
            url=f"https://verified-news.in/announcements/{inst.symbol.lower()}-corporate-update-2026",
            headline=f"{inst.company_name} reports strategic progress and updates outlook",
            summary=f"Key operational highlights and order pipeline review disclosed in regulatory filing for {inst.symbol}.",
            publisher="NSE Exchange Disclosures",
            source_type="EXCHANGE_FILING",
            published_at=now - timedelta(hours=random.randint(4, 72)),
            first_seen_at=now - timedelta(hours=random.randint(4, 72)),
            status="PROCESSED"
        )
        db.add(article)
        db.flush()

        db.add(NewsCompanyAssociation(
            article_id=article.id,
            instrument_id=inst.id,
            relevance_score=1.0
        ))

        sent_score = round(random.uniform(-0.1, 0.6) if item["signal"] == "BUY" else random.uniform(-0.5, 0.2), 3)
        db.add(NewsSentimentResult(
            article_id=article.id,
            sentiment_score=sent_score,
            sentiment_label="POSITIVE" if sent_score > 0.1 else ("NEGATIVE" if sent_score < -0.1 else "NEUTRAL"),
            confidence=0.88,
            event_category="EARNINGS" if "LTD" in inst.company_name.upper() else "CONTRACT",
            model_version="finbert-indic-v1"
        ))

        # Seed calibrated Prediction
        db.add(Prediction(
            instrument_id=inst.id,
            model_id=model_reg.id,
            as_of=now,
            forecast_horizon="5_trading_sessions",
            probability_up=item["prob"],
            probability_down=round(1.0 - item["prob"], 4),
            expected_return=item["ret"],
            signal=item["signal"],
            risk_level=item["risk"],
            supporting_factors=[
                f"Calibrated probability {item['prob']:.0%} meets threshold",
                f"5-session momentum is {item['mom']*100:+.1f}% with positive volume support",
                "Operating above 20-day exponential moving average"
            ],
            contradicting_factors=[
                "Sector dispersion observed over recent 3 trading sessions"
            ],
            data_quality_status="VERIFIED_FRESH",
            news_summary=f"Recent filings indicate constructive operational developments for {item['company_name']}."
        ))

    # Add virtual positions for top BUY symbols
    sample_buy_syms = ["RELIANCE", "TCS", "ICICIBANK"]
    for sym in sample_buy_syms:
        inst_match = db.query(Instrument).filter(Instrument.symbol == sym).first()
        if inst_match:
            stock_meta = next(s for s in SAMPLE_STOCKS if s["symbol"] == sym)
            qty = 50 if sym == "RELIANCE" else (30 if sym == "TCS" else 100)
            avg_price = stock_meta["price"] * 0.96
            curr_price = stock_meta["price"]
            unreal_pnl = (curr_price - avg_price) * qty
            db.add(PaperPosition(
                portfolio_id=portfolio.id,
                instrument_id=inst_match.id,
                quantity=qty,
                average_buy_price=round(avg_price, 2),
                current_price=round(curr_price, 2),
                unrealized_pnl=round(unreal_pnl, 2),
                realized_pnl=0.0
            ))

    db.commit()
