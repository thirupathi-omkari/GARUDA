from dataclasses import dataclass

import pandas as pd

from execution.controlled_live_paper_trading_session import (
    ControlledLivePaperTradingSession,
)

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

from risk.account import (
    TradingAccount,
)

from risk.risk_config import (
    RiskConfig,
)

from risk.risk_manager import (
    RiskManager,
)


# ============================================================
# DETERMINISTIC STRATEGY RESULT
# ============================================================


@dataclass
class DeterministicStrategyResult:
    """
    Minimal strategy result compatible with GARUDA's
    existing paper-trading session interface.
    """

    symbol: str

    signal: str

    entry_price: float = None

    stop_loss: float = None

    target_price: float = None


# ============================================================
# DETERMINISTIC STRATEGY
# ============================================================


class DeterministicFullStackStrategy:
    """
    Produce one deterministic BUY signal.

    Cycle 1:

        No position exists.
        GARUDA evaluates the strategy.
        BUY signal is generated.

    Cycles 2 and 3:

        An open position exists.
        GARUDA therefore uses the existing
        position-monitoring and exit path.
    """

    def __init__(self):

        self.evaluation_count = 0


    def evaluate(
        self,
        symbol,
        dataframe,
    ):

        self.evaluation_count += 1

        return DeterministicStrategyResult(
            symbol=symbol,
            signal="BUY",
            entry_price=100.0,
            stop_loss=95.0,
            target_price=110.0,
        )


# ============================================================
# ADVANCING DETERMINISTIC MARKET DATA
# ============================================================


class AdvancingFullStackMarketDataFetcher:
    """
    Return one advancing latest candle per polling cycle.

    Cycle 1:

        BUY signal.
        Paper position opens.

    Cycle 2:

        Position remains open.

    Cycle 3:

        Target is reached.
        Position closes.
        Account capital updates.
        Equity curve updates.
    """

    def __init__(self):

        self.call_count = 0

        self.candles = [
            {
                "datetime": pd.Timestamp(
                    "2026-07-14 09:20:00"
                ),
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-14 09:25:00"
                ),
                "open": 100.0,
                "high": 106.0,
                "low": 99.0,
                "close": 105.0,
                "volume": 1200,
            },
            {
                "datetime": pd.Timestamp(
                    "2026-07-14 09:30:00"
                ),
                "open": 105.0,
                "high": 112.0,
                "low": 104.0,
                "close": 111.0,
                "volume": 1500,
            },
        ]


    def __call__(
        self,
        kite,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        candle = self.candles[
            self.call_count
        ]

        self.call_count += 1

        return pd.DataFrame(
            [candle]
        )


# ============================================================
# BUILD REAL GARUDA PAPER-TRADING STACK
# ============================================================


def build_garuda_paper_trading_stack():
    """
    Build GARUDA's actual tested paper-trading stack.

    No fake execution engine is used.
    No fake risk manager is used.
    No fake order manager is used.
    No fake broker is used.
    No fake position manager is used.
    """

    # --------------------------------------------------------
    # AUTHORITATIVE TRADING ACCOUNT
    # --------------------------------------------------------

    account = TradingAccount.create(
        initial_capital=100000.0
    )

    # --------------------------------------------------------
    # EXISTING GARUDA RISK CONFIGURATION
    # --------------------------------------------------------

    risk_config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=50.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    # --------------------------------------------------------
    # EXISTING GARUDA RISK MANAGER
    # --------------------------------------------------------

    risk_manager = RiskManager(
        account=account,
        config=risk_config,
    )

    # --------------------------------------------------------
    # EXISTING GARUDA PAPER COMPONENTS
    # --------------------------------------------------------

    order_manager = PaperOrderManager()

    broker = SimulatedBroker()

    position_manager = PaperPositionManager()

    # --------------------------------------------------------
    # EXISTING GARUDA RISK-MANAGED EXECUTOR
    # --------------------------------------------------------

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=broker,
        position_manager=position_manager,
    )

    # --------------------------------------------------------
    # EXISTING GARUDA PAPER SESSION ENGINE
    # --------------------------------------------------------

    session_engine = PaperTradingSessionEngine(
        executor=executor
    )

    return {
        "account": account,
        "risk_manager": risk_manager,
        "order_manager": order_manager,
        "broker": broker,
        "position_manager": position_manager,
        "executor": executor,
        "session_engine": session_engine,
    }


# ============================================================
# FULL-STACK DEMONSTRATION
# ============================================================


def main():

    print("\n" + "=" * 70)

    print(
        "GARUDA QUANT LAB"
    )

    print(
        "MODULE 9 PART 13F-3A"
    )

    print(
        "FULL-STACK CONTROLLED PAPER TRADING DEMONSTRATION"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # BUILD ACTUAL GARUDA PAPER STACK
    # --------------------------------------------------------

    components = (
        build_garuda_paper_trading_stack()
    )

    account = components["account"]

    order_manager = components[
        "order_manager"
    ]

    position_manager = components[
        "position_manager"
    ]

    executor = components["executor"]

    session_engine = components[
        "session_engine"
    ]

    # --------------------------------------------------------
    # EXISTING GARUDA LIVE RUNNER
    # --------------------------------------------------------

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="DEMO",
        instrument_token=12345,
    )

    # --------------------------------------------------------
    # DETERMINISTIC STRATEGY
    # --------------------------------------------------------

    strategy = (
        DeterministicFullStackStrategy()
    )

    # --------------------------------------------------------
    # DETERMINISTIC ADVANCING MARKET DATA
    # --------------------------------------------------------

    market_data_fetcher = (
        AdvancingFullStackMarketDataFetcher()
    )

    # --------------------------------------------------------
    # EXISTING GARUDA MULTI-SYMBOL POLLING ENGINE
    # --------------------------------------------------------

    polling_engine = (
        LiveMultiSymbolPollingEngine(
            kite=object(),
            runner=runner,
            strategy=strategy,
            session_engine=session_engine,
            poll_interval_seconds=0.0,
            sleep_function=(
                lambda seconds: None
            ),
            market_data_fetcher=(
                market_data_fetcher
            ),
            current_time_provider=(
                lambda: pd.Timestamp(
                    "2026-07-14 10:00:00"
                )
            ),
        )
    )

    # --------------------------------------------------------
    # NEW GARUDA CONTROLLED SESSION
    # --------------------------------------------------------

    session_times = iter(
        [
            pd.Timestamp(
                "2026-07-14 09:15:00"
            ),
            pd.Timestamp(
                "2026-07-14 15:30:00"
            ),
        ]
    )

    controlled_session = (
        ControlledLivePaperTradingSession(
            polling_engine=polling_engine,
            current_time_provider=(
                lambda: next(session_times)
            ),
        )
    )

    # --------------------------------------------------------
    # RUN THREE CONTROLLED POLLING CYCLES
    # --------------------------------------------------------

    result = controlled_session.run(
        cycles=3
    )

    # --------------------------------------------------------
    # DISPLAY POLLING CYCLE RESULTS
    # --------------------------------------------------------

    print("\n[CYCLE RESULTS]")

    print("-" * 70)

    for cycle_result in (
        result.polling_result.cycle_results
    ):

        for symbol_result in (
            cycle_result.symbol_results
        ):

            print(
                f"Cycle "
                f"{cycle_result.cycle_number}"
                f" | Symbol: "
                f"{symbol_result.symbol}"
                f" | Status: "
                f"{symbol_result.status}"
            )

    # --------------------------------------------------------
    # DISPLAY EXECUTION STATE
    # --------------------------------------------------------

    print("\n[EXECUTION STATE]")

    print("-" * 70)

    print(
        f"Strategy Evaluations : "
        f"{strategy.evaluation_count}"
    )

    print(
        f"Paper Orders Created : "
        f"{order_manager.order_count}"
    )

    print(
        f"Open Positions       : "
        f"{position_manager.position_count}"
    )

    print(
        f"Equity Curve Trades  : "
        f"{executor.equity_curve.trade_count}"
    )

    # --------------------------------------------------------
    # DISPLAY FINAL SESSION STATE
    # --------------------------------------------------------

    print("\n[FINAL SESSION STATE]")

    print("-" * 70)

    print(
        f"Session Status       : "
        f"{result.status}"
    )

    print(
        f"Requested Cycles     : "
        f"{result.requested_cycles}"
    )

    print(
        f"Completed Cycles     : "
        f"{result.completed_cycles}"
    )

    print(
        f"Runner Active        : "
        f"{result.runner_summary['running']}"
    )

    print(
        f"Processed Candles    : "
        f"{result.runner_summary['processed_candles']}"
    )

    print(
        f"Generated Signals    : "
        f"{result.runner_summary['generated_signals']}"
    )

    print(
        f"Executed Trades      : "
        f"{result.runner_summary['executed_trades']}"
    )

    print(
        f"Closed Trades        : "
        f"{result.runner_summary['closed_trades']}"
    )

    print(
        f"Open Positions       : "
        f"{result.runner_summary['open_positions']}"
    )

    print(
        f"Initial Capital      : "
        f"{result.initial_capital:.2f}"
    )

    print(
        f"Current Capital      : "
        f"{result.current_capital:.2f}"
    )

    print(
        f"Net Realized P&L     : "
        f"{result.net_realized_pnl:.2f}"
    )

    # --------------------------------------------------------
    # ACCEPTANCE CHECKS
    # --------------------------------------------------------

    assert result.status == "COMPLETED"

    assert result.requested_cycles == 3

    assert result.completed_cycles == 3

    assert (
        result.runner_summary["running"]
        is False
    )

    assert (
        result.runner_summary[
            "processed_candles"
        ]
        == 3
    )

    assert (
        result.runner_summary[
            "generated_signals"
        ]
        == 1
    )

    assert (
        result.runner_summary[
            "executed_trades"
        ]
        == 1
    )

    assert (
        result.runner_summary[
            "closed_trades"
        ]
        == 1
    )

    assert (
        result.runner_summary[
            "open_positions"
        ]
        == 0
    )

    assert strategy.evaluation_count == 1

    assert order_manager.order_count == 1

    assert position_manager.position_count == 0

    assert account.current_capital > (
        account.initial_capital
    )

    print("\n[ACCEPTANCE RESULT]")

    print("-" * 70)

    print(
        "FULL-STACK DETERMINISTIC "
        "INTEGRATION: PASSED"
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":

    main()