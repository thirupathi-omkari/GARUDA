from enum import Enum

import pandas as pd

from risk.stop_losses.orb_stop import (
    calculate_orb_stop_loss,
)

from risk.stop_losses.swing_stop import (
    calculate_swing_stop_loss,
)

from risk.stop_losses.atr import (
    calculate_atr_stop_loss,
)

from risk.stop_losses.vwap_stop import (
    calculate_vwap_stop_loss,
)

class StopLossMode(Enum):

    ORB = "ORB"

    SWING = "SWING"

    ATR = "ATR"

    VWAP = "VWAP"


def calculate_stop_loss(
    mode: StopLossMode,
    signal: str,
    entry_price: float,
    opening_high: float,
    opening_low: float,
    candles: pd.DataFrame,
):

    """
     Master stop-loss dispatcher.
    """

    if isinstance(mode, str):

        mode = StopLossMode[mode.upper()]
    

    if mode == StopLossMode.ORB:

        return calculate_orb_stop_loss(
            signal=signal,
            opening_high=opening_high,
            opening_low=opening_low,
        )

    if mode == StopLossMode.SWING:

        stop_loss = calculate_swing_stop_loss(
            signal=signal,
            candles=candles,
        )

        if stop_loss is not None:
            return stop_loss

        return calculate_orb_stop_loss(
            signal=signal,
            opening_high=opening_high,
            opening_low=opening_low,
        )

    # --------------------------------------------------
    # ATR STOP LOSS
    # --------------------------------------------------

    if mode == StopLossMode.ATR:

        return calculate_atr_stop_loss(
            signal=signal,
            entry_price=entry_price,
            candles=candles,
        )


    if mode == StopLossMode.VWAP:

        return calculate_vwap_stop_loss(
            signal=signal,
            vwap=candles.iloc[-1]["vwap"],
            candles=candles,
        )

    raise NotImplementedError(
            f"{mode} is not implemented."
        )

