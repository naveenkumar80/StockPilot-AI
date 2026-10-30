import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.paper_trading import PaperPortfolio, PaperPosition, PaperOrder


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_paper_portfolio_fetch_and_reset(client):
    # 1. Reset first to ensure clean state
    reset_resp = client.post("/api/v1/paper/reset")
    assert reset_resp.status_code == 200
    res_data = reset_resp.json()
    assert res_data["cash_balance"] == 1000000.0
    assert len(res_data["positions"]) == 0
    assert len(res_data["recent_orders"]) == 0

    # 2. Get portfolio
    get_resp = client.get("/api/v1/paper/portfolio")
    assert get_resp.status_code == 200
    p_data = get_resp.json()
    assert p_data["cash_balance"] == 1000000.0


def test_paper_buy_order_and_idempotency(client):
    idempotency_key = f"test-buy-{uuid.uuid4()}"
    payload = {
        "idempotency_key": idempotency_key,
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 10,
        "order_type": "MARKET",
    }

    # 1. First execution
    resp = client.post("/api/v1/paper/orders", json=payload)
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "FILLED"
    assert order["symbol"] == "RELIANCE"
    assert order["quantity"] == 10
    assert order["executed_price"] > 0
    assert order["transaction_fee"] > 0

    # 2. Duplicate submission returns exact same order without double deduction
    dup_resp = client.post("/api/v1/paper/orders", json=payload)
    assert dup_resp.status_code == 201
    dup_order = dup_resp.json()
    assert dup_order["id"] == order["id"]

    # 3. Check portfolio has RELIANCE position
    p_resp = client.get("/api/v1/paper/portfolio")
    p_data = p_resp.json()
    assert p_data["cash_balance"] < 1000000.0
    rel_pos = next((p for p in p_data["positions"] if p["symbol"] == "RELIANCE"), None)
    assert rel_pos is not None
    assert rel_pos["quantity"] == 10


def test_paper_sell_order_and_overdraft_checks(client):
    # 1. Partial Sell (5 out of 10 shares)
    sell_key = f"test-sell-{uuid.uuid4()}"
    sell_payload = {
        "idempotency_key": sell_key,
        "symbol": "RELIANCE",
        "side": "SELL",
        "quantity": 5,
        "order_type": "MARKET",
    }
    resp = client.post("/api/v1/paper/orders", json=sell_payload)
    assert resp.status_code == 201
    assert resp.json()["status"] == "FILLED"

    # Remaining quantity should be 5
    p_resp = client.get("/api/v1/paper/portfolio")
    rel_pos = next((p for p in p_resp.json()["positions"] if p["symbol"] == "RELIANCE"), None)
    assert rel_pos is not None
    assert rel_pos["quantity"] == 5

    # 2. Excessive Sell should fail with 400
    excess_key = f"test-excess-{uuid.uuid4()}"
    excess_payload = {
        "idempotency_key": excess_key,
        "symbol": "RELIANCE",
        "side": "SELL",
        "quantity": 100,
        "order_type": "MARKET",
    }
    excess_resp = client.post("/api/v1/paper/orders", json=excess_payload)
    assert excess_resp.status_code == 400
    assert "Cannot SELL" in excess_resp.json()["detail"]


def test_insufficient_cash_buy_fails(client):
    broke_key = f"test-broke-{uuid.uuid4()}"
    broke_payload = {
        "idempotency_key": broke_key,
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 500000,  # ₹1.4 billion order
        "order_type": "MARKET",
    }
    broke_resp = client.post("/api/v1/paper/orders", json=broke_payload)
    assert broke_resp.status_code == 400
    assert "Insufficient virtual cash" in broke_resp.json()["detail"]

