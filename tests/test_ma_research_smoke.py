import pandas as pd

from indicators.moving_average import add_moving_averages


def test_ema_columns_are_present():
    df = pd.DataFrame({"close": range(1, 30)})
    result = add_moving_averages(df, 9, 21, "EMA")
    assert "fast_ma" in result.columns
    assert "slow_ma" in result.columns
    assert result["fast_ma"].notna().sum() > 0
    assert result["slow_ma"].notna().sum() > 0
