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


def test_end_of_day_exit():

    trade = BacktestTrade(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 1),
        direction="BUY",
        entry_time=datetime(
            2026,
            7,
            1,
            15,
            15,
        ),
        entry_price=100.00,
        quantity=1,
    )

    future_candles = pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-07-01 15:15:00"
                ),
                pd.Timestamp(
                    "2026-07-01 15:20:00"
                ),
                pd.Timestamp(
                    "2026-07-01 15:25:00"
                ),
                pd.Timestamp(
                    "2026-07-01 15:30:00"
                ),
            ],

            "open": [
                100.00,
                100.20,
                100.50,
                100.70,
            ],

            "high": [
                100.50,
                100.80,
                101.00,
                101.20,
            ],

            "low": [
                99.50,
                99.80,
                100.00,
                100.20,
            ],

            "close": [
                100.20,
                100.50,
                100.70,
                101.00,
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
        15,
        15,
    )

    assert completed_trade.entry_price == 100.00

    assert completed_trade.exit_time == pd.Timestamp(
        "2026-07-01 15:30:00"
    )

    assert completed_trade.exit_price == 101.00

    assert completed_trade.exit_reason == "END_OF_DAY"