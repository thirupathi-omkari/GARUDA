import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from strategy.orb_vwap_strategy import ORBVWAPStrategy
from execution.paper_trading_session import PaperTradingSessionEngine
from execution.paper_order_manager import PaperOrderManager
from execution.paper_position_manager import PaperPositionManager
from execution.risk_managed_paper_executor import RiskManagedPaperExecutor
from execution.simulated_broker import SimulatedBroker
from risk.account import TradingAccount
from risk.equity_curve import EquityCurve
from risk.risk_config import RiskConfig
from risk.risk_manager import RiskManager


def main():
    print("=" * 80)
    print("GARUDA — ORB_VWAP 50% ORB SL + 2R PAPER SMOKE TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # Controlled deterministic candles
    #
    # ORB:
    # 09:15 high = 102, low = 99
    # 09:20 high = 103, low = 100
    # 09:25 high = 104, low = 101
    #
    # ORB high = 104
    # ORB low  = 99
    # ORB range = 5
    # 50% range = 2.5
    #
    # Entry candle close = 106
    #
    # BUY SL = 106 - 2.5 = 103.5
    # Risk   = 2.5
    # 2R     = 111.0
    # ---------------------------------------------------------

    data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                ]
            ),
            "open": [
                100.0,
                101.0,
                102.0,
                103.0,
                105.0,
            ],
            "high": [
                102.0,
                103.0,
                104.0,
                105.0,
                107.0,
            ],
            "low": [
                99.0,
                100.0,
                101.0,
                102.0,
                104.0,
            ],
            "close": [
                101.0,
                102.0,
                103.0,
                104.0,
                106.0,
            ],
            "volume": [
                1000,
                1200,
                1500,
                1800,
                2500,
            ],
        }
    )

    # ---------------------------------------------------------
    # Strategy evaluation
    # ---------------------------------------------------------

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    result = strategy.evaluate(
        symbol="INFY",
        dataframe=data,
    )

    print("\nSTRATEGY RESULT")
    print("-" * 80)
    print(f"Strategy             : {result.strategy_name}")
    print(f"Signal               : {result.signal}")
    print(f"Entry                : {result.entry_price}")
    print(f"SL                   : {result.stop_loss}")
    print(f"Target               : {result.target_price}")
    print(f"BE enabled           : {result.break_even_enabled}")
    print(f"Trailing enabled     : {result.trailing_stop_enabled}")

    assert result.signal == "BUY", (
        f"Expected BUY, got {result.signal}"
    )

    assert result.entry_price == 106.0
    assert result.stop_loss == 103.5
    assert result.target_price == 111.0

    assert result.break_even_enabled is False
    assert result.trailing_stop_enabled is False

    # ---------------------------------------------------------
    # Paper execution infrastructure
    # ---------------------------------------------------------

    initial_capital = 100000.0

    account = TradingAccount.create(
        initial_capital=initial_capital
    )

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(),
    )

    order_manager = PaperOrderManager()
    broker = SimulatedBroker()
    position_manager = PaperPositionManager()

    equity_curve = EquityCurve(
        initial_equity=initial_capital
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

    # ---------------------------------------------------------
    # Process actual StrategyResult through paper engine
    # ---------------------------------------------------------

    paper_result = engine.process_entry(
        strategy_result=result,
        market_price=result.entry_price,
        lot_size=1,
        current_exposure=0.0,
        current_open_risk=0.0,
        current_open_positions=0,
        daily_realized_pnl=0.0,
    )

    print("\nPAPER EXECUTION")
    print("-" * 80)
    print(f"Status               : {paper_result.status}")
    print(
        f"Execution status    : "
        f"{paper_result.execution_result.status}"
    )

    assert paper_result.status == "POSITION_OPEN"
    assert (
        paper_result.execution_result.status
        == "EXECUTED"
    )

    # ---------------------------------------------------------
    # Inspect active exit state
    # ---------------------------------------------------------

    levels = engine._active_exit_levels["INFY"]

    print("\nACTIVE EXIT LEVELS")
    print("-" * 80)

    for key, value in levels.items():
        print(f"{key:<22}: {value}")

    assert levels["entry_price"] == 106.0
    assert levels["stop_loss_price"] == 103.5
    assert levels["initial_stop_loss"] == 103.5
    assert levels["initial_risk"] == 2.5
    assert levels["target_price"] == 111.0

    assert levels["break_even_enabled"] is False
    assert levels["trailing_stop_enabled"] is False

    assert levels["break_even_done"] is False
    assert levels["trailing_active"] is False
    assert levels["trade_state"] == "INITIAL"

    print("\n" + "=" * 80)
    print("SMOKE TEST: PASSED")
    print("=" * 80)
    print("ORB_VWAP")
    print("50% ORB SL       : VERIFIED")
    print("2R TARGET        : VERIFIED")
    print("BE OFF           : VERIFIED")
    print("TRAILING OFF     : VERIFIED")
    print("PAPER EXECUTION  : VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    main()