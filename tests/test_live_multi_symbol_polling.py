import pandas as pd
import pytest

from execution.live_multi_symbol_polling import (
    LiveMultiSymbolPollingEngine,
)

from execution.live_paper_trading_runner import (
    LivePaperTradingRunner,
)

from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.paper_trading_session import (
    PaperTradingSessionEngine,
)

from execution.risk_managed_paper_executor import (
    RiskManagedPaperExecutor,
)

from execution.simulated_broker import (
    SimulatedBroker,
)

from risk.account import TradingAccount

from risk.risk_config import RiskConfig

from risk.risk_manager import RiskManager

from strategy.strategy_result import StrategyResult


# ============================================================
# TEST STRATEGIES
# ============================================================


class NoSignalStrategy:

    def evaluate(
        self,
        symbol,
        dataframe,
    ):

        return StrategyResult(
            symbol=symbol,
            strategy_name="TEST_NO_SIGNAL",
            signal="NO_SIGNAL",
            reason="Test no signal.",
        )


class BuyStrategy:

    def evaluate(
        self,
        symbol,
        dataframe,
    ):

        latest_close = (
            dataframe.iloc[-1]["close"]
        )

        return StrategyResult(
            symbol=symbol,
            strategy_name="TEST_BUY",
            signal="BUY",
            entry_price=latest_close,
            reason="Test buy signal.",
        )


# ============================================================
# TEST MARKET DATA
# ============================================================


def create_market_data(
    candle_time="2026-07-10 10:00:00",
    close_price=500.0,
):

    return pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(candle_time)
            ],
            "open": [
                close_price
            ],
            "high": [
                close_price + 2.0
            ],
            "low": [
                close_price - 2.0
            ],
            "close": [
                close_price
            ],
            "volume": [
                10000
            ],
        }
    )


# ============================================================
# TEST MARKET DATA FETCHERS
# ============================================================


def successful_market_data_fetcher(
    kite,
    instrument_token,
    from_date,
    to_date,
    interval,
):

    return create_market_data()


def empty_market_data_fetcher(
    kite,
    instrument_token,
    from_date,
    to_date,
    interval,
):

    return pd.DataFrame()


def failing_market_data_fetcher(
    kite,
    instrument_token,
    from_date,
    to_date,
    interval,
):

    raise RuntimeError(
        "Simulated market data failure."
    )


class SequentialMarketDataFetcher:

    def __init__(self):

        self.call_count = 0


    def __call__(
        self,
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        self.call_count += 1

        candle_time = pd.Timestamp(
            "2026-07-10 10:00:00"
        ) + pd.Timedelta(
            minutes=5 * (
                self.call_count - 1
            )
        )

        return create_market_data(
            candle_time=candle_time
        )

# ============================================================
# TEST FACTORIES
# ============================================================


def create_runner(
    symbols=None,
):

    runner = LivePaperTradingRunner()

    if symbols is None:

        symbols = {
            "INFY": 408065,
        }

    for (
        symbol,
        instrument_token,
    ) in symbols.items():

        runner.register_symbol(
            symbol=symbol,
            instrument_token=instrument_token,
        )

    runner.start(
        started_at=pd.Timestamp(
            "2026-07-10 09:15:00"
        )
    )

    return runner


def create_session_engine(
    initial_capital=100000.0,
    max_portfolio_exposure_pct=100.0,
):

    account = TradingAccount.create(
        initial_capital=initial_capital
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=(
            max_portfolio_exposure_pct
        ),
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=config,
    )

    order_manager = PaperOrderManager()

    broker = SimulatedBroker()

    position_manager = (
        PaperPositionManager()
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=broker,
        position_manager=position_manager,
    )

    session_engine = (
        PaperTradingSessionEngine(
            executor=executor
        )
    )

    return (
        session_engine,
        account,
        order_manager,
        position_manager,
    )


def create_polling_engine(
    runner=None,
    strategy=None,
    market_data_fetcher=None,
    sleep_function=None,
    current_time_provider=None,
):

    if runner is None:

        runner = create_runner()

    if strategy is None:

        strategy = NoSignalStrategy()

    if market_data_fetcher is None:

        market_data_fetcher = (
            successful_market_data_fetcher
        )

    if sleep_function is None:

        sleep_function = lambda seconds: None

    if current_time_provider is None:

        current_time_provider = (
            lambda: pd.Timestamp(
                "2026-07-10 10:30:00"
            )
        )

    (
        session_engine,
        account,
        order_manager,
        position_manager,
    ) = create_session_engine()

    engine = LiveMultiSymbolPollingEngine(
        kite=object(),
        runner=runner,
        strategy=strategy,
        session_engine=session_engine,
        interval="5minute",
        lookback_days=5,
        poll_interval_seconds=5.0,
        sleep_function=sleep_function,
        market_data_fetcher=(
            market_data_fetcher
        ),
        current_time_provider=(
            current_time_provider
        ),
    )

    return (
        engine,
        session_engine,
        account,
        order_manager,
        position_manager,
    )

# ============================================================
# VALIDATION TESTS
# ============================================================


def test_polling_requires_positive_cycle_count():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine()

    with pytest.raises(ValueError):

        engine.run(
            cycles=0
        )


def test_polling_requires_integer_cycle_count():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine()

    with pytest.raises(TypeError):

        engine.run(
            cycles=1.5
        )


def test_polling_requires_registered_symbol():

    runner = LivePaperTradingRunner()

    runner.start(
        started_at=pd.Timestamp(
            "2026-07-10 09:15:00"
        )
    )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        runner=runner
    )

    with pytest.raises(ValueError):

        engine.run(
            cycles=1
        )


# ============================================================
# SINGLE SYMBOL POLLING
# ============================================================


def test_single_symbol_polling_cycle_completes():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine()

    result = engine.run(
        cycles=1
    )

    assert result.status == "COMPLETED"

    assert result.requested_cycles == 1

    assert result.completed_cycles == 1

    assert result.total_symbol_polls == 1

    assert (
        result.successful_symbol_polls
        == 1
    )

    assert result.failed_symbol_polls == 0


def test_no_signal_result_is_preserved():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine()

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert symbol_result.status == "NO_SIGNAL"

    assert (
        symbol_result.cycle_result.status
        == "NO_SIGNAL"
    )


# ============================================================
# MULTI-SYMBOL POLLING
# ============================================================


def test_multiple_symbols_are_processed():

    runner = create_runner(
        symbols={
            "INFY": 408065,
            "TCS": 2953217,
            "RELIANCE": 738561,
        }
    )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        runner=runner
    )

    result = engine.run(
        cycles=1
    )

    cycle_result = (
        result.cycle_results[0]
    )

    assert (
        cycle_result.processed_symbols
        == 3
    )

    assert (
        cycle_result.successful_symbols
        == 3
    )

    assert (
        cycle_result.failed_symbols
        == 0
    )

    assert (
        result.total_symbol_polls
        == 3
    )


def test_multiple_polling_cycles_complete():

    fetcher = (
        SequentialMarketDataFetcher()
    )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=fetcher
    )

    result = engine.run(
        cycles=3
    )

    assert result.completed_cycles == 3

    assert result.total_symbol_polls == 3

    assert (
        result.successful_symbol_polls
        == 3
    )

    assert fetcher.call_count == 3


# ============================================================
# SLEEP CONTROL
# ============================================================


def test_sleep_occurs_between_polling_cycles():

    sleep_calls = []

    def test_sleep(seconds):

        sleep_calls.append(seconds)

    fetcher = (
        SequentialMarketDataFetcher()
    )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=fetcher,
        sleep_function=test_sleep,
    )

    engine.run(
        cycles=3
    )

    assert sleep_calls == [
        5.0,
        5.0,
    ]


def test_single_cycle_does_not_sleep():

    sleep_calls = []

    def test_sleep(seconds):

        sleep_calls.append(seconds)

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        sleep_function=test_sleep
    )

    engine.run(
        cycles=1
    )

    assert sleep_calls == []


# ============================================================
# MARKET DATA FAILURE CONTROL
# ============================================================


def test_empty_market_data_is_handled():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            empty_market_data_fetcher
        )
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "NO_MARKET_DATA"
    )

    assert (
        result.successful_symbol_polls
        == 1
    )

    assert result.failed_symbol_polls == 0


def test_market_data_exception_is_isolated():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            failing_market_data_fetcher
        )
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert symbol_result.status == "ERROR"

    assert (
        symbol_result.error_message
        == "Simulated market data failure."
    )

    assert (
        result.successful_symbol_polls
        == 0
    )

    assert result.failed_symbol_polls == 1


# ============================================================
# PAPER EXECUTION
# ============================================================


def test_buy_signal_opens_position():

    (
        engine,
        _,
        _,
        order_manager,
        position_manager,
    ) = create_polling_engine(
        strategy=BuyStrategy()
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "POSITION_OPEN"
    )

    assert order_manager.order_count == 1

    assert (
        position_manager.position_count
        == 1
    )


# ============================================================
# PORTFOLIO STATE
# ============================================================


def test_initial_portfolio_state_is_zero():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine()

    portfolio_state = (
        engine.get_portfolio_state()
    )

    assert (
        portfolio_state[
            "current_exposure"
        ]
        == 0.0
    )

    assert (
        portfolio_state[
            "current_open_risk"
        ]
        == 0.0
    )

    assert (
        portfolio_state[
            "current_open_positions"
        ]
        == 0
    )

    assert (
        portfolio_state[
            "daily_realized_pnl"
        ]
        == 0.0
    )


def test_portfolio_state_updates_after_entry():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        strategy=BuyStrategy()
    )

    engine.run(
        cycles=1
    )

    portfolio_state = (
        engine.get_portfolio_state()
    )

    assert (
        portfolio_state[
            "current_exposure"
        ]
        > 0.0
    )

    assert (
        portfolio_state[
            "current_open_risk"
        ]
        > 0.0
    )

    assert (
        portfolio_state[
            "current_open_positions"
        ]
        == 1
    )


# ============================================================
# DUPLICATE CANDLE CONTROL
# ============================================================


def test_same_candle_is_not_processed_twice():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine()

    result = engine.run(
        cycles=2
    )

    first_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    second_result = (
        result
        .cycle_results[1]
        .symbol_results[0]
    )

    assert first_result.status == "NO_SIGNAL"

    assert (
        second_result.status
        == "DUPLICATE_CANDLE"
    )


# ============================================================
# RESULT STRUCTURE
# ============================================================


def test_polling_cycle_result_contains_symbol_results():

    runner = create_runner(
        symbols={
            "INFY": 408065,
            "TCS": 2953217,
        }
    )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        runner=runner
    )

    result = engine.run(
        cycles=1
    )

    cycle_result = (
        result.cycle_results[0]
    )

    assert cycle_result.cycle_number == 1

    assert (
        len(cycle_result.symbol_results)
        == 2
    )

    symbols = {
        symbol_result.symbol
        for symbol_result
        in cycle_result.symbol_results
    }

    assert symbols == {
        "INFY",
        "TCS",
    }

def test_portfolio_exposure_uses_current_market_price():

    (
        engine,
        session_engine,
        _,
        _,
        position_manager,
    ) = create_polling_engine(
        strategy=BuyStrategy()
    )

    engine.run(
        cycles=1
    )

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    original_entry_price = (
        position.entry_price
    )

    position_manager.update_market_price(
        symbol="INFY",
        market_price=505.0,
    )

    portfolio_state = (
        engine.get_portfolio_state()
    )

    expected_exposure = (
        position.quantity
        * 505.0
    )

    entry_based_exposure = (
        position.quantity
        * original_entry_price
    )

    assert (
        portfolio_state[
            "current_exposure"
        ]
        == expected_exposure
    )

    assert (
        portfolio_state[
            "current_exposure"
        ]
        != entry_based_exposure
    )


def test_portfolio_exposure_changes_with_market_price():

    (
        engine,
        _,
        _,
        _,
        position_manager,
    ) = create_polling_engine(
        strategy=BuyStrategy()
    )

    engine.run(
        cycles=1
    )

    initial_state = (
        engine.get_portfolio_state()
    )

    initial_exposure = (
        initial_state[
            "current_exposure"
        ]
    )

    position_manager.update_market_price(
        symbol="INFY",
        market_price=510.0,
    )

    updated_state = (
        engine.get_portfolio_state()
    )

    updated_exposure = (
        updated_state[
            "current_exposure"
        ]
    )

    assert (
        updated_exposure
        > initial_exposure
    )

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    assert (
        updated_exposure
        == position.quantity * 510.0
    )

def test_market_data_fetcher_receives_date_range():

    captured_arguments = {}

    def date_range_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        captured_arguments[
            "instrument_token"
        ] = instrument_token

        captured_arguments[
            "from_date"
        ] = from_date

        captured_arguments[
            "to_date"
        ] = to_date

        captured_arguments[
            "interval"
        ] = interval

        return create_market_data()

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            date_range_fetcher
        )
    )

    engine.run(
        cycles=1
    )

    assert (
        captured_arguments[
            "instrument_token"
        ]
        == 408065
    )

    assert (
        captured_arguments[
            "from_date"
        ]
        is not None
    )

    assert (
        captured_arguments[
            "to_date"
        ]
        is not None
    )

    assert (
        captured_arguments[
            "from_date"
        ]
        < captured_arguments[
            "to_date"
        ]
    )

    assert (
        captured_arguments[
            "interval"
        ]
        == "5minute"
    )
# ============================================================
# STALE MARKET DATA PROTECTION
# ============================================================


def test_current_date_market_data_is_not_stale():

    current_time = pd.Timestamp(
        "2026-07-14 10:30:00"
    )

    def current_date_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        return create_market_data(
            candle_time=(
                "2026-07-14 10:25:00"
            )
        )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            current_date_fetcher
        )
    )

    engine.current_time_provider = (
        lambda: current_time
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        != "STALE_MARKET_DATA"
    )


def test_previous_date_market_data_is_stale():

    current_time = pd.Timestamp(
        "2026-07-14 10:30:00"
    )

    def stale_date_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        return create_market_data(
            candle_time=(
                "2026-07-13 15:25:00"
            )
        )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            stale_date_fetcher
        )
    )

    engine.current_time_provider = (
        lambda: current_time
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "STALE_MARKET_DATA"
    )

    assert (
        symbol_result.cycle_result
        is None
    )


def test_timezone_aware_current_date_is_not_stale():

    current_time = pd.Timestamp(
        "2026-07-14 10:30:00",
        tz="Asia/Kolkata",
    )

    def timezone_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        dataframe = create_market_data(
            candle_time=(
                "2026-07-14 10:25:00"
            )
        )

        dataframe["datetime"] = (
            dataframe["datetime"]
            .dt.tz_localize(
                "Asia/Kolkata"
            )
        )

        return dataframe

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            timezone_fetcher
        )
    )

    engine.current_time_provider = (
        lambda: current_time
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        != "STALE_MARKET_DATA"
    )


def test_timezone_aware_previous_date_is_stale():

    current_time = pd.Timestamp(
        "2026-07-14 10:30:00",
        tz="Asia/Kolkata",
    )

    def timezone_stale_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        dataframe = create_market_data(
            candle_time=(
                "2026-07-13 15:25:00"
            )
        )

        dataframe["datetime"] = (
            dataframe["datetime"]
            .dt.tz_localize(
                "Asia/Kolkata"
            )
        )

        return dataframe

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            timezone_stale_fetcher
        )
    )

    engine.current_time_provider = (
        lambda: current_time
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "STALE_MARKET_DATA"
    )


def test_timezone_conversion_detects_stale_date():

    current_time = pd.Timestamp(
        "2026-07-14 01:00:00",
        tz="UTC",
    )

    def timezone_conversion_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        dataframe = create_market_data(
            candle_time=(
                "2026-07-13 15:25:00"
            )
        )

        dataframe["datetime"] = (
            dataframe["datetime"]
            .dt.tz_localize(
                "Asia/Kolkata"
            )
        )

        return dataframe

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            timezone_conversion_fetcher
        )
    )

    engine.current_time_provider = (
        lambda: current_time
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "STALE_MARKET_DATA"
    )


def test_stale_market_data_does_not_reach_runner():

    current_time = pd.Timestamp(
        "2026-07-14 10:30:00"
    )

    def stale_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        return create_market_data(
            candle_time=(
                "2026-07-13 15:25:00"
            )
        )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=(
            stale_fetcher
        ),
        current_time_provider=(
            lambda: current_time
        ),
    )

    runner_called = False

    original_process_symbol_cycle = (
        engine.runner.process_symbol_cycle
    )

    def tracking_process_symbol_cycle(
        *args,
        **kwargs,
    ):

        nonlocal runner_called

        runner_called = True

        return original_process_symbol_cycle(
            *args,
            **kwargs,
        )

    engine.runner.process_symbol_cycle = (
        tracking_process_symbol_cycle
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "STALE_MARKET_DATA"
    )

    assert runner_called is False

    assert (
        symbol_result.cycle_result
        is None
    )


def test_stale_market_data_does_not_create_order():

    current_time = pd.Timestamp(
        "2026-07-14 10:30:00"
    )

    def stale_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        return create_market_data(
            candle_time=(
                "2026-07-13 10:25:00"
            )
        )

    (
        engine,
        _,
        account,
        order_manager,
        position_manager,
    ) = create_polling_engine(
        strategy=BuyStrategy(),
        market_data_fetcher=(
            stale_fetcher
        ),
    )

    engine.current_time_provider = (
        lambda: current_time
    )

    result = engine.run(
        cycles=1
    )

    symbol_result = (
        result
        .cycle_results[0]
        .symbol_results[0]
    )

    assert (
        symbol_result.status
        == "STALE_MARKET_DATA"
    )

    assert (
        order_manager.order_count
        == 0
    )

    assert (
        position_manager.position_count
        == 0
    )

    assert (
        account.current_capital
        == account.initial_capital
    )

# ============================================================
# PHASE 16 ACCEPTANCE TESTS
# ============================================================


def test_multi_symbol_portfolio_state_propagates_between_symbols():

    processed_portfolio_states = []

    class TrackingBuyStrategy:

        def evaluate(
            self,
            symbol,
            dataframe,
        ):

            return StrategyResult(
                symbol=symbol,
                strategy_name="TEST_TRACKING_BUY",
                signal="BUY",
                entry_price=(
                    dataframe.iloc[-1]["close"]
                ),
                reason="Test portfolio propagation.",
            )

    runner = create_runner(
        symbols={
            "INFY": 408065,
            "TCS": 2953217,
        }
    )

    (
        engine,
        session_engine,
        _,
        _,
        position_manager,
    ) = create_polling_engine(
        runner=runner,
        strategy=TrackingBuyStrategy(),
    )

    original_process_symbol_cycle = (
        engine.runner.process_symbol_cycle
    )

    def tracking_process_symbol_cycle(
        *args,
        **kwargs,
    ):

        processed_portfolio_states.append(
            {
                "current_exposure": (
                    kwargs["current_exposure"]
                ),
                "current_open_risk": (
                    kwargs["current_open_risk"]
                ),
                "current_open_positions": (
                    kwargs[
                        "current_open_positions"
                    ]
                ),
            }
        )

        return original_process_symbol_cycle(
            *args,
            **kwargs,
        )

    engine.runner.process_symbol_cycle = (
        tracking_process_symbol_cycle
    )

    result = engine.run(
        cycles=1
    )

    assert result.completed_cycles == 1

    assert (
        len(processed_portfolio_states)
        == 2
    )

    # First symbol sees an empty portfolio.
    assert (
        processed_portfolio_states[0][
            "current_open_positions"
        ]
        == 0
    )

    # First symbol opens a position.
    assert (
        position_manager.position_count
        == 1
    )

    # Second symbol must see the first
    # symbol's position before evaluation.
    assert (
        processed_portfolio_states[1][
            "current_open_positions"
        ]
        == 1
    )

    assert (
        processed_portfolio_states[1][
            "current_exposure"
        ]
        > 0.0
    )

    assert (
        processed_portfolio_states[1][
            "current_open_risk"
        ]
        > 0.0
    )


def test_market_data_fetcher_uses_injected_current_time():

    captured_arguments = {}

    def tracking_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        captured_arguments[
            "from_date"
        ] = from_date

        captured_arguments[
            "to_date"
        ] = to_date

        return create_market_data(
            candle_time="2026-07-14 10:25:00"
        )

    fixed_time = pd.Timestamp(
        "2026-07-14 10:30:00"
    )

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        market_data_fetcher=tracking_fetcher,
        current_time_provider=lambda: fixed_time,
    )

    engine.run(
        cycles=1
    )

    assert (
        captured_arguments["to_date"]
        == fixed_time.to_pydatetime()
    )

    assert (
        captured_arguments["from_date"]
        == (
            fixed_time
            - pd.Timedelta(days=5)
        ).to_pydatetime()
    )


def test_multi_symbol_market_data_failure_is_isolated():

    runner = create_runner(
        symbols={
            "INFY": 408065,
            "TCS": 2953217,
            "RELIANCE": 738561,
        }
    )

    call_count = 0

    def mixed_market_data_fetcher(
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        nonlocal call_count

        call_count += 1

        if instrument_token == 408065:

            raise RuntimeError(
                "INFY market-data failure."
            )

        return create_market_data()

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_polling_engine(
        runner=runner,
        market_data_fetcher=(
            mixed_market_data_fetcher
        ),
    )

    result = engine.run(
        cycles=1
    )

    cycle_result = (
        result.cycle_results[0]
    )

    assert call_count == 3

    assert (
        cycle_result.processed_symbols
        == 3
    )

    assert (
        cycle_result.failed_symbols
        == 1
    )

    assert (
        cycle_result.successful_symbols
        == 2
    )

    results_by_symbol = {
        item.symbol: item
        for item in cycle_result.symbol_results
    }

    assert (
        results_by_symbol["INFY"].status
        == "ERROR"
    )

    assert (
        results_by_symbol["INFY"].error_message
        == "INFY market-data failure."
    )

    assert (
        results_by_symbol["TCS"].status
        != "ERROR"
    )

    assert (
        results_by_symbol["RELIANCE"].status
        != "ERROR"
    )