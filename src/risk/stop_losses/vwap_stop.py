import pandas as pd

from risk.stop_losses.atr import (
    calculate_atr,
)

from risk.risk_config import (
    RiskConfig,
)

risk_config = RiskConfig()

def calculate_vwap_stop_loss(
    signal: str,
    vwap: float,
    candles: pd.DataFrame,
    atr_period: int | None = None,
    atr_multiplier: float | None = None,
):
    """
    Calculate VWAP stop loss with ATR buffer.
    """

    if atr_multiplier is None:


        atr_multiplier = (
            risk_config.vwap_atr_multiplier
        )

    if atr_period is None:

        atr_period = (
            risk_config.atr_period
        )

    atr = calculate_atr(
        candles=candles,
        period=atr_period,
    )

    signal = signal.upper()

    if signal == "BUY":

        return (
            vwap
            - (atr * atr_multiplier)
        )

    if signal == "SELL":

        return (
            vwap
            + (atr * atr_multiplier)
        )

    raise ValueError(
        "Signal must be BUY or SELL."
    )