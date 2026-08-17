import pandas as pd
import pytest

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from indicators.moving_average import (
    calculate_moving_average,
    add_moving_averages,
)


def test_sma():
    df = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
    result = calculate_moving_average(df, 3, "SMA")
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_ema():
    df = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
    result = calculate_moving_average(df, 3, "EMA")
    assert result.iloc[2] == pytest.approx(2.25)
    assert result.iloc[4] == pytest.approx(4.0625)


def test_invalid_periods():
    df = pd.DataFrame({"close": [1, 2, 3]})
    with pytest.raises(ValueError):
        calculate_moving_average(df, 0)
    with pytest.raises(ValueError):
        add_moving_averages(df, 21, 9)
