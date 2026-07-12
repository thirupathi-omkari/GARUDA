import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.account import TradingAccount
from risk.risk_config import RiskConfig

from risk.risk_calculator import (
    calculate_risk_amount,
)


def test_risk_amount_calculation():

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0
    )

    risk_amount = calculate_risk_amount(
        current_capital=account.current_capital,
        risk_per_trade_pct=config.risk_per_trade_pct,
    )

    assert risk_amount == 1000.00