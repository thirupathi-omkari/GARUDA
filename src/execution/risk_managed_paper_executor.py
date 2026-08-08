from dataclasses import dataclass

from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.simulated_broker import (
    SimulatedBroker,
)

from risk.equity_curve import (
    EquityCurve,
)

from risk.risk_manager import (
    RiskDecision,
    RiskManager,
)


@dataclass
class PaperExecutionResult:
    """
    Result returned by GARUDA's
    risk-managed paper execution layer.
    """

    status: str

    risk_decision: RiskDecision

    reason: str = None

    order: object = None

    position: object = None

    stop_loss_price: float = 0.0


@dataclass
class PaperExitResult:
    """
    Result returned when GARUDA closes
    a virtual paper position.
    """

    status: str

    position: object

    exit_price: float

    realized_pnl: float

    previous_capital: float

    current_capital: float


class RiskManagedPaperExecutor:
    """
    Coordinates GARUDA's existing RiskManager
    with the paper trading execution layer.

    Responsibilities:

    Risk Evaluation
        ↓
    Paper Order Creation
        ↓
    Order Submission
        ↓
    Simulated Execution
        ↓
    Virtual Position Creation
        ↓
    Position Exit
        ↓
    Trading Account Update
        ↓
    Equity Curve Update
    """

    def __init__(
        self,
        risk_manager: RiskManager,
        order_manager: PaperOrderManager,
        broker: SimulatedBroker,
        position_manager: PaperPositionManager,
        equity_curve: EquityCurve = None,
    ):

        self.risk_manager = risk_manager

        self.order_manager = order_manager

        self.broker = broker

        self.position_manager = position_manager

        if equity_curve is None:

            equity_curve = EquityCurve(
                initial_equity=(
                    self.risk_manager
                    .account
                    .current_capital
                )
            )

        self.equity_curve = equity_curve

    @property
    def account(self):
        """
        Expose the authoritative TradingAccount
        managed by RiskManager.
        """

        return self.risk_manager.account


    def execute_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss_price: float,
        market_price: float,
        lot_size: int,
        current_exposure: float,
        current_open_risk: float,
        current_open_positions: int,
        daily_realized_pnl: float,
    ):
        """
        Evaluate and execute a proposed
        paper trade through GARUDA's
        complete risk-managed execution path.
        """

        # --------------------------------------------------
        # RISK EVALUATION
        # --------------------------------------------------

        risk_decision = (
            self.risk_manager.evaluate_trade(
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                lot_size=lot_size,
                current_exposure=current_exposure,
                current_open_risk=current_open_risk,
                current_open_positions=(
                    current_open_positions
                ),
                daily_realized_pnl=(
                    daily_realized_pnl
                ),
            )
        )

        # --------------------------------------------------
        # RISK REJECTION
        # --------------------------------------------------

        if not risk_decision.approved:

            return PaperExecutionResult(
                status="REJECTED",
                risk_decision=risk_decision,
                reason=risk_decision.reason,
                stop_loss_price=risk_decision.stop_loss_price,
            )

        # --------------------------------------------------
        # CREATE PAPER ORDER
        # --------------------------------------------------

        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            quantity=(
                risk_decision.approved_quantity
            ),
            order_type="MARKET",
        )

        # --------------------------------------------------
        # SUBMIT PAPER ORDER
        # --------------------------------------------------

        self.order_manager.submit_order(
            order_id=order.order_id
        )

        # --------------------------------------------------
        # SIMULATED EXECUTION
        # --------------------------------------------------

        self.broker.execute_market_order(
            order=order,
            market_price=market_price,
        )

        # --------------------------------------------------
        # OPEN VIRTUAL POSITION
        # --------------------------------------------------

        position = (
            self.position_manager
            .open_position_from_order(
                order=order
            )
        )

        # --------------------------------------------------
        # RETURN EXECUTION RESULT
        # --------------------------------------------------

        return PaperExecutionResult(
            status="EXECUTED",
            risk_decision=risk_decision,
            reason=risk_decision.reason,
            order=order,
            position=position,
            stop_loss_price=risk_decision.stop_loss_price,
        )


    def close_trade(
        self,
        symbol: str,
        exit_price: float,
    ):
        """
        Close an open paper position,
        update GARUDA's authoritative
        TradingAccount, and record the
        result in the EquityCurve.
        """

        # --------------------------------------------------
        # CAPTURE CAPITAL BEFORE EXIT
        # --------------------------------------------------

        previous_capital = (
            self.risk_manager
            .account
            .current_capital
        )

        # --------------------------------------------------
        # CLOSE PAPER POSITION
        # --------------------------------------------------

        (
            position,
            realized_pnl,
        ) = self.position_manager.close_position(
            symbol=symbol,
            exit_price=exit_price,
        )

        # --------------------------------------------------
        # UPDATE AUTHORITATIVE TRADING ACCOUNT
        # --------------------------------------------------

        self.risk_manager.account.current_capital += (
            realized_pnl
        )

        # --------------------------------------------------
        # UPDATE EXISTING EQUITY CURVE
        # --------------------------------------------------

        self.equity_curve.record_trade(
            pnl=realized_pnl
        )

        # --------------------------------------------------
        # CAPTURE UPDATED CAPITAL
        # --------------------------------------------------

        current_capital = (
            self.risk_manager
            .account
            .current_capital
        )

        # --------------------------------------------------
        # RETURN EXIT RESULT
        # --------------------------------------------------

        return PaperExitResult(
            status="CLOSED",
            position=position,
            exit_price=exit_price,
            realized_pnl=realized_pnl,
            previous_capital=previous_capital,
            current_capital=current_capital,
        )