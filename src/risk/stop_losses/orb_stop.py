def calculate_orb_stop_loss(
    signal: str,
    opening_high: float,
    opening_low: float,
) -> float:
    """
    Calculate ORB-based stop loss.

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