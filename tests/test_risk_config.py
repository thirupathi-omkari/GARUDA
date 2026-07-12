import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.risk_config import RiskConfig


def test_risk_config_defaults():

    config = RiskConfig()

    assert config.risk_per_trade_pct == 1.0

    assert config.max_daily_loss_pct == 3.0

    assert config.max_portfolio_exposure_pct == 50.0

    assert config.max_portfolio_risk_pct == 5.0

    assert config.max_open_positions == 5