def calculate_orb_stop_loss(
    signal: str,
    opening_high: float,
    opening_low: float,
) -> float:
    """
    Calculate existing ORB-based stop loss.

    BUY  -> ORB Low
    SELL -> ORB High
    """

    signal = signal.upper()

    if signal == "BUY":
        return opening_low

    if signal == "SELL":
        return opening_high

    raise ValueError(
        "Signal must be BUY or SELL."
    )


def calculate_orb_50_stop_loss(
    signal: str,
    entry_price: float,
    opening_high: float,
    opening_low: float,
) -> float:
    """
    Calculate 50% ORB-range stop loss.

    ORB range = opening_high - opening_low

    BUY:
        SL = entry - 50% of ORB range

    SELL:
        SL = entry + 50% of ORB range
    """

    signal = signal.upper()

    orb_range = (
        float(opening_high)
        - float(opening_low)
    )

    if orb_range <= 0:
        raise ValueError(
            "ORB range must be greater than zero."
        )

    half_range = orb_range * 0.50

    if signal == "BUY":
        return float(entry_price) - half_range

    if signal == "SELL":
        return float(entry_price) + half_range

    raise ValueError(
        "Signal must be BUY or SELL."
    )
# Backward-compatible alias
def calculate_orb_stop(
    signal: str,
    opening_high: float,
    opening_low: float,
):
    return calculate_orb_stop_loss(
        signal=signal,
        opening_high=opening_high,
        opening_low=opening_low,
    )

