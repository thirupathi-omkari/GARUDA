import sys
from pathlib import Path
from datetime import date, datetime

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade

from backtesting.exit_simulator import (
    simulate_trade_exit,
)


def test_target_simulation():

    trade = BacktestTrade(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 1),
        direction="BUY",
        entry_time=datetime(
            2026,
            7,
            1,
            9,
            40,
        ),
        entry_price=100.00,
        quantity=1,
    )

    future_candles = pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-07-01 09:40:00"
                ),
                pd.Timestamp(
                    "2026-07-01 09:45:00"
                ),
                pd.Timestamp(
                    "2026-07-01 09:50:00"
                ),
                pd.Timestamp(
                    "2026-07-01 09:55:00"
                ),
            ],

            "open": [
                100.00,
                100.50,
                101.20,
                102.50,
            ],

            "high": [
                100.50,
                101.20,
                102.30,
                103.00,
            ],

            "low": [
                99.50,
                100.00,
                100.80,
                102.00,
            ],

            "close": [
                100.40,
                101.00,
                102.10,
                102.80,
            ],
        }
    )

    completed_trade = simulate_trade_exit(
        trade=trade,
        future_candles=future_candles,
        stop_loss=99.00,
        target=102.00,
    )

    assert completed_trade is not None

    assert completed_trade.symbol == "INFY"
    assert completed_trade.direction == "BUY"

    assert completed_trade.entry_time == datetime(
        2026,
        7,
        1,
        9,
        40,
    )

    assert completed_trade.entry_price == 100.00

    assert completed_trade.exit_time == pd.Timestamp(
        "2026-07-01 09:50:00"
    )

    assert completed_trade.exit_price == 102.00

    assert completed_trade.exit_reason == "TARGET"