from enum import Enum

from risk.targets.risk_reward import (
    calculate_risk_reward_target,
)

from risk.targets.atr_target import (
    calculate_atr_target,
)

from risk.targets.support_resistance import (
    calculate_support_resistance_target,
)


class TargetMode(Enum):

    RISK_REWARD = "RISK_REWARD"

    ATR = "ATR"

    SUPPORT_RESISTANCE = (
        "SUPPORT_RESISTANCE"
    )


def calculate_target(
    mode: TargetMode,
    signal: str,
    entry_price: float,
    stop_loss: float,
    candles,
    risk_reward_ratio: float,
):
    """
    Master target dispatcher.
    """

    if isinstance(mode, str):

        mode = TargetMode[
            mode.upper()
        ]

    if mode == TargetMode.RISK_REWARD:

        return (
            calculate_risk_reward_target(
                signal=signal,
                entry_price=entry_price,
                stop_loss=stop_loss,
                risk_reward_ratio=(
                    risk_reward_ratio
                ),
            )
        )

    if mode == TargetMode.ATR:

        return calculate_atr_target(
            signal=signal,
            entry_price=entry_price,
            candles=candles,
        )

    if mode == TargetMode.SUPPORT_RESISTANCE:

        return (
            calculate_support_resistance_target(
                signal=signal,
                candles=candles,
            )
        )

    raise NotImplementedError(
        f"{mode} is not implemented."
    )