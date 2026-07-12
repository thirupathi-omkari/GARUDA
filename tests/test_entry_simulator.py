import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.entry_simulator import simulate_entry
from strategy.strategy_result import StrategyResult


def test_entry_simulator():

    signal_result = StrategyResult(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        signal="BUY",
        entry_price=106.00,
        reason="Test BUY signal",
    )

    signal_record = {
        "evaluation_time": pd.Timestamp(
            "2026-07-01 09:35:00"
        ),
        "visible_candles": 5,
        "result": signal_result,
    }

    next_candle = pd.Series(
        {
            "datetime": pd.Timestamp(
                "2026-07-01 09:40:00"
            ),
            "open": 107.00,
            "high": 110.00,
            "low": 106.00,
            "close": 109.00,
            "volume": 3500,
        }
    )

    trade = simulate_entry(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        signal_record=signal_record,
        next_candle=next_candle,
    )

    assert trade is not None
    assert trade.symbol == "INFY"
    assert trade.strategy_name == "ORB_VWAP"
    assert trade.direction == "BUY"

    assert trade.entry_time == pd.Timestamp(
        "2026-07-01 09:40:00"
    )

    assert trade.entry_price == 107.00
    assert trade.quantity == 1

    assert trade.exit_time is None
    assert trade.exit_price is None