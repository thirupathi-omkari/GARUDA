import pandas as pd

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from strategy.ma_strategy import MovingAverageStrategy


def make_frame():
    closes = [
        100, 99, 98, 97, 96, 95, 94, 93, 92, 91,
        90, 91, 92, 93, 94, 95, 96, 97, 98, 99,
        100, 101, 102, 103, 104,
    ]
    dates = pd.date_range(
        "2026-07-01 09:15",
        periods=len(closes),
        freq="5min",
    )
    return pd.DataFrame({
        "datetime": dates,
        "open": closes,
        "high": [x + 0.5 for x in closes],
        "low": [x - 0.5 for x in closes],
        "close": closes,
        "volume": [1000] * len(closes),
    })


def test_ma_strategy_contract_and_diagnostics():
    strategy = MovingAverageStrategy(3, 5, "EMA")
    result = strategy.evaluate("INFY", make_frame())

    assert result.strategy_name == "MA"
    assert result.signal in {"BUY", "SELL", "NO_SIGNAL"}
    assert result.diagnostics["fast_period"] == 3
    assert result.diagnostics["slow_period"] == 5
