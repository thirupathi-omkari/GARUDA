from dataclasses import dataclass

from risk.account import TradingAccount
from risk.risk_config import RiskConfig

from risk.risk_calculator import (
    calculate_risk_amount,
)

from risk.position_sizer import (
    calculate_position_size,
)

from risk.quantity_rules import (
    adjust_quantity_to_lot_size,
)

from risk.exposure_control import (
    is_exposure_allowed,
)

from risk.daily_loss_control import (
    is_trading_allowed_by_daily_loss,
)

from risk.position_limit_control import (
    is_new_position_allowed,
)

from risk.portfolio_risk_control import (
    is_portfolio_risk_allowed,
)


@dataclass
class RiskDecision:
    """
    Result returned by the GARUDA Risk Manager.
    """

    approved: bool

    reason: str

    risk_amount: float = 0.0

    raw_position_size: int = 0

    approved_quantity: int = 0

    proposed_exposure: float = 0.0

    stop_loss_price: float = 0.0

    target_price: float = 0.0


class RiskManager:
    """
    Central coordinator for GARUDA risk controls.
    """

    def __init__(
        self,
        account: TradingAccount,
        config: RiskConfig,
    ):

        self.account = account

        self.config = config


    def evaluate_trade(
        self,
        entry_price: float,
        stop_loss_price: float,
        lot_size: int,
        current_exposure: float,
        current_open_risk: float,
        current_open_positions: int,
        daily_realized_pnl: float,
    ) -> RiskDecision:
        """
        Evaluate a proposed trade against
        GARUDA risk rules.
        """

        current_capital = (
            self.account.current_capital
        )

        # --------------------------------------------------
        # DAILY LOSS CHECK
        # --------------------------------------------------

        if not is_trading_allowed_by_daily_loss(
            current_capital=current_capital,
            max_daily_loss_pct=(
                self.config.max_daily_loss_pct
            ),
            daily_realized_pnl=daily_realized_pnl,
        ):

            return RiskDecision(
                approved=False,
                reason="DAILY_LOSS_LIMIT",
            )

        # --------------------------------------------------
        # OPEN POSITION LIMIT CHECK
        # --------------------------------------------------

        if not is_new_position_allowed(
            current_open_positions=(
                current_open_positions
            ),
            max_open_positions=(
                self.config.max_open_positions
            ),
        ):

            return RiskDecision(
                approved=False,
                reason="MAX_OPEN_POSITIONS",
            )

        # --------------------------------------------------
        # RISK AMOUNT
        # --------------------------------------------------

        risk_amount = calculate_risk_amount(
            current_capital=current_capital,
            risk_per_trade_pct=(
                self.config.risk_per_trade_pct
            ),
        )

        # --------------------------------------------------
        # RAW POSITION SIZE
        # --------------------------------------------------

        raw_position_size = calculate_position_size(
            risk_amount=risk_amount,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
        )

        # --------------------------------------------------
        # LOT-SIZE ADJUSTMENT
        # --------------------------------------------------

        approved_quantity = (
            adjust_quantity_to_lot_size(
                position_size=raw_position_size,
                lot_size=lot_size,
            )
        )

        if approved_quantity == 0:

            return RiskDecision(
                approved=False,
                reason="QUANTITY_BELOW_MINIMUM_LOT",
                risk_amount=risk_amount,
                raw_position_size=raw_position_size,
            )

        # --------------------------------------------------
        # PROPOSED EXPOSURE
        # --------------------------------------------------

        proposed_exposure = (
            approved_quantity
            * entry_price
        )

        # --------------------------------------------------
        # EXPOSURE CHECK
        # --------------------------------------------------

        if not is_exposure_allowed(
            current_capital=current_capital,
            max_portfolio_exposure_pct=(
                self.config
                .max_portfolio_exposure_pct
            ),
            current_exposure=current_exposure,
            proposed_exposure=proposed_exposure,
        ):

            return RiskDecision(
                approved=False,
                reason="MAX_PORTFOLIO_EXPOSURE",
                risk_amount=risk_amount,
                raw_position_size=raw_position_size,
                approved_quantity=approved_quantity,
                proposed_exposure=proposed_exposure,
            )

        # --------------------------------------------------
        # PORTFOLIO RISK CHECK
        # --------------------------------------------------

        if not is_portfolio_risk_allowed(
            current_capital=current_capital,
            max_portfolio_risk_pct=(
                self.config.max_portfolio_risk_pct
            ),
            current_open_risk=current_open_risk,
            proposed_trade_risk=risk_amount,
        ):

            return RiskDecision(
                approved=False,
                reason="MAX_PORTFOLIO_RISK",
                risk_amount=risk_amount,
                raw_position_size=raw_position_size,
                approved_quantity=approved_quantity,
                proposed_exposure=proposed_exposure,
            )

        # --------------------------------------------------
        # TRADE APPROVED
        # --------------------------------------------------

        return RiskDecision(
            approved=True,
            reason="APPROVED",
            risk_amount=risk_amount,
            raw_position_size=raw_position_size,
            approved_quantity=approved_quantity,
            proposed_exposure=proposed_exposure,
            stop_loss_price=stop_loss_price,
        )