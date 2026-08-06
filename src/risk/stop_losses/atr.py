import numpy as np
import pandas as pd

from risk.risk_config import RiskConfig

risk_config = RiskConfig()


def calculate_atr(
    candles: pd.DataFrame,
    period: int = 14,
):
    """
    Calculate Average True Range.
    """

    high = candles["high"]

    low = candles["low"]

    close = candles["close"]

    previous_close = close.shift(1)

    true_range = np.maximum(
        high - low,
        np.maximum(
            abs(high - previous_close),
            abs(low - previous_close),
        ),
    )

    atr = (
        pd.Series(true_range)
        .rolling(period)
        .mean()
        .iloc[-1]
    )

    return atr

def calculate_atr_stop_loss(
    signal: str,
    entry_price: float,
    candles: pd.DataFrame,
    atr_period: int | None = None,
    atr_multiplier: float | None = None,
):
    """
    Calculate ATR-based stop loss.
    """

    if atr_period is None:
        atr_period = risk_config.atr_period

    if atr_multiplier is None:
        atr_multiplier = risk_config.atr_multiplier

    atr = calculate_atr(
        candles=candles,
        period=atr_period,
    )

    signal = signal.upper()

    if signal == "BUY":

        return (
            entry_price
            - (atr * atr_multiplier)
        )

    if signal == "SELL":

        return (
            entry_price
            + (atr * atr_multiplier)
        )

    raise ValueError(
        "Signal must be BUY or SELL."
    )