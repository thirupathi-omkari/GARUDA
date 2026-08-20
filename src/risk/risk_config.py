from dataclasses import dataclass



@dataclass
class RiskConfig:
    """
    Central risk configuration for GARUDA.
    """

    # --------------------------------------------------
    # Position Risk
    # --------------------------------------------------

    risk_per_trade_pct: float = 1.0

    max_daily_loss_pct: float = 3.0

    max_portfolio_exposure_pct: float = 50.0

    max_portfolio_risk_pct: float = 5.0

    max_open_positions: int = 5

    # --------------------------------------------------
    # Stop Loss Configuration
    # --------------------------------------------------

    active_stop_loss_mode: str = "ORB_50"

    atr_period: int = 14

    atr_multiplier: float = 2.0

    risk_reward_ratio: float = 2.0

    vwap_atr_multiplier: float = 0.5

    # --------------------------------------------------
    # Target Configuration
    # --------------------------------------------------

    active_target_mode: str = "RISK_REWARD"
    
    atr_target_multiplier: float = 3.0

    # --------------------------------------------------
    # Trailing Stop Configuration
    # --------------------------------------------------

    active_trailing_stop_mode: str = "ATR"

    atr_trailing_multiplier: float = 2.0

    trailing_stop_enabled: bool = True

    trailing_activation_multiple: float = 2.0

    # --------------------------------------------------
    # Break-even Configuration
    # --------------------------------------------------

    break_even_enabled: bool = True

    active_break_even_mode: str = (
        "RISK_REWARD"
    )

    break_even_trigger_multiple: float = 1.0