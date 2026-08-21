import pandas as pd

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


class SellStrategy:

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
            strategy_name="TEST_SELL",
            signal="SELL",
            entry_price=latest_close,
            reason="Test sell signal.",
        )


# ============================================================
# TEST FACTORIES
# ============================================================


def create_market_data(
    candle_time="2026-07-10 10:00:00",
    open_price=500.0,
    high_price=505.0,
    low_price=495.0,
    close_price=500.0,
):

    return pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(candle_time)
            ],
            "open": [
                open_price
            ],
            "high": [
                high_price
            ],
            "low": [
                low_price
            ],
            "close": [
                close_price
            ],
            "volume": [
                10000
            ],
        }
    )


def create_runner():

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
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


# ============================================================
# RUNNER CONTROL TESTS
# ============================================================


def test_cycle_requires_active_runner():

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
    )

    (
        session_engine,
        _,
        _,
        _,
    ) = create_session_engine()

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=create_market_data(),
        strategy=NoSignalStrategy(),
        session_engine=session_engine,
    )

    assert (
        result.status
        == "RUNNER_NOT_ACTIVE"
    )


def test_cycle_rejects_empty_market_data():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        _,
    ) = create_session_engine()

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=pd.DataFrame(),
        strategy=NoSignalStrategy(),
        session_engine=session_engine,
    )

    assert (
        result.status
        == "NO_MARKET_DATA"
    )


def test_cycle_rejects_inactive_market_session():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        _,
    ) = create_session_engine()

    dataframe = create_market_data(
        candle_time=(
            "2026-07-10 08:00:00"
        )
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=NoSignalStrategy(),
        session_engine=session_engine,
    )

    assert (
        result.status
        == "MARKET_SESSION_INACTIVE"
    )


# ============================================================
# CANDLE PROCESSING TESTS
# ============================================================


def test_no_signal_cycle_marks_candle_processed():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        _,
    ) = create_session_engine()

    dataframe = create_market_data()

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=NoSignalStrategy(),
        session_engine=session_engine,
    )

    symbol_state = (
        runner.get_symbol_state("INFY")
    )

    assert result.status == "NO_SIGNAL"

    assert (
        symbol_state.processed_candle_count
        == 1
    )

    assert (
        symbol_state.generated_signal_count
        == 0
    )


def test_duplicate_candle_is_not_processed_twice():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        _,
    ) = create_session_engine()

    dataframe = create_market_data()

    first_result = (
        runner.process_symbol_cycle(
            symbol="INFY",
            dataframe=dataframe,
            strategy=NoSignalStrategy(),
            session_engine=session_engine,
        )
    )

    second_result = (
        runner.process_symbol_cycle(
            symbol="INFY",
            dataframe=dataframe,
            strategy=NoSignalStrategy(),
            session_engine=session_engine,
        )
    )

    symbol_state = (
        runner.get_symbol_state("INFY")
    )

    assert (
        first_result.status
        == "NO_SIGNAL"
    )

    assert (
        second_result.status
        == "DUPLICATE_CANDLE"
    )

    assert (
        symbol_state.processed_candle_count
        == 1
    )


# ============================================================
# BUY ENTRY TESTS
# ============================================================


def test_buy_signal_opens_paper_position():

    runner = create_runner()

    (
        session_engine,
        _,
        order_manager,
        position_manager,
    ) = create_session_engine()

    dataframe = create_market_data(
        close_price=500.0
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    symbol_state = (
        runner.get_symbol_state("INFY")
    )

    assert (
        result.status
        == "POSITION_OPEN"
    )

    assert symbol_state.position_open

    assert (
        symbol_state.generated_signal_count
        == 1
    )

    assert (
        symbol_state.executed_trade_count
        == 1
    )

    assert order_manager.order_count == 1

    assert (
        position_manager.position_count
        == 1
    )


def test_buy_execution_uses_latest_market_close():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        position_manager,
    ) = create_session_engine()

    dataframe = create_market_data(
        close_price=502.50
    )

    runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    assert (
        position.entry_price
        == 502.50
    )


# ============================================================
# SELL ENTRY TEST
# ============================================================


def test_sell_signal_opens_short_position():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        position_manager,
    ) = create_session_engine()

    dataframe = create_market_data(
        close_price=500.0
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=SellStrategy(),
        session_engine=session_engine,
    )

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    assert (
        result.status
        == "POSITION_OPEN"
    )

    assert position.side == "SHORT"


# ============================================================
# RISK REJECTION TEST
# ============================================================


def test_exposure_limit_reduces_quantity_and_executes():

    runner = create_runner()

    (
        session_engine,
        _,
        order_manager,
        position_manager,
    ) = create_session_engine(
        max_portfolio_exposure_pct=10.0
    )

    dataframe = create_market_data(
        close_price=500.0
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    symbol_state = (
        runner.get_symbol_state("INFY")
    )

    assert result.status == "POSITION_OPEN"

    assert symbol_state.executed_trade_count == 1
    assert symbol_state.rejected_trade_count == 0
    assert symbol_state.position_open

    assert order_manager.order_count == 1
    assert position_manager.position_count == 1


# ============================================================
# OPEN POSITION MONITORING
# ============================================================


def test_open_position_is_updated_on_new_candle():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        position_manager,
    ) = create_session_engine()

    entry_data = create_market_data(
        candle_time=(
            "2026-07-10 10:00:00"
        ),
        close_price=500.0,
    )

    runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=entry_data,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    update_data = create_market_data(
        candle_time=(
            "2026-07-10 10:05:00"
        ),
        high_price=506.0,
        low_price=499.0,
        close_price=505.0,
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=update_data,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    assert (
        result.status
        == "POSITION_OPEN"
    )

    assert (
        position.current_price
        == 505.0
    )


# ============================================================
# AUTOMATIC TARGET EXIT
# ============================================================


def test_buy_position_closes_at_target():

    runner = create_runner()

    (
        session_engine,
        account,
        _,
        position_manager,
    ) = create_session_engine()

    entry_data = create_market_data(
        candle_time=(
            "2026-07-10 10:00:00"
        ),
        close_price=500.0,
    )

    runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=entry_data,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    target_data = create_market_data(
        candle_time=(
            "2026-07-10 10:05:00"
        ),
        high_price=511.0,
        low_price=501.0,
        close_price=509.0,
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=target_data,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    symbol_state = (
        runner.get_symbol_state("INFY")
    )

    assert (
        result.status
        == "POSITION_CLOSED"
    )

    assert (
        result.market_candle_result.exit_reason
        == "TARGET"
    )

    assert not symbol_state.position_open

    assert (
        symbol_state.closed_trade_count
        == 1
    )

    assert (
        position_manager.position_count
        == 0
    )

    assert account.current_capital > 100000.0


# ============================================================
# AUTOMATIC STOP LOSS EXIT
# ============================================================


def test_buy_position_closes_at_stop_loss():

    runner = create_runner()

    (
        session_engine,
        account,
        _,
        position_manager,
    ) = create_session_engine()

    entry_data = create_market_data(
        candle_time=(
            "2026-07-10 10:00:00"
        ),
        close_price=500.0,
    )

    runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=entry_data,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    stop_data = create_market_data(
        candle_time=(
            "2026-07-10 10:05:00"
        ),
        high_price=501.0,
        low_price=494.0,
        close_price=496.0,
    )

    result = runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=stop_data,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    symbol_state = (
        runner.get_symbol_state("INFY")
    )

    assert (
        result.status
        == "POSITION_CLOSED"
    )

    assert (
        result.market_candle_result.exit_reason
        == "STOP_LOSS"
    )

    assert not symbol_state.position_open

    assert (
        symbol_state.closed_trade_count
        == 1
    )

    assert (
        position_manager.position_count
        == 0
    )

    assert account.current_capital < 100000.0


# ============================================================
# RUNNER SUMMARY
# ============================================================


def test_runner_summary_reflects_cycle_activity():

    runner = create_runner()

    (
        session_engine,
        _,
        _,
        _,
    ) = create_session_engine()

    dataframe = create_market_data()

    runner.process_symbol_cycle(
        symbol="INFY",
        dataframe=dataframe,
        strategy=BuyStrategy(),
        session_engine=session_engine,
    )

    summary = runner.get_summary()

    assert (
        summary["registered_symbols"]
        == 1
    )

    assert (
        summary["processed_candles"]
        == 1
    )

    assert (
        summary["generated_signals"]
        == 1
    )

    assert (
        summary["executed_trades"]
        == 1
    )

    assert (
        summary["open_positions"]
        == 1
    )