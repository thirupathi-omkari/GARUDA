import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit
from backtesting.pnl_calculator import calculate_trade_pnl


def create_trade(
    direction="BUY",
    entry_price=100.00,
    stop_loss=95.00,
    target=120.00,
    quantity=1,
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
        entry_price=entry_price,
        initial_stop_loss=stop_loss,
        current_stop_loss=stop_loss,
        target_price=target,
        initial_risk=abs(
            entry_price - stop_loss
        ),
        quantity=quantity,
    )


def candles(rows):
    return pd.DataFrame(rows)


def test_dynamic_target_exit_and_pnl():
    trade = create_trade(
        direction="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        target=110.00,
    )

    future = candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 104.00,
                "high": 105.00,
                "low": 103.00,
                "close": 104.50,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 104.50,
                "high": 111.00,
                "low": 104.00,
                "close": 110.00,
            },
        ]
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=95.00,
        target=110.00,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert trade.exit_reason == "TARGET"

    assert trade.exit_time == pd.Timestamp(
        "2026-07-01 09:50:00"
    )

    assert trade.exit_price == pytest.approx(
        110.00
    )

    assert trade.gross_pnl == pytest.approx(
        10.00
    )

    assert trade.costs == pytest.approx(
        0.21
    )

    assert trade.net_pnl == pytest.approx(
        9.79
    )


def test_dynamic_stop_loss_exit_and_pnl():
    trade = create_trade(
        direction="BUY",
        entry_price=100.00,
        stop_loss=97.00,
        target=120.00,
    )

    future = candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 99.00,
                "high": 100.00,
                "low": 96.00,
                "close": 97.00,
            },
        ]
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=97.00,
        target=120.00,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert trade.exit_reason == "STOP_LOSS"

    assert trade.exit_time == pd.Timestamp(
        "2026-07-01 09:45:00"
    )

    assert trade.exit_price == pytest.approx(
        97.00
    )

    assert trade.gross_pnl == pytest.approx(
        -3.00
    )

    assert trade.net_pnl < -3.00


def test_buy_break_even_then_stop_exit():
    trade = create_trade(
        direction="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        target=120.00,
    )

    future = candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 104.00,
                "high": 106.00,
                "low": 103.00,
                "close": 105.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 105.00,
                "high": 106.00,
                "low": 99.00,
                "close": 100.00,
            },
        ]
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=95.00,
        target=120.00,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert trade.current_stop_loss == pytest.approx(
        100.00
    )

    assert trade.exit_reason == "STOP_LOSS"

    assert trade.exit_price == pytest.approx(
        100.00
    )

    assert trade.gross_pnl == pytest.approx(
        0.00
    )

    assert trade.net_pnl < 0


def test_sell_break_even_then_stop_exit():
    trade = create_trade(
        direction="SELL",
        entry_price=100.00,
        stop_loss=105.00,
        target=80.00,
    )

    future = candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 96.00,
                "high": 97.00,
                "low": 94.00,
                "close": 95.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 95.00,
                "high": 101.00,
                "low": 94.00,
                "close": 100.00,
            },
        ]
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=105.00,
        target=80.00,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert trade.current_stop_loss == pytest.approx(
        100.00
    )

    assert trade.exit_reason == "STOP_LOSS"

    assert trade.exit_price == pytest.approx(
        100.00
    )

    assert trade.gross_pnl == pytest.approx(
        0.00
    )


def test_trailing_stop_then_exit():
    trade = create_trade(
        direction="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        target=120.00,
    )

    rows = []

    for index in range(14):
        rows.append(
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                )
                + pd.Timedelta(
                    minutes=5 * index
                ),
                "open": 100.00,
                "high": 101.00,
                "low": 99.00,
                "close": 100.00,
            }
        )

    rows[13] = {
        "datetime": pd.Timestamp(
            "2026-07-01 10:50:00"
        ),
        "open": 110.00,
        "high": 112.00,
        "low": 109.00,
        "close": 110.00,
    }

    rows.append(
        {
            "datetime": pd.Timestamp(
                "2026-07-01 10:55:00"
            ),
            "open": 110.00,
            "high": 110.50,
            "low": 100.00,
            "close": 101.00,
        }
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=candles(rows),
        stop_loss=95.00,
        target=120.00,
    )

    assert trade.exit_reason == "STOP_LOSS"

    assert trade.exit_time == pd.Timestamp(
        "2026-07-01 10:55:00"
    )

    assert trade.current_stop_loss > 95.00


def test_end_of_day_when_no_dynamic_exit_is_hit():
    trade = create_trade(
        direction="BUY",
        entry_price=100.00,
        stop_loss=90.00,
        target=120.00,
    )

    future = candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 101.00,
                "high": 103.00,
                "low": 100.00,
                "close": 102.00,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                "open": 102.00,
                "high": 104.00,
                "low": 101.00,
                "close": 103.00,
            },
        ]
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=90.00,
        target=120.00,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert trade.exit_reason == "END_OF_DAY"

    assert trade.exit_time == pd.Timestamp(
        "2026-07-01 09:50:00"
    )

    assert trade.exit_price == pytest.approx(
        103.00
    )

    assert trade.gross_pnl == pytest.approx(
        3.00
    )

    assert trade.net_pnl < 3.00


def test_stop_loss_has_priority_when_same_candle_hits_both():
    trade = create_trade(
        direction="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        target=105.00,
    )

    future = candles(
        [
            {
                "datetime": pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                "open": 100.00,
                "high": 106.00,
                "low": 94.00,
                "close": 100.00,
            },
        ]
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=95.00,
        target=105.00,
    )

    assert trade.exit_reason == "STOP_LOSS"

    assert trade.exit_price == pytest.approx(
        95.00
    )