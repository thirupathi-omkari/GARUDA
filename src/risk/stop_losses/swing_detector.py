import pandas as pd


def find_recent_swing_points(
    candles: pd.DataFrame,
):
    """
    Find the most recent swing high
    and swing low.

    Returns:
        (
            swing_high,
            swing_low,
        )
    """

    swing_high = None

    swing_low = None

    if len(candles) < 5:

        return (
            swing_high,
            swing_low,
        )

    for index in range(
        len(candles) - 2,
        1,
        -1,
    ):

        high = candles.iloc[index]["high"]

        if (
            high > candles.iloc[index - 1]["high"]
            and
            high > candles.iloc[index + 1]["high"]
        ):

            swing_high = high

            break

    for index in range(
        len(candles) - 2,
        1,
        -1,
    ):

        low = candles.iloc[index]["low"]

        if (
            low < candles.iloc[index - 1]["low"]
            and
            low < candles.iloc[index + 1]["low"]
        ):

            swing_low = low

            break

    return (
        swing_high,
        swing_low,
    )