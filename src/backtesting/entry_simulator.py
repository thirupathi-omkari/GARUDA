from backtesting.backtest_trade import BacktestTrade


def simulate_entry(
    symbol,
    strategy_name,
    signal_record,
    next_candle,
):
    """Create a backtest trade from a signal and next candle."""

    if signal_record is None:
        return None

    if next_candle is None:
        return None

    result = signal_record["result"]

    if result.signal not in (
        "BUY",
        "SELL",
    ):
        return None

    entry_time = next_candle["datetime"]
    entry_price = next_candle["open"]

    trade_date = entry_time.date()

    trade = BacktestTrade(
        symbol=symbol,
        strategy_name=strategy_name,
        trade_date=trade_date,
        direction=result.signal,
        entry_time=entry_time,
        entry_price=entry_price,
        quantity=1,
    )

    return trade