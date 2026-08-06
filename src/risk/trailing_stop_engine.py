from enum import Enum

from risk.trailing.atr_trailing import (
    calculate_atr_trailing_stop,
)


class TrailingStopMode(Enum):

    ATR = "ATR"


def calculate_trailing_stop(
    mode: TrailingStopMode,
    signal: str,
    current_stop: float,
    candles,
):
    """
    Master trailing stop dispatcher.
    """

    if isinstance(mode, str):

        mode = TrailingStopMode[
            mode.upper()
        ]

    if mode == TrailingStopMode.ATR:

        return calculate_atr_trailing_stop(
            signal=signal,
            current_stop=current_stop,
            candles=candles,
        )

    raise NotImplementedError(
        f"{mode} is not implemented."
    )