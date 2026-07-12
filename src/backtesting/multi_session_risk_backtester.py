from dataclasses import dataclass, field

import pandas as pd


from backtesting.performance_metrics import (
    generate_backtest_summary,
)

from backtesting.pre_execution_risk_backtester import (
    PreExecutionRiskBacktestResult,
    run_pre_execution_risk_backtest,
)

from backtesting.session_preparer import (
    prepare_historical_sessions,
)

from risk.risk_manager import (
    RiskManager,
)


@dataclass
class MultiSessionRiskBacktestResult:
    """
    Result returned by GARUDA's
    multi-session risk backtester.
    """

    session_results: list[
        PreExecutionRiskBacktestResult
    ] = field(default_factory=list)

    total_sessions: int = 0

    executed_trades: int = 0

    rejected_trades: int = 0

    no_trade_sessions: int = 0

    initial_capital: float = 0.0

    final_capital: float = 0.0

    total_net_pnl: float = 0.0

    return_percentage: float = 0.0

    performance_summary: dict = field(
        default_factory=dict
    )


def run_multi_session_risk_backtest(
    symbol: str,
    strategy,
    historical_data: pd.DataFrame,
    risk_manager: RiskManager,
    stop_loss_pct: float,
    target_pct: float,
    cost_rate_pct: float,
    slippage_pct: float,
    lot_size: int,
) -> MultiSessionRiskBacktestResult:
    """
    Run GARUDA's pre-execution risk backtester
    across multiple historical trading sessions.

    Account capital is updated after every
    executed trade.
    """

    # --------------------------------------------------
    # PREPARE HISTORICAL SESSIONS
    # --------------------------------------------------

    sessions = prepare_historical_sessions(
        historical_data
    )

    # --------------------------------------------------
    # CAPTURE INITIAL CAPITAL
    # --------------------------------------------------

    initial_capital = (
        risk_manager.account.current_capital
    )

    # --------------------------------------------------
    # CREATE RESULT CONTAINER
    # --------------------------------------------------

    result = MultiSessionRiskBacktestResult(
        total_sessions=len(sessions),
        initial_capital=initial_capital,
        final_capital=initial_capital,
    )

    # --------------------------------------------------
    # CREATE EXECUTED TRADE COLLECTION
    # --------------------------------------------------

    executed_trade_list = []

    # --------------------------------------------------
    # PROCESS EACH SESSION
    # --------------------------------------------------

    for session in sessions:

        session_data = session["data"]

        session_result = (
            run_pre_execution_risk_backtest(
                symbol=symbol,
                strategy=strategy,
                session_data=session_data,
                risk_manager=risk_manager,
                stop_loss_pct=stop_loss_pct,
                target_pct=target_pct,
                cost_rate_pct=cost_rate_pct,
                slippage_pct=slippage_pct,
                lot_size=lot_size,
                current_exposure=0.00,
                current_open_risk=0.00,
                current_open_positions=0,
                daily_realized_pnl=0.00,
            )
        )

        result.session_results.append(
            session_result
        )

        # --------------------------------------------------
        # EXECUTED TRADE
        # --------------------------------------------------

        if session_result.status == "EXECUTED":

            result.executed_trades += 1

            trade = session_result.trade

            executed_trade_list.append(
                trade
            )

            # ----------------------------------------------
            # UPDATE ACCOUNT CAPITAL
            # ----------------------------------------------

            risk_manager.account.current_capital += (
                trade.net_pnl
            )

        # --------------------------------------------------
        # REJECTED TRADE
        # --------------------------------------------------

        elif session_result.status == "REJECTED":

            result.rejected_trades += 1

        # --------------------------------------------------
        # NO TRADE
        # --------------------------------------------------

        elif session_result.status == "NO_TRADE":

            result.no_trade_sessions += 1

    # --------------------------------------------------
    # CAPTURE FINAL CAPITAL
    # --------------------------------------------------

    result.final_capital = (
        risk_manager.account.current_capital
    )

    # --------------------------------------------------
    # CALCULATE MULTI-SESSION P&L
    # --------------------------------------------------

    result.total_net_pnl = (
        result.final_capital
        - result.initial_capital
    )

    result.return_percentage = (
        result.total_net_pnl
        / result.initial_capital
    ) * 100

    # --------------------------------------------------
    # GENERATE PERFORMANCE SUMMARY
    # --------------------------------------------------

    result.performance_summary = (
        generate_backtest_summary(
            executed_trade_list
        )
    )

    # --------------------------------------------------
    # RETURN FINAL RESULT
    # --------------------------------------------------

    return result