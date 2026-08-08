import sys
from datetime import datetime

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from execution.live_paper_trading_runner import (
    LivePaperTradingRunner,
)

from execution.paper_trading_session import (
    PaperTradingSessionEngine,
)

from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.risk_managed_paper_executor import (
    RiskManagedPaperExecutor,
)

from execution.simulated_broker import (
    SimulatedBroker,
)

from risk.account import TradingAccount

from risk.equity_curve import EquityCurve

from risk.risk_config import RiskConfig

from risk.risk_manager import RiskManager

from strategy.strategy_result import StrategyResult


def create_session_engine():
    account = TradingAccount.create(
        initial_capital=100000.0
    )

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(),
    )

    order_manager = PaperOrderManager()

    broker = SimulatedBroker()

    position_manager = PaperPositionManager()

    equity_curve = EquityCurve(
        initial_equity=100000.0
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=broker,
        position_manager=position_manager,
        equity_curve=equity_curve,
    )

    engine = PaperTradingSessionEngine(
        executor=executor
    )

    return (
        engine,
        position_manager,
    )


def open_infy_position(
    session_engine,
    runner,
):
    pass