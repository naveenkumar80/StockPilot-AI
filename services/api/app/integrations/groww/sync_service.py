import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.integrations.groww.client import GrowwClient
from app.integrations.groww.models import SyncResult, ValidatedCandle


class CandleSyncService:
    """
    Orchestrates historical and incremental market candle ingestion from Groww Trade API,
    validates data integrity, and updates the local database idempotently.
    """

    def __init__(self, client: Optional[GrowwClient] = None):
        self.client = client or GrowwClient()

    async def sync_instrument_candles(
        self,
        db: Session,
        symbol: str,
        interval: str = "1d",
        lookback_days: int = 90,
        force_full_backfill: bool = False,
    ) -> SyncResult:
        """
        Performs an incremental or full backfill sync for a given stock symbol and interval.
        """
        start_time_bench = time.perf_counter()
        symbol_upper = symbol.upper()

        inst = db.query(Instrument).filter(Instrument.symbol == symbol_upper).first()
        if not inst:
            raise ValueError(f"Instrument '{symbol_upper}' not found in database")

        now_utc = datetime.utcnow()

        # Determine start_time
        if not force_full_backfill:
            latest_candle = (
                db.query(MarketCandle)
                .filter(MarketCandle.instrument_id == inst.id, MarketCandle.interval == interval)
                .order_by(MarketCandle.timestamp.desc())
                .first()
            )
            if latest_candle:
                # Incremental sync: start from 2 days prior to ensure current active bar is refreshed
                start_dt = latest_candle.timestamp - timedelta(days=2)
            else:
                start_dt = now_utc - timedelta(days=lookback_days)
        else:
            start_dt = now_utc - timedelta(days=lookback_days)

        # Call Groww Client
        valid_candles, report, is_demo = await self.client.get_historical_candles(
            symbol=inst.symbol,
            start_time=start_dt,
            end_time=now_utc,
            interval=interval,
            exchange=inst.exchange,
        )

        candles_ingested = 0
        candles_updated = 0

        # Idempotent database upsert
        for candle in valid_candles:
            existing = (
                db.query(MarketCandle)
                .filter(
                    MarketCandle.instrument_id == inst.id,
                    MarketCandle.timestamp == candle.timestamp,
                    MarketCandle.interval == interval,
                )
                .first()
            )

            if existing:
                # Update existing candle
                existing.open = candle.open
                existing.high = candle.high
                existing.low = candle.low
                existing.close = candle.close
                existing.volume = candle.volume
                existing.source = "demo_groww_mock" if is_demo else "groww_api"
                existing.ingested_at = now_utc
                candles_updated += 1
            else:
                new_candle = MarketCandle(
                    instrument_id=inst.id,
                    timestamp=candle.timestamp,
                    interval=interval,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                    source="demo_groww_mock" if is_demo else "groww_api",
                    ingested_at=now_utc,
                )
                db.add(new_candle)
                candles_ingested += 1

        inst.updated_at = now_utc
        db.commit()

        duration_ms = round((time.perf_counter() - start_time_bench) * 1000, 2)

        logger.info(
            f"[CandleSyncService] {symbol_upper} ({interval}) sync complete: "
            f"+{candles_ingested} inserted, {candles_updated} updated, "
            f"{report.dropped_count} dropped in {duration_ms}ms (Demo={is_demo})"
        )

        return SyncResult(
            symbol=symbol_upper,
            interval=interval,
            candles_fetched=report.total_received,
            candles_ingested=candles_ingested,
            candles_updated=candles_updated,
            candles_dropped=report.dropped_count,
            is_demo=is_demo,
            source="demo_groww_mock" if is_demo else "groww_api",
            sync_duration_ms=duration_ms,
            start_time=start_dt,
            end_time=now_utc,
            warnings=report.violations[:10],
        )

    async def sync_all_active_instruments(
        self,
        db: Session,
        interval: str = "1d",
        lookback_days: int = 90,
    ) -> List[SyncResult]:
        """
        Syncs market candles for all active instruments in the database.
        """
        instruments = db.query(Instrument).filter(Instrument.is_active == True).all()
        results: List[SyncResult] = []

        for inst in instruments:
            try:
                res = await self.sync_instrument_candles(
                    db=db,
                    symbol=inst.symbol,
                    interval=interval,
                    lookback_days=lookback_days,
                )
                results.append(res)
            except Exception as e:
                logger.error(f"[CandleSyncService] Error syncing {inst.symbol}: {e}")
                results.append(
                    SyncResult(
                        symbol=inst.symbol,
                        interval=interval,
                        candles_fetched=0,
                        candles_ingested=0,
                        candles_updated=0,
                        candles_dropped=0,
                        is_demo=True,
                        source="error",
                        sync_duration_ms=0,
                        warnings=[str(e)],
                    )
                )

        return results
