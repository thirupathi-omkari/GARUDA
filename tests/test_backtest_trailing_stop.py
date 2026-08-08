import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit


def create_trade(direction="BUY"):
    if direction == "BUY":
        stop_loss = 95.00
    else:
        stop_loss = 105.00

    return BacktestTrade(
        symbol="INFY",
        strategy_name="TEST",
        trade_date=pd.Timestamp(
            "2026-07-01"
        ).date(),
        direction=direction,
        entry_time=pd.Timestamp(
            "2026-07-01 09:40:00"
        ),
        entry_price=100.00,
        initial_stop_loss=stop_loss,
        current_stop_loss=stop_loss,
        target_price=120.00,
        initial_risk=5.00,
        quantity=1,
    )


def create_candles(rows):
    return pd.DataFrame(rows)


def test_buy_trailing_stop_moves_upward():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 101.00,
                "low": 99.50,
                "close": 100.50,
            }
            for _ in range(14)
        ]
    )

    # Force a clear upward market move.
    candles.loc[13, "open"] = 110.00
    candles.loc[13, "high"] = 112.00
    candles.loc[13, "low"] = 109.00
    candles.loc[13, "close"] = 110.00

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    assert result.current_stop_loss > 95.00

    assert result.exit_reason == "END_OF_DAY"


def test_sell_trailing_stop_moves_downward():
    trade = create_trade("SELL")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 100.50,
                "low": 99.50,
                "close": 100.00,
            }
            for _ in range(14)
        ]
    )

    # Force a clear downward market move.
    candles.loc[13, "open"] = 90.00
    candles.loc[13, "high"] = 91.00
    candles.loc[13, "low"] = 88.00
    candles.loc[13, "close"] = 90.00

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=105.00,
        target=80.00,
    )

    assert result is not None

    assert result.current_stop_loss < 105.00

    assert result.exit_reason == "END_OF_DAY"


def test_buy_trailing_stop_never_moves_backward():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 101.00,
                "low": 99.50,
                "close": 100.00,
            }
            for _ in range(14)
        ]
    )

    candles.loc[13, "open"] = 110.00
    candles.loc[13, "high"] = 112.00
    candles.loc[13, "low"] = 109.00
    candles.loc[13, "close"] = 110.00

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    first_stop = result.current_stop_loss

    assert first_stop >= 95.00

    # A BUY trailing stop must never move below
    # its previous value.
    assert first_stop >= (
        trade.initial_stop_loss
    )


def test_insufficient_atr_history_does_not_create_nan_stop():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 101.00,
                "low": 99.00,
                "close": 100.00,
            }
            for _ in range(5)
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    assert pd.notna(
        result.current_stop_loss
    )

    assert result.current_stop_loss == pytest.approx(
        95.00
    )

    assert result.exit_reason == "END_OF_DAY"


def test_buy_trailing_stop_applies_from_next_candle():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 101.00,
                "low": 99.00,
                "close": 100.00,
            }
            for _ in range(14)
        ]
    )

    # Establish ATR history.
    candles.loc[13, "open"] = 110.00
    candles.loc[13, "high"] = 112.00
    candles.loc[13, "low"] = 109.00
    candles.loc[13, "close"] = 110.00

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    assert result.current_stop_loss > 95.00


def test_trailing_stop_can_close_trade():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 101.00,
                "low": 99.00,
                "close": 100.00,
            }
            for _ in range(14)
        ]
    )

    # Create a strong upward move to establish
    # a higher trailing stop.
    candles.loc[13, "open"] = 110.00
    candles.loc[13, "high"] = 112.00
    candles.loc[13, "low"] = 109.00
    candles.loc[13, "close"] = 110.00

    # Next candle falls through the newly
    # established trailing stop.
    candles.loc[14] = {
        "datetime": pd.Timestamp(
            "2026-07-01 10:00:00"
        ),
        "open": 110.00,
        "high": 110.50,
        "low": 100.00,
        "close": 101.00,
    }

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    assert result.exit_reason == "STOP_LOSS"

    assert result.exit_time == pd.Timestamp(
        "2026-07-01 10:00:00"
    )