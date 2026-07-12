from dataclasses import dataclass
from typing import Optional

from backtesting.backtest_trade import BacktestTrade
from backtesting.session_backtester import (
    run_session_backtest,
)

from risk.risk_manager import (
    RiskDecision,
    RiskManager,
)


@dataclass
class RiskAwareBacktestResult:
    """
    Result returned by the GARUDA
    risk-aware backtesting layer.
    """

    trade: Optional[BacktestTrade]

    risk_decision: Optional[RiskDecision]

    status: str


def run_risk_aware_session_backtest(
    symbol: str,
    strategy,
    session_data,
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
) -> RiskAwareBacktestResult:
    """
    Run the existing session backtester,
    then evaluate the generated trade
    through GARUDA's Risk Manager.
    """

    trade = run_session_backtest(
        symbol=symbol,
        strategy=strategy,
        session_data=session_data,
        stop_loss_pct=stop_loss_pct,
        target_pct=target_pct,
        cost_rate_pct=cost_rate_pct,
        slippage_pct=slippage_pct,
    )

    if trade is None:

        return RiskAwareBacktestResult(
            trade=None,
            risk_decision=None,
            status="NO_TRADE",
        )

    stop_loss_price = (
        trade.entry_price
        * (
            1.0
            - stop_loss_pct / 100.0
        )
        if trade.direction == "BUY"
        else trade.entry_price
        * (
            1.0
            + stop_loss_pct / 100.0
        )
    )

    risk_decision = risk_manager.evaluate_trade(
        entry_price=trade.entry_price,
        stop_loss_price=stop_loss_price,
        lot_size=lot_size,
        current_exposure=current_exposure,
        current_open_risk=current_open_risk,
        current_open_positions=current_open_positions,
        daily_realized_pnl=daily_realized_pnl,
    )

    status = (
        "APPROVED"
        if risk_decision.approved
        else "REJECTED"
    )

    return RiskAwareBacktestResult(
        trade=trade,
        risk_decision=risk_decision,
        status=status,
    )