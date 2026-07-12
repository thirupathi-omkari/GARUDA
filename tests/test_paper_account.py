import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from execution.paper_account import (
    PaperTradingAccount,
)


def test_paper_account_creation():

    account = PaperTradingAccount.create(
        initial_capital=100000.00
    )

    assert account.initial_capital == 100000.00

    assert account.current_capital == 100000.00

    assert account.available_cash == 100000.00

    assert account.realized_pnl == 0.00


def test_paper_account_requires_positive_capital():

    with pytest.raises(ValueError):

        PaperTradingAccount.create(
            initial_capital=0.00
        )

    with pytest.raises(ValueError):

        PaperTradingAccount.create(
            initial_capital=-100000.00
        )


def test_paper_account_records_profit():

    account = PaperTradingAccount.create(
        initial_capital=100000.00
    )

    account.record_realized_pnl(
        pnl=5000.00
    )

    assert account.current_capital == 105000.00

    assert account.available_cash == 105000.00

    assert account.realized_pnl == 5000.00


def test_paper_account_records_loss():

    account = PaperTradingAccount.create(
        initial_capital=100000.00
    )

    account.record_realized_pnl(
        pnl=-3000.00
    )

    assert account.current_capital == 97000.00

    assert account.available_cash == 97000.00

    assert account.realized_pnl == -3000.00


def test_paper_account_records_multiple_trade_results():

    account = PaperTradingAccount.create(
        initial_capital=100000.00
    )

    account.record_realized_pnl(
        pnl=5000.00
    )

    account.record_realized_pnl(
        pnl=-2000.00
    )

    account.record_realized_pnl(
        pnl=3000.00
    )

    assert account.current_capital == 106000.00

    assert account.available_cash == 106000.00

    assert account.realized_pnl == 6000.00