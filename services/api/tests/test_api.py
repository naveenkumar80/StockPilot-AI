def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "StockPilot AI"
    assert data["version"] == "1.0.0"


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "integrations" in data
    assert "database" in data["integrations"]
    assert "groww_api" in data["integrations"]
    assert "news_provider" in data["integrations"]
    assert "model_engine" in data["integrations"]


def test_market_overview(client):
    response = client.get("/api/v1/market/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["monitored_stocks_count"] > 0
    assert "active_signals_summary" in data
    assert "BUY" in data["active_signals_summary"]
    assert "paper_portfolio_snapshot" in data
    assert data["paper_portfolio_snapshot"]["total_value"] > 0


def test_stocks_screener(client):
    response = client.get("/api/v1/stocks?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10
    symbols = [item["symbol"] for item in data["items"]]
    assert any(s in ["RELIANCE", "TCS", "INFY", "HDFCBANK"] for s in symbols)


def test_stock_detail(client):
    response = client.get("/api/v1/stocks/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "TCS"
    assert data["exchange"] == "NSE"
    assert data["last_price"] > 0


def test_stock_candles(client):
    response = client.get("/api/v1/stocks/TCS/candles?interval=1d")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "TCS"
    assert len(data["candles"]) > 0
    first_candle = data["candles"][0]
    assert "open" in first_candle
    assert "close" in first_candle
    assert first_candle["high"] >= first_candle["low"]


def test_stock_prediction(client):
    response = client.get("/api/v1/stocks/TCS/prediction")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "TCS"
    assert data["signal"] in ["BUY", "HOLD", "SELL", "NO_TRADE"]
    assert 0.0 <= data["probability_up"] <= 1.0
    assert len(data["supporting_factors"]) > 0


def test_paper_portfolio_and_order(client):
    # Check initial portfolio
    port_resp = client.get("/api/v1/paper/portfolio")
    assert port_resp.status_code == 200
    port_data = port_resp.json()
    assert port_data["cash_balance"] > 0

    # Place an idempotent order
    order_payload = {
        "idempotency_key": "test-key-tcs-001",
        "symbol": "TCS",
        "side": "BUY",
        "quantity": 5,
        "order_type": "MARKET"
    }
    order_resp = client.post("/api/v1/paper/orders", json=order_payload)
    assert order_resp.status_code == 201
    order_data = order_resp.json()
    assert order_data["status"] == "FILLED"
    assert order_data["quantity"] == 5

    # Idempotent re-submission returns identical order without double billing
    repeat_resp = client.post("/api/v1/paper/orders", json=order_payload)
    assert repeat_resp.status_code == 201
    assert repeat_resp.json()["id"] == order_data["id"]
