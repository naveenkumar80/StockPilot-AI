from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.paper_trading import PaperPortfolio, PaperPosition, PaperOrder
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.schemas.paper import (
    PaperPortfolioResponse,
    PaperPositionResponse,
    PaperOrderCreate,
    PaperOrderResponse,
)

router = APIRouter()


@router.get("/portfolio", response_model=PaperPortfolioResponse)
def get_paper_portfolio(db: Session = Depends(get_db)):
    portfolio = db.query(PaperPortfolio).first()
    if not portfolio:
        portfolio = PaperPortfolio(
            name="StockPilot Sandbox Virtual Fund",
            initial_capital=1000000.00,
            cash_balance=1000000.00,
            total_equity=1000000.00,
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

    positions_db = db.query(PaperPosition).filter(PaperPosition.portfolio_id == portfolio.id).all()
    position_items: List[PaperPositionResponse] = []
    total_pos_value = 0.0

    for pos in positions_db:
        inst = db.query(Instrument).filter(Instrument.id == pos.instrument_id).first()
        latest_candle = (
            db.query(MarketCandle)
            .filter(MarketCandle.instrument_id == pos.instrument_id)
            .order_by(MarketCandle.timestamp.desc())
            .first()
        )
        curr_price = float(latest_candle.close) if latest_candle else float(pos.current_price)
        pos_qty = float(pos.quantity)
        avg_price = float(pos.average_buy_price)

        market_val = pos_qty * curr_price
        total_pos_value += market_val
        unreal_pnl = market_val - (pos_qty * avg_price)
        unreal_pct = (unreal_pnl / (pos_qty * avg_price) * 100) if avg_price > 0 else 0.0

        position_items.append(
            PaperPositionResponse(
                symbol=inst.symbol if inst else "UNKNOWN",
                company_name=inst.company_name if inst else "Unknown Company",
                quantity=pos_qty,
                average_buy_price=round(avg_price, 2),
                current_price=round(curr_price, 2),
                unrealized_pnl=round(unreal_pnl, 2),
                unrealized_pnl_pct=round(unreal_pct, 2),
                market_value=round(market_val, 2),
            )
        )

    # Recalculate portfolio equity
    total_eq = float(portfolio.cash_balance) + total_pos_value
    portfolio.total_equity = total_eq
    db.commit()

    orders_db = (
        db.query(PaperOrder)
        .filter(PaperOrder.portfolio_id == portfolio.id)
        .order_by(PaperOrder.created_at.desc())
        .limit(10)
        .all()
    )

    recent_orders = [
        PaperOrderResponse(
            id=ord.id,
            portfolio_id=ord.portfolio_id,
            idempotency_key=ord.idempotency_key,
            symbol=db.query(Instrument.symbol).filter(Instrument.id == ord.instrument_id).scalar() or "UNKNOWN",
            side=ord.side,
            quantity=float(ord.quantity),
            order_type=ord.order_type,
            status=ord.status,
            executed_price=float(ord.executed_price) if ord.executed_price else None,
            transaction_fee=float(ord.transaction_fee),
            created_at=ord.created_at,
            executed_at=ord.executed_at,
        )
        for ord in orders_db
    ]

    initial_cap = float(portfolio.initial_capital)
    unreal_pnl = total_eq - initial_cap
    unreal_pnl_pct = (unreal_pnl / initial_cap * 100) if initial_cap > 0 else 0.0

    return PaperPortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        initial_capital=initial_cap,
        cash_balance=float(portfolio.cash_balance),
        total_equity=round(total_eq, 2),
        unrealized_pnl=round(unreal_pnl, 2),
        unrealized_pnl_pct=round(unreal_pnl_pct, 2),
        positions=position_items,
        recent_orders=recent_orders,
        updated_at=portfolio.updated_at,
    )


@router.post("/orders", response_model=PaperOrderResponse, status_code=201)
def place_paper_order(payload: PaperOrderCreate, db: Session = Depends(get_db)):
    portfolio = db.query(PaperPortfolio).first()
    if not portfolio:
        portfolio = PaperPortfolio(
            name="StockPilot Sandbox Virtual Fund",
            initial_capital=1000000.00,
            cash_balance=1000000.00,
            total_equity=1000000.00,
        )
        db.add(portfolio)
        db.flush()

    # 1. Idempotency Check
    existing_order = db.query(PaperOrder).filter(PaperOrder.idempotency_key == payload.idempotency_key).first()
    if existing_order:
        sym = db.query(Instrument.symbol).filter(Instrument.id == existing_order.instrument_id).scalar() or payload.symbol
        return PaperOrderResponse(
            id=existing_order.id,
            portfolio_id=existing_order.portfolio_id,
            idempotency_key=existing_order.idempotency_key,
            symbol=sym,
            side=existing_order.side,
            quantity=float(existing_order.quantity),
            order_type=existing_order.order_type,
            status=existing_order.status,
            executed_price=float(existing_order.executed_price) if existing_order.executed_price else None,
            transaction_fee=float(existing_order.transaction_fee),
            created_at=existing_order.created_at,
            executed_at=existing_order.executed_at,
        )

    # 2. Instrument resolution
    inst = db.query(Instrument).filter(Instrument.symbol == payload.symbol.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{payload.symbol}' not found.")

    latest_candle = (
        db.query(MarketCandle)
        .filter(MarketCandle.instrument_id == inst.id)
        .order_by(MarketCandle.timestamp.desc())
        .first()
    )
    if not latest_candle:
        raise HTTPException(status_code=400, detail=f"No market price available for {payload.symbol}")

    price = float(latest_candle.close)
    slippage_bps = 0.0005  # 5 bps
    fee_rate = 0.0003      # 0.03% estimated brokerage + taxes

    pos = (
        db.query(PaperPosition)
        .filter(PaperPosition.portfolio_id == portfolio.id, PaperPosition.instrument_id == inst.id)
        .first()
    )

    if payload.side == "BUY":
        exec_price = round(price * (1.0 + slippage_bps), 2)
        total_cost = (exec_price * payload.quantity) * (1.0 + fee_rate)
        fee = round((exec_price * payload.quantity) * fee_rate, 2)

        if float(portfolio.cash_balance) < total_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient virtual cash balance. Required: ₹{total_cost:,.2f}, Available: ₹{float(portfolio.cash_balance):,.2f}"
            )

        # Deduct cash
        portfolio.cash_balance = float(portfolio.cash_balance) - total_cost

        # Update position
        if pos:
            old_qty = float(pos.quantity)
            old_avg = float(pos.average_buy_price)
            new_qty = old_qty + payload.quantity
            new_avg = ((old_qty * old_avg) + (payload.quantity * exec_price)) / new_qty
            pos.quantity = new_qty
            pos.average_buy_price = round(new_avg, 2)
            pos.current_price = exec_price
        else:
            pos = PaperPosition(
                portfolio_id=portfolio.id,
                instrument_id=inst.id,
                quantity=payload.quantity,
                average_buy_price=exec_price,
                current_price=exec_price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
            )
            db.add(pos)

    elif payload.side == "SELL":
        if not pos or float(pos.quantity) < payload.quantity:
            avail = float(pos.quantity) if pos else 0.0
            raise HTTPException(
                status_code=400,
                detail=f"Cannot SELL {payload.quantity} shares of {payload.symbol}. Current position holding: {avail}"
            )

        exec_price = round(price * (1.0 - slippage_bps), 2)
        proceeds = (exec_price * payload.quantity) * (1.0 - fee_rate)
        fee = round((exec_price * payload.quantity) * fee_rate, 2)

        portfolio.cash_balance = float(portfolio.cash_balance) + proceeds
        pos.quantity = float(pos.quantity) - payload.quantity
        if pos.quantity <= 0.0001:
            db.delete(pos)

    order = PaperOrder(
        portfolio_id=portfolio.id,
        instrument_id=inst.id,
        idempotency_key=payload.idempotency_key,
        side=payload.side,
        quantity=payload.quantity,
        order_type=payload.order_type,
        status="FILLED",
        executed_price=exec_price,
        transaction_fee=fee,
        executed_at=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return PaperOrderResponse(
        id=order.id,
        portfolio_id=order.portfolio_id,
        idempotency_key=order.idempotency_key,
        symbol=payload.symbol.upper(),
        side=order.side,
        quantity=float(order.quantity),
        order_type=order.order_type,
        status=order.status,
        executed_price=float(order.executed_price),
        transaction_fee=float(order.transaction_fee),
        created_at=order.created_at,
        executed_at=order.executed_at,
    )


@router.post("/reset", response_model=PaperPortfolioResponse)
def reset_paper_portfolio(db: Session = Depends(get_db)):
    """
    Resets the virtual sandbox fund to initial ₹1,000,000 cash balance
    and wipes all open positions and order history.
    """
    portfolio = db.query(PaperPortfolio).first()
    if not portfolio:
        portfolio = PaperPortfolio(
            name="StockPilot Sandbox Virtual Fund",
            initial_capital=1000000.00,
            cash_balance=1000000.00,
            total_equity=1000000.00,
        )
        db.add(portfolio)
    else:
        portfolio.cash_balance = 1000000.00
        portfolio.total_equity = 1000000.00
        db.query(PaperPosition).filter(PaperPosition.portfolio_id == portfolio.id).delete()
        db.query(PaperOrder).filter(PaperOrder.portfolio_id == portfolio.id).delete()

    db.commit()
    db.refresh(portfolio)

    return PaperPortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        initial_capital=float(portfolio.initial_capital),
        cash_balance=float(portfolio.cash_balance),
        total_equity=float(portfolio.total_equity),
        unrealized_pnl=0.0,
        unrealized_pnl_pct=0.0,
        positions=[],
        recent_orders=[],
        updated_at=portfolio.updated_at,
    )

