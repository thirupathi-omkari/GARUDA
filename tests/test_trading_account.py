import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.account import TradingAccount


def test_trading_account_creation():

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    assert account.initial_capital == 100000.00

    assert account.current_capital == 100000.00