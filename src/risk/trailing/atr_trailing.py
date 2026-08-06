import pandas as pd

from risk.risk_config import (
    RiskConfig,
)

from risk.stop_losses.atr import (
    calculate_atr,
)

risk_config = RiskConfig()


def calculate_atr_trailing_stop(
    signal: str,
    current_stop: float,
    candles: pd.DataFrame,
    atr_period: int | None = None,
    atr_multiplier: float | None = None,
):
    """
    Calculate ATR-based trailing stop.

    BUY:
        Trail upward only.

    SELL:
        Trail downward only.
    """

    # --------------------------------------------------
    # LOAD DEFAULT CONFIGURATION
    # --------------------------------------------------

    if atr_period is None:

        atr_period = (
            risk_config.atr_period
        )

    if atr_multiplier is None:

        atr_multiplier = (
            risk_config.atr_trailing_multiplier
        )

    # --------------------------------------------------
    # CALCULATE ATR
    # --------------------------------------------------

    atr = calculate_atr(
        candles=candles,
        period=atr_period,
    )

    # --------------------------------------------------
    # LATEST MARKET PRICE
    # --------------------------------------------------

    latest_close = (
        candles.iloc[-1]["close"]
    )

    signal = signal.upper()

    # --------------------------------------------------
    # BUY TRAILING STOP
    # --------------------------------------------------

    if signal == "BUY":

        new_stop = (
            latest_close
            - (atr * atr_multiplier)
        )

        return max(
            current_stop,
            new_stop,
        )

    # --------------------------------------------------
    # SELL TRAILING STOP
    # --------------------------------------------------

    if signal == "SELL":

        new_stop = (
            latest_close
            + (atr * atr_multiplier)
        )

        return min(
            current_stop,
            new_stop,
        )

    # --------------------------------------------------
    # INVALID SIGNAL
    # --------------------------------------------------

    raise ValueError(
        "Signal must be BUY or SELL."
    )