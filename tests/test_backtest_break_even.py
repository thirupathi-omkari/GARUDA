import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit


def create_trade(
    direction="BUY",
):
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
        initial_stop_loss=(
            95.00
            if direction == "BUY"
            else 105.00
        ),
        current_stop_loss=(
            95.00
            if direction == "BUY"
            else 105.00
        ),
        target_price=120.00,
        initial_risk=5.00,
        quantity=1,
    )


def create_candles(rows):
    return pd.DataFrame(rows)


def test_buy_break_even_moves_stop_to_entry():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 104.00,
                "high": 106.00,
                "low": 103.50,
                "close": 105.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 105.00,
                "high": 106.00,
                "low": 104.50,
                "close": 105.50,
            },
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    assert result.current_stop_loss == pytest.approx(
        100.00
    )

    assert result.exit_reason == "END_OF_DAY"


def test_buy_below_one_r_stop_remains_unchanged():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 103.00,
                "high": 104.50,
                "low": 102.50,
                "close": 104.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 104.00,
                "high": 104.50,
                "low": 101.00,
                "close": 103.00,
            },
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    assert result.current_stop_loss == pytest.approx(
        95.00
    )

    assert result.exit_reason == "END_OF_DAY"


def test_sell_break_even_moves_stop_to_entry():
    trade = create_trade("SELL")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 96.00,
                "high": 96.50,
                "low": 94.00,
                "close": 95.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 95.00,
                "high": 95.50,
                "low": 94.00,
                "close": 94.50,
            },
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=105.00,
        target=80.00,
    )

    assert result is not None

    assert result.current_stop_loss == pytest.approx(
        100.00
    )

    assert result.exit_reason == "END_OF_DAY"


def test_sell_below_one_r_stop_remains_unchanged():
    trade = create_trade("SELL")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 97.00,
                "high": 97.50,
                "low": 96.00,
                "close": 96.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 96.00,
                "high": 99.00,
                "low": 95.00,
                "close": 98.00,
            },
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=105.00,
        target=80.00,
    )

    assert result is not None

    assert result.current_stop_loss == pytest.approx(
        105.00
    )

    assert result.exit_reason == "END_OF_DAY"


def test_buy_break_even_applies_from_next_candle():
    trade = create_trade("BUY")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 104.00,
                "high": 106.00,
                "low": 99.00,
                "close": 105.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 105.00,
                "high": 106.00,
                "low": 99.50,
                "close": 100.00,
            },
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=120.00,
    )

    assert result is not None

    # The first candle reached 1R but its low
    # must be evaluated against the original
    # stop of 95, not the newly-created BE stop.

    assert result.exit_time == pd.Timestamp(
        "2026-07-01 09:50:00"
    )

    assert result.exit_price == pytest.approx(
        100.00
    )

    # The current stop was moved to entry
    # after the first candle.

    assert result.current_stop_loss == pytest.approx(
        100.00
    )

    # The existing lifecycle uses STOP_LOSS
    # for a stop hit, including a break-even stop.

    assert result.exit_reason == "STOP_LOSS"


def test_sell_break_even_applies_from_next_candle():
    trade = create_trade("SELL")

    candles = create_candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 96.00,
                "high": 101.00,
                "low": 94.00,
                "close": 95.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 95.00,
                "high": 100.50,
                "low": 94.00,
                "close": 100.00,
            },
        ]
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=105.00,
        target=80.00,
    )

    assert result is not None

    # The first candle reached 1R but its high
    # must be evaluated against the original
    # stop of 105, not the newly-created BE stop.

    assert result.exit_time == pd.Timestamp(
        "2026-07-01 09:50:00"
    )

    assert result.exit_price == pytest.approx(
        100.00
    )

    assert result.current_stop_loss == pytest.approx(
        100.00
    )

    assert result.exit_reason == "STOP_LOSS"