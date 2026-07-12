import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.transaction_costs import (
    calculate_transaction_costs,
)


def test_transaction_cost_calculation():

    costs = calculate_transaction_costs(
        entry_price=100.00,
        exit_price=102.00,
        quantity=10,
        cost_rate_pct=0.10,
    )

    assert round(costs, 2) == 2.02