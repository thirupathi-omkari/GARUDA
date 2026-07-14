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


# ============================================================
# DEMO SUPPORT COMPONENTS
# ============================================================


@dataclass
class DemoStrategyResult:
    symbol: str
    signal: str
    entry_price: float = None
    stop_loss: float = None
    target_price: float = None


class DeterministicDemoStrategy:
    """
    Produce one BUY signal when GARUDA first evaluates
    the strategy.

    Later cycles contain an existing open position, so
    the runner delegates those candles to the existing
    paper-trading session engine instead of evaluating
    the strategy again.
    """

    def __init__(self):

        self.evaluation_count = 0


    def evaluate(
        self,
        symbol,
        dataframe,
    ):

        self.evaluation_count += 1

        return DemoStrategyResult(
            symbol=symbol,
            signal="BUY",
            entry_price=100.0,
            stop_loss=95.0,
            target_price=110.0,
        )


class DemoAccount:

    def __init__(self):

        self.initial_capital = 100000.0

        self.current_capital = 100000.0


class DemoRiskManager:

    def __init__(self):

        self.account = DemoAccount()


class DemoPosition:

    def __init__(
        self,
        symbol,
        side,
        entry_price,
        quantity,
    ):

        self.symbol = symbol

        self.side = side

        self.entry_price = entry_price

        self.quantity = quantity

        self.current_price = entry_price

        self.unrealized_pnl = 0.0


class DemoPositionManager:

    def __init__(self):

        self.positions = []


    @property
    def position_count(self):

        return len(self.positions)


class DemoExecutor:

    def __init__(self):

        self.risk_manager = DemoRiskManager()

        self.position_manager = (
            DemoPositionManager()
        )


class DemoSessionResult:

    def __init__(
        self,
        status,
    ):

        self.status = status


class DemoMarketCandleResult:

    def __init__(
        self,
        status,
    ):

        self.status = status


class DeterministicDemoSessionEngine:
    """
    Minimal deterministic session engine used only to
    demonstrate the real GARUDA runner, polling engine,
    and controlled-session lifecycle.

    No production GARUDA source code is modified.
    """

    def __init__(self):

        self.executor = DemoExecutor()

        self._active_exit_levels = {}


    def process_entry(
        self,
        strategy_result,
        market_price,
        lot_size,
        current_exposure,
        current_open_risk,
        current_open_positions,
        daily_realized_pnl,
        stop_loss_pct,
        target_pct,
    ):

        position = DemoPosition(
            symbol=strategy_result.symbol,
            side="LONG",
            entry_price=strategy_result.entry_price,
            quantity=1,
        )

        self.executor.position_manager.positions.append(
            position
        )

        self._active_exit_levels[
            strategy_result.symbol
        ] = {
            "direction": "BUY",
            "stop_loss_price": (
                strategy_result.stop_loss
            ),
            "target_price": (
                strategy_result.target_price
            ),
        }

        return DemoSessionResult(
            status="POSITION_OPEN"
        )


    def process_market_candle(
        self,
        symbol,
        candle,
    ):

        position = (
            self.executor
            .position_manager
            .positions[0]
        )

        position.current_price = candle["close"]

        position.unrealized_pnl = (
            position.current_price
            - position.entry_price
        ) * position.quantity

        target_price = (
            self._active_exit_levels[
                symbol
            ][
                "target_price"
            ]
        )

        if candle["high"] >= target_price:

            realized_pnl = (
                target_price
                - position.entry_price
            ) * position.quantity

            self.executor.risk_manager.account.current_capital += (
                realized_pnl
            )

            self.executor.position_manager.positions.clear()

            self._active_exit_levels.pop(
                symbol
            )

            return DemoMarketCandleResult(
                status="POSITION_CLOSED"
            )

        return DemoMarketCandleResult(
            status="POSITION_OPEN"
        )


    def get_exit_levels(
        self,
        symbol,
    ):

        if symbol not in self._active_exit_levels:

            raise ValueError(
                "Exit levels not found."
            )

        return dict(
            self._active_exit_levels[
                symbol
            ]
        )


# ============================================================
# DETERMINISTIC MARKET DATA
# ============================================================


class AdvancingMarketDataFetcher:
    """
    Return a different latest candle on every polling cycle.

    Cycle 1:
        BUY entry at 100.

    Cycle 2:
        Position remains open.

    Cycle 3:
        Target 110 is reached.
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
# DEMONSTRATION
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
        "CONTROLLED MULTI-CYCLE PAPER TRADING DEMONSTRATION"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # CREATE EXISTING GARUDA RUNNER
    # --------------------------------------------------------

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="DEMO",
        instrument_token=12345,
    )

    # --------------------------------------------------------
    # CREATE DETERMINISTIC COMPONENTS
    # --------------------------------------------------------

    strategy = DeterministicDemoStrategy()

    session_engine = (
        DeterministicDemoSessionEngine()
    )

    market_data_fetcher = (
        AdvancingMarketDataFetcher()
    )

    # --------------------------------------------------------
    # CREATE EXISTING GARUDA POLLING ENGINE
    # --------------------------------------------------------

    polling_engine = (
        LiveMultiSymbolPollingEngine(
            kite=object(),
            runner=runner,
            strategy=strategy,
            session_engine=session_engine,
            poll_interval_seconds=0.0,
            sleep_function=lambda seconds: None,
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
    # CREATE NEW CONTROLLED SESSION
    # --------------------------------------------------------

    controlled_session = (
        ControlledLivePaperTradingSession(
            polling_engine=polling_engine,
            current_time_provider=iter(
                [
                    pd.Timestamp(
                        "2026-07-14 09:15:00"
                    ),
                    pd.Timestamp(
                        "2026-07-14 15:30:00"
                    ),
                ]
            ).__next__,
        )
    )

    # --------------------------------------------------------
    # RUN THREE CONTROLLED CYCLES
    # --------------------------------------------------------

    result = controlled_session.run(
        cycles=3
    )

    # --------------------------------------------------------
    # DISPLAY EACH CYCLE
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
                f"Cycle {cycle_result.cycle_number}"
                f" | Symbol: {symbol_result.symbol}"
                f" | Status: {symbol_result.status}"
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

    print("\n" + "=" * 70)


if __name__ == "__main__":

    main()