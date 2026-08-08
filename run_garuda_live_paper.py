"""
GARUDA Quant Lab
Module 9 Part 13F-3B / 13F-3C

Manual Real-Kite Live Paper Trading Launcher
with Signal CSV Journal.

REAL KITE MARKET DATA.
PAPER EXECUTION ONLY.
NO REAL BROKER ORDERS.
"""

import sys
from datetime import datetime, time
from pathlib import Path




PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config.market_session import (
    MARKET_OPEN,
    ENTRY_CUTOFF,
    BROKER_SQUARE_OFF,
    MARKET_CLOSE,
    PROGRAM_EXIT,
    AUTO_SQUARE_OFF,
)

from broker.session_manager import create_authenticated_session

from data.instrument_resolver import resolve_instrument_token

from execution.controlled_live_paper_trading_session import (
    ControlledLivePaperTradingSession,
)

from execution.live_multi_symbol_polling import (
    LiveMultiSymbolPollingEngine,
)

from execution.live_paper_trading_runner import (
    LivePaperTradingRunner,
)

from execution.paper_order_manager import PaperOrderManager

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.paper_trading_session import (
    PaperTradingSessionEngine,
)

from execution.risk_managed_paper_executor import (
    RiskManagedPaperExecutor,
)

from execution.signal_csv_journal import SignalCSVJournal

from execution.simulated_broker import SimulatedBroker

from risk.account import TradingAccount

from risk.risk_config import RiskConfig

from risk.risk_manager import RiskManager

from strategy.orb_vwap_strategy import ORBVWAPStrategy


SYMBOLS = [
    "INFY",
    "TCS",
    "RELIANCE",
    "HDFCBANK",
    "ICICIBANK",
]

INITIAL_CAPITAL = 100000.0

INTERVAL = "5minute"

LOOKBACK_DAYS = 5

POLL_INTERVAL_SECONDS = 300.0

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


SIGNAL_CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "logs"
    / "garuda_signals.csv"
)


def create_garuda_components():
    """
    Build GARUDA's existing paper-trading stack.
    """

    account = TradingAccount.create(
        initial_capital=INITIAL_CAPITAL
    )

    risk_config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=risk_config,
    )

    order_manager = PaperOrderManager()

    simulated_broker = SimulatedBroker()

    position_manager = PaperPositionManager()

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=simulated_broker,
        position_manager=position_manager,
    )

    session_engine = PaperTradingSessionEngine(
        executor=executor
    )

    runner = LivePaperTradingRunner()

    strategy = ORBVWAPStrategy()

    signal_journal = SignalCSVJournal(
        file_path=SIGNAL_CSV_FILE
    )

    return {
        "account": account,
        "risk_manager": risk_manager,
        "order_manager": order_manager,
        "simulated_broker": simulated_broker,
        "position_manager": position_manager,
        "executor": executor,
        "session_engine": session_engine,
        "runner": runner,
        "strategy": strategy,
        "signal_journal": signal_journal,
    }


def register_symbols(
    kite,
    runner,
):
    """
    Resolve Kite instrument tokens and register symbols.
    """

    print()
    print("=" * 70)
    print("GARUDA SYMBOL REGISTRATION")
    print("=" * 70)

    registered_symbols = []

    failed_symbols = []

    for symbol in SYMBOLS:

        print()
        print(f"Resolving {symbol}...")

        try:

            instrument_token = resolve_instrument_token(
                kite=kite,
                tradingsymbol=symbol,
                exchange="NSE",
            )

            runner.register_symbol(
                symbol=symbol,
                instrument_token=instrument_token,
            )

            registered_symbols.append(symbol)

            print(
                f"{symbol:<12} : REGISTERED"
            )

        except Exception as error:

            failed_symbols.append(symbol)

            print(
                f"{symbol:<12} : FAILED"
            )

            print(
                f"Reason       : {error}"
            )

    return registered_symbols, failed_symbols

from math import ceil

def calculate_remaining_cycles():
    """
    Calculate the number of polling cycles remaining
    until broker square-off time.
    """

    now = datetime.now()

    square_off_dt = datetime.combine(
        now.date(),
        BROKER_SQUARE_OFF,
    )

    if now >= square_off_dt:
        return 0

    remaining_seconds = (
        square_off_dt - now
    ).total_seconds()

    return max(
        1,
        ceil(
            remaining_seconds /
            POLL_INTERVAL_SECONDS
        )
    )


def print_header():

    print()
    print("=" * 70)
    print("GARUDA QUANT LAB")
    print("MANUAL REAL-KITE LIVE PAPER TRADING SESSION")
    print("=" * 70)

    print()

    print("Execution Mode       : PAPER TRADING")

    print("Real Broker Orders   : DISABLED")

    print(
        f"Initial Capital      : {INITIAL_CAPITAL:.2f}"
    )

    print(
        f"Market Interval      : {INTERVAL}"
    )

    print(
        f"Polling Interval     : "
        f"{POLL_INTERVAL_SECONDS:.0f} seconds"
    )

    print(
        "Requested Cycles     : Auto (Until Market Close)"
    )

    print(
        f"Signal CSV           : {SIGNAL_CSV_FILE}"
    )

    print()

    print("Symbols:")

    for symbol in SYMBOLS:
        print(f"  - {symbol}")

    print()

    print("=" * 70)


def print_final_report(
    result,
    registered_symbols,
    failed_symbols,
    account,
    position_manager,
):

    print()
    print("=" * 70)
    print("GARUDA MANUAL LIVE PAPER SESSION RESULT")
    print("=" * 70)

    print()

    print(
        f"Session Status       : {result.status}"
    )

    print(
        f"Requested Cycles     : {result.requested_cycles}"
    )

    print(
        f"Completed Cycles     : {result.completed_cycles}"
    )

    print(
        f"Registered Symbols   : "
        f"{len(registered_symbols)}"
    )

    print(
        f"Failed Symbols       : "
        f"{len(failed_symbols)}"
    )

    print()

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
        f"Rejected Trades      : "
        f"{result.runner_summary['rejected_trades']}"
    )

    print(
        f"Closed Trades        : "
        f"{result.runner_summary['closed_trades']}"
    )

    print(
        f"Open Positions       : "
        f"{position_manager.position_count}"
    )

    print()

    print(
        f"Initial Capital      : "
        f"{result.initial_capital:.2f}"
    )

    print(
        f"Current Capital      : "
        f"{account.current_capital:.2f}"
    )

    net_realized_pnl = (
        account.current_capital
        - account.initial_capital
    )

    print(
        f"Net Realized P&L     : "
        f"{net_realized_pnl:.2f}"
    )

    print(
        f"Net Realized P&L     : "
        f"{account.realized_pnl:.2f}"
    )

    print()

    print(
        f"Signal CSV           : {SIGNAL_CSV_FILE}"
    )

    print()

    print("=" * 70)
    print("REAL BROKER ORDERS WERE NOT SENT")
    print("=" * 70)


def main():

    print_header()

    print()
    print("Authenticating Kite session...")

    kite = create_authenticated_session()

    if kite is None:

        print()
        print("=" * 70)
        print("GARUDA STARTUP FAILED")
        print("=" * 70)
        print("Reason : Kite authentication failed.")
        print("GARUDA will exit.")
        print("=" * 70)

        return

    print("Kite Authentication : SUCCESS")

    print()

    now = datetime.now().time()

    market_open = MARKET_OPEN
    market_close = MARKET_CLOSE

    print("=" * 70)
    print("GARUDA MARKET STATUS")
    print("=" * 70)
    print(f"Current Time : {now.strftime('%H:%M:%S')}")

    if now < market_open:

        print("Market Status : PRE-MARKET")
        print("GARUDA is waiting for market open (09:15).")
        return

    if now >= market_close:

        print("Market Status : CLOSED")
        print("Today's trading session has ended.")
        return

    print("Market Status : OPEN")
    print("=" * 70)
    print()

    print()
    print("Creating GARUDA paper-trading stack...")

    components = create_garuda_components()

    print("GARUDA Stack         : READY")

    (
        registered_symbols,
        failed_symbols,
    ) = register_symbols(
        kite=kite,
        runner=components["runner"],
    )

    if not registered_symbols:

        raise RuntimeError(
            "No symbols were registered. "
            "GARUDA session cannot start."
        )

    polling_engine = LiveMultiSymbolPollingEngine(
        kite=kite,
        runner=components["runner"],
        strategy=components["strategy"],
        session_engine=components["session_engine"],
        interval=INTERVAL,
        lookback_days=LOOKBACK_DAYS,
        poll_interval_seconds=POLL_INTERVAL_SECONDS,
    )

    controlled_session = (
        ControlledLivePaperTradingSession(
            polling_engine=polling_engine
        )
    )

    print()
    print("=" * 70)
    print("STARTING CONTROLLED REAL-KITE PAPER SESSION")
    print("=" * 70)

    print()
    print("GARUDA will poll real Kite market data.")
    print("All execution remains simulated.")

    print()
    print(
        "BUY/SELL signals will be processed by the "
        "existing GARUDA stack."
    )

    print(
        "Signal CSV component is ready at:"
    )

    print(SIGNAL_CSV_FILE)

    print()

    remaining_cycles = calculate_remaining_cycles()

    print()
    print("=" * 70)
    print("GARUDA SESSION PLAN")
    print("=" * 70)

    print(
        f"Broker Square-Off : "
        f"{BROKER_SQUARE_OFF.strftime('%H:%M')}"
    )

    print(
        f"Market Close      : "
        f"{MARKET_CLOSE.strftime('%H:%M')}"
    )

    print(
        f"Program Exit      : "
        f"{PROGRAM_EXIT.strftime('%H:%M')}"
    )

    print(
        f"Remaining Cycles  : "
        f"{remaining_cycles}"
    )

    print(
        f"Estimated Runtime : "
        f"{remaining_cycles * POLL_INTERVAL_SECONDS / 3600:.2f} Hours"
    )

    print("=" * 70)
    print()

    result = controlled_session.run(
        cycles=remaining_cycles
    )

    # --------------------------------------------------
    # END-OF-DAY PAPER SETTLEMENT
    # --------------------------------------------------

    session_engine = (
        components["session_engine"]
    )

    if (
        AUTO_SQUARE_OFF
        and session_engine
        .executor
        .position_manager
        .position_count > 0
    ):

        print()
        print("=" * 70)
        print("GARUDA END-OF-DAY SQUARE OFF")
        print("=" * 70)

        closed_positions = (
            session_engine
            .square_off_all_positions()
        )

        result.runner_summary["closed_trades"] += (
            len(closed_positions)
        )

        result.runner_summary["open_positions"] = (
            session_engine
            .executor
            .position_manager
            .position_count
        )

        print(
            f"Positions Closed : "
            f"{len(closed_positions)}"
        )

        print("=" * 70)

    print_final_report(
        result=result,
        registered_symbols=registered_symbols,
        failed_symbols=failed_symbols,
        account=components["account"],
        position_manager=(
            components["session_engine"]
            .executor
            .position_manager
        ),
    )


if __name__ == "__main__":
    main()

