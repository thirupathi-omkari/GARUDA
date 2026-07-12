from dataclasses import dataclass
from typing import Optional

import pandas as pd


from backtesting.backtest_trade import (
    BacktestTrade,
)

from backtesting.candle_replay import (
    replay_session_candles,
)

from backtesting.signal_generator import (
    generate_historical_signals,
)

from backtesting.exit_rules import (
    calculate_exit_levels,
)

from backtesting.exit_simulator import (
    simulate_trade_exit,
)

from backtesting.pnl_calculator import (
    calculate_trade_pnl,
)

from backtesting.slippage import (
    apply_slippage,
)

from risk.risk_manager import (
    RiskDecision,
    RiskManager,
)


@dataclass
class PreExecutionRiskBacktestResult:
    """
    Result returned by GARUDA's
    pre-execution risk backtester.
    """

    trade: Optional[BacktestTrade]

    risk_decision: Optional[RiskDecision]

    status: str


def run_pre_execution_risk_backtest(
    symbol: str,
    strategy,
    session_data: pd.DataFrame,
    risk_manager: RiskManager,
    stop_loss_pct: float,
    target_pct: float,
    cost_rate_pct: float,
    slippage_pct: float,
    lot_size: int,
    current_exposure: float,
    current_open_risk: float,
    current_open_positions: int,
    daily_realized_pnl: float,
) -> PreExecutionRiskBacktestResult:
    """
    Run a session backtest where GARUDA's
    Risk Manager evaluates the proposed trade
    before trade execution.
    """

    # --------------------------------------------------
    # VALIDATE SESSION DATA
    # --------------------------------------------------

    if session_data.empty:

        return PreExecutionRiskBacktestResult(
            trade=None,
            risk_decision=None,
            status="NO_TRADE",
        )

    session_data = (
        session_data
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    # --------------------------------------------------
    # GENERATE HISTORICAL SIGNALS
    # --------------------------------------------------

    signal_results = generate_historical_signals(
        strategy=strategy,
        session_data=session_data,
        replay_function=replay_session_candles,
    )

    # --------------------------------------------------
    # FIND FIRST VALID SIGNAL
    # --------------------------------------------------

    signal_result = None
    signal_index = None

    for index, signal_record in enumerate(
        signal_results
    ):

        result = signal_record["result"]

        if result.signal in (
            "BUY",
            "SELL",
        ):

            signal_result = result
            signal_index = index

            break

    # --------------------------------------------------
    # NO SIGNAL
    # --------------------------------------------------

    if signal_result is None:

        return PreExecutionRiskBacktestResult(
            trade=None,
            risk_decision=None,
            status="NO_TRADE",
        )

    # --------------------------------------------------
    # PREVENT LAST-CANDLE ENTRY
    # --------------------------------------------------

    if signal_index >= len(session_data) - 1:

        return PreExecutionRiskBacktestResult(
            trade=None,
            risk_decision=None,
            status="NO_TRADE",
        )

    # --------------------------------------------------
    # CREATE PROPOSED ENTRY
    # --------------------------------------------------

    direction = signal_result.signal

    entry_candle = session_data.iloc[
        signal_index + 1
    ]

    raw_entry_price = float(
        entry_candle["open"]
    )

    entry_price = apply_slippage(
        price=raw_entry_price,
        direction=direction,
        slippage_pct=slippage_pct,
        is_entry=True,
    )

    entry_time = pd.Timestamp(
        entry_candle["datetime"]
    )

    # --------------------------------------------------
    # CALCULATE PROPOSED EXIT LEVELS
    # --------------------------------------------------

    exit_levels = calculate_exit_levels(
        entry_price=entry_price,
        direction=direction,
        stop_loss_pct=stop_loss_pct,
        target_pct=target_pct,
    )

    stop_loss_price = exit_levels[
        "stop_loss"
    ]

    target_price = exit_levels[
        "target"
    ]

    # --------------------------------------------------
    # RISK MANAGER
    #
    # Risk evaluation happens BEFORE
    # trade creation and execution.
    # --------------------------------------------------

    risk_decision = risk_manager.evaluate_trade(
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        lot_size=lot_size,
        current_exposure=current_exposure,
        current_open_risk=current_open_risk,
        current_open_positions=current_open_positions,
        daily_realized_pnl=daily_realized_pnl,
    )

    # --------------------------------------------------
    # REJECTED BY RISK MANAGER
    # --------------------------------------------------

    if not risk_decision.approved:

        return PreExecutionRiskBacktestResult(
            trade=None,
            risk_decision=risk_decision,
            status="REJECTED",
        )

    # --------------------------------------------------
    # CREATE APPROVED TRADE
    # --------------------------------------------------

    trade = BacktestTrade(
        symbol=symbol,
        strategy_name=(
            strategy.__class__.__name__
        ),
        trade_date=entry_time.date(),
        direction=direction,
        entry_time=entry_time,
        entry_price=entry_price,
        quantity=(
            risk_decision.approved_quantity
        ),
    )

    # --------------------------------------------------
    # FUTURE CANDLES
    # --------------------------------------------------

    future_candles = session_data.iloc[
        signal_index + 1:
    ].copy()

    # --------------------------------------------------
    # SIMULATE TRADE EXIT
    # --------------------------------------------------

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future_candles,
        stop_loss=stop_loss_price,
        target=target_price,
    )

    # --------------------------------------------------
    # APPLY EXIT SLIPPAGE
    # --------------------------------------------------

    trade.exit_price = apply_slippage(
        price=trade.exit_price,
        direction=trade.direction,
        slippage_pct=slippage_pct,
        is_entry=False,
    )

    # --------------------------------------------------
    # CALCULATE FINAL P&L
    # --------------------------------------------------

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=cost_rate_pct,
    )

    # --------------------------------------------------
    # RETURN COMPLETED RESULT
    # --------------------------------------------------

    return PreExecutionRiskBacktestResult(
        trade=trade,
        risk_decision=risk_decision,
        status="EXECUTED",
    )