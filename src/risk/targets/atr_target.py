import pandas as pd

from risk.stop_losses.atr import (
    calculate_atr,
)

from risk.risk_config import (
    RiskConfig,
)

risk_config = RiskConfig()


def calculate_atr_target(
    signal: str,
    entry_price: float,
    candles: pd.DataFrame,
    atr_period: int = 14,
    atr_multiplier: float | None = None,
):
    """
    Calculate ATR-based target.
    """

    if atr_multiplier is None:

        atr_multiplier = (
            risk_config.atr_target_multiplier
        )

    atr = calculate_atr(
        candles=candles,
        period=atr_period,
    )

    signal = signal.upper()

    if signal == "BUY":

        return (
            entry_price
            + (atr * atr_multiplier)
        )

    if signal == "SELL":

        return (
            entry_price
            - (atr * atr_multiplier)
        )

    raise ValueError(
        "Signal must be BUY or SELL."
    )