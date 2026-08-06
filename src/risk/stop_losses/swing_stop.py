import pandas as pd

from risk.stop_losses.swing_detector import (
    find_recent_swing_points,
)


def calculate_swing_stop_loss(
    signal: str,
    candles: pd.DataFrame,
):
    """
    Calculate Swing-based stop loss.

    BUY  -> Recent Swing Low

    SELL -> Recent Swing High
    """

    swing_high, swing_low = (
        find_recent_swing_points(
            candles
        )
    )

    signal = signal.upper()

    if signal == "BUY":

        if swing_low is not None:
            return swing_low

        return None

    if signal == "SELL":

        if swing_high is not None:
            return swing_high

        return None

    raise ValueError(
        "Signal must be BUY or SELL."
    )