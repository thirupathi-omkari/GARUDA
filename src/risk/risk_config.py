from dataclasses import dataclass


@dataclass
class RiskConfig:
    """
    Central risk configuration for GARUDA.
    """

    risk_per_trade_pct: float = 1.0

    max_daily_loss_pct: float = 3.0

    max_portfolio_exposure_pct: float = 50.0

    max_portfolio_risk_pct: float = 5.0

    max_open_positions: int = 5