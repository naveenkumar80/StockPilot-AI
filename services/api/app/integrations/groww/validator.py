from datetime import datetime, timezone
from typing import List, Tuple, Any, Union
from app.integrations.groww.models import ValidatedCandle, ValidationReport
from app.core.logging import logger


class CandleValidator:
    """
    Enforces strict quantitative finance integrity rules on raw OHLCV market candles.
    """

    def __init__(self, max_allowed_jump_pct: float = 40.0):
        self.max_allowed_jump_pct = max_allowed_jump_pct

    def validate_candles(
        self,
        raw_candles: List[Union[List[Any], Tuple[Any, ...]]],
        symbol: str = "UNKNOWN"
    ) -> Tuple[List[ValidatedCandle], ValidationReport]:
        """
        Validates a list of raw candle tuples [timestamp, open, high, low, close, volume].
        
        Rules enforced:
        1. Non-negative volume (vol >= 0)
        2. Positive prices (open > 0, high > 0, low > 0, close > 0)
        3. High >= Low
        4. High >= max(Open, Close)
        5. Low <= min(Open, Close)
        6. Timestamp monotonicity & duplicate elimination
        7. Outlier jump warning
        """
        valid_candles: List[ValidatedCandle] = []
        violations: List[str] = []
        seen_timestamps = set()
        prev_close: Union[float, None] = None
        prev_ts: Union[datetime, None] = None

        total_received = len(raw_candles)

        for idx, row in enumerate(raw_candles):
            if not row or len(row) < 5:
                violations.append(f"Row {idx}: Invalid tuple length ({len(row) if row else 0})")
                continue

            try:
                raw_ts = row[0]
                # Parse timestamp: can be epoch int/float, ISO string, or datetime object
                if isinstance(raw_ts, (int, float)):
                    # Handle epoch in milliseconds vs seconds
                    if raw_ts > 1e11:  # Milliseconds
                        ts = datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc).replace(tzinfo=None)
                    else:
                        ts = datetime.fromtimestamp(raw_ts, tz=timezone.utc).replace(tzinfo=None)
                elif isinstance(raw_ts, str):
                    try:
                        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        ts = datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                elif isinstance(raw_ts, datetime):
                    ts = raw_ts.replace(tzinfo=None)
                else:
                    violations.append(f"Row {idx}: Unsupported timestamp type {type(raw_ts)}")
                    continue

                o = float(row[1])
                h = float(row[2])
                l = float(row[3])
                c = float(row[4])
                vol = int(row[5]) if len(row) > 5 and row[5] is not None else 0

                # 1. Check positive prices
                if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                    violations.append(f"Row {idx} ({ts}): Non-positive price detected (O={o}, H={h}, L={l}, C={c})")
                    continue

                # 2. Check non-negative volume
                if vol < 0:
                    violations.append(f"Row {idx} ({ts}): Negative volume ({vol})")
                    continue

                # 3. Check High >= Low
                if h < l:
                    violations.append(f"Row {idx} ({ts}): High ({h}) is less than Low ({l})")
                    continue

                # 4. Check High >= max(Open, Close)
                max_oc = max(o, c)
                if h < max_oc:
                    violations.append(
                        f"Row {idx} ({ts}): High ({h}) is less than max(Open, Close) ({max_oc})"
                    )
                    continue

                # 5. Check Low <= min(Open, Close)
                min_oc = min(o, c)
                if l > min_oc:
                    violations.append(
                        f"Row {idx} ({ts}): Low ({l}) is greater than min(Open, Close) ({min_oc})"
                    )
                    continue

                # 6. Deduplication by timestamp
                if ts in seen_timestamps:
                    violations.append(f"Row {idx} ({ts}): Duplicate timestamp dropped")
                    continue
                seen_timestamps.add(ts)

                # 7. Check monotonicity (should be sorted ascending)
                if prev_ts and ts < prev_ts:
                    violations.append(f"Row {idx} ({ts}): Out-of-order timestamp after {prev_ts}")
                    # Keep it but note warning, or skip if strict
                    continue

                # 8. Check abnormal single-candle jump
                if prev_close and prev_close > 0:
                    jump_pct = abs((c - prev_close) / prev_close) * 100.0
                    if jump_pct > self.max_allowed_jump_pct:
                        logger.warning(
                            f"Suspicious price jump of {jump_pct:.2f}% detected for {symbol} at {ts} "
                            f"(prev close: {prev_close}, current close: {c})"
                        )

                valid_candles.append(
                    ValidatedCandle(
                        timestamp=ts,
                        open=round(o, 4),
                        high=round(h, 4),
                        low=round(l, 4),
                        close=round(c, 4),
                        volume=vol,
                    )
                )
                prev_close = c
                prev_ts = ts

            except (ValueError, TypeError, IndexError) as err:
                violations.append(f"Row {idx}: Parse error: {str(err)}")
                continue

        # Sort valid candles chronologically ascending
        valid_candles.sort(key=lambda x: x.timestamp)

        report = ValidationReport(
            total_received=total_received,
            valid_count=len(valid_candles),
            dropped_count=total_received - len(valid_candles),
            violations=violations,
        )

        return valid_candles, report
