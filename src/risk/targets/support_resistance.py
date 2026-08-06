import pandas as pd

from risk.stop_losses.swing_detector import (
    find_recent_swing_points,
)


def calculate_support_resistance_target(
    signal: str,
    candles: pd.DataFrame,
):
    """
    Calculate Support / Resistance target.
    """

    swing_high, swing_low = (
        find_recent_swing_points(
            candles
        )
    )

    signal = signal.upper()

    if signal == "BUY":

        return swing_high

    if signal == "SELL":

        return swing_low

    raise ValueError(
        "Signal must be BUY or SELL."
    )