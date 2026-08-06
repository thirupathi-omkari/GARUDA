from enum import Enum

from risk.break_even.risk_reward_break_even import (
    calculate_break_even_stop,
)


class BreakEvenMode(Enum):

    RISK_REWARD = "RISK_REWARD"


def calculate_break_even(
    mode: BreakEvenMode,
    signal: str,
    entry_price: float,
    current_stop: float,
    latest_price: float,
    initial_risk: float,
    trigger_multiple: float,
):
    """
    Master Break-even dispatcher.
    """

    if isinstance(mode, str):

        mode = BreakEvenMode[
            mode.upper()
        ]

    if mode == BreakEvenMode.RISK_REWARD:

        return calculate_break_even_stop(
            signal=signal,
            entry_price=entry_price,
            current_stop=current_stop,
            latest_price=latest_price,
            initial_risk=initial_risk,
            trigger_multiple=trigger_multiple,
        )

    raise NotImplementedError(
        f"{mode} is not implemented."
    )