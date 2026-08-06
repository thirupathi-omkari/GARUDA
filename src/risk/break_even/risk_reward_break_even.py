def calculate_break_even_stop(
    signal: str,
    entry_price: float,
    current_stop: float,
    latest_price: float,
    initial_risk: float,
    trigger_multiple: float = 1.0,
):
    """
    Move stop loss to break-even once the trade
    reaches the specified Risk:Reward trigger.
    """

    signal = signal.upper()

    # --------------------------------------------------
    # BUY
    # --------------------------------------------------

    if signal == "BUY":

        profit = (
            latest_price
            - entry_price
        )

        if profit >= (
            initial_risk
            * trigger_multiple
        ):

            return max(
                current_stop,
                entry_price,
            )

        return current_stop

    # --------------------------------------------------
    # SELL
    # --------------------------------------------------

    if signal == "SELL":

        profit = (
            entry_price
            - latest_price
        )

        if profit >= (
            initial_risk
            * trigger_multiple
        ):

            return min(
                current_stop,
                entry_price,
            )

        return current_stop

    # --------------------------------------------------
    # INVALID SIGNAL
    # --------------------------------------------------

    raise ValueError(
        "Signal must be BUY or SELL."
    )