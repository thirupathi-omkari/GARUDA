def calculate_risk_reward_target(
    signal: str,
    entry_price: float,
    stop_loss: float,
    risk_reward_ratio: float,
):
    """
    Calculate Risk:Reward target.
    """

    signal = signal.upper()

    if signal == "BUY":

        risk = (
            entry_price
            - stop_loss
        )

        return (
            entry_price
            + (risk * risk_reward_ratio)
        )

    if signal == "SELL":

        risk = (
            stop_loss
            - entry_price
        )

        return (
            entry_price
            - (risk * risk_reward_ratio)
        )

    raise ValueError(
        "Signal must be BUY or SELL."
    )