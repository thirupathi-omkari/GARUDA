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

        Order of checks:

        1. Daily loss
        2. Maximum open positions
        3. Risk amount
        4. Raw position size
        5. Lot-size adjustment
        6. Portfolio exposure
        7. Portfolio risk
        8. Approval
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
                approved_quantity=0,
                proposed_exposure=0.0,
                stop_loss_price=stop_loss_price,
            )

        # --------------------------------------------------
        # PROPOSED EXPOSURE
        # --------------------------------------------------

        proposed_exposure = (
            approved_quantity
            * entry_price
        )

        # --------------------------------------------------
        # PORTFOLIO EXPOSURE CHECK
        # --------------------------------------------------

        if not is_exposure_allowed(
            current_capital=current_capital,
            max_portfolio_exposure_pct=(
                self.config.max_portfolio_exposure_pct
            ),
            current_exposure=current_exposure,
            proposed_exposure=proposed_exposure,
        ):

            max_portfolio_exposure = (
                current_capital
                * self.config.max_portfolio_exposure_pct
                / 100.0
            )

            available_exposure = max(
                max_portfolio_exposure - current_exposure,
                0.0,
            )

            max_affordable_quantity = int(
                available_exposure // entry_price
            ) if entry_price > 0 else 0

            max_affordable_quantity = (
                max_affordable_quantity // lot_size
            ) * lot_size if lot_size > 0 else 0

            print()
            print('\n' + '=' * 70)
            print('GARUDA PORTFOLIO EXPOSURE AUDIT — REJECTION')
            print('=' * 70)
            print(f'Current Capital              : {current_capital:,.2f}')
            print(f'Max Exposure Limit           : {self.config.max_portfolio_exposure_pct:.2f}%')
            print(f'Max Portfolio Exposure       : {max_portfolio_exposure:,.2f}')
            print(f'Current Open Exposure        : {current_exposure:,.2f}')
            print(f'Available Exposure           : {available_exposure:,.2f}')
            print('-' * 70)
            print(f'Entry Price                  : {entry_price:,.2f}')
            print(f'Stop Loss Price              : {stop_loss_price:,.2f}')
            print(f'Lot Size                     : {lot_size:,}')
            print(f'Risk Amount                  : {risk_amount:,.2f}')
            print(f'Raw Position Size            : {raw_position_size:,}')
            print(f'Requested Quantity            : {approved_quantity:,}')
            print(f'Requested Trade Exposure      : {proposed_exposure:,.2f}')
            print(f'Max Affordable Quantity       : {max_affordable_quantity:,}')
            print(f'Max Affordable Exposure      : {max_affordable_quantity * entry_price:,.2f}')
            print('-' * 70)
            print(f'Current Exposure + Required  : {current_exposure + proposed_exposure:,.2f}')
            print(f'Exposure Limit                : {max_portfolio_exposure:,.2f}')
            print('Decision                     : REJECTED')
            print('Reason                       : MAX_PORTFOLIO_EXPOSURE')
            print('=' * 70)

            return RiskDecision(
                approved=False,
                reason="MAX_PORTFOLIO_EXPOSURE",
                risk_amount=risk_amount,
                raw_position_size=raw_position_size,
                approved_quantity=approved_quantity,
                proposed_exposure=proposed_exposure,
                stop_loss_price=stop_loss_price,
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
                stop_loss_price=stop_loss_price,
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