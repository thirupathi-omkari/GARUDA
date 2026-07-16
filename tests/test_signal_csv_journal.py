import csv
from datetime import datetime

import pytest

from execution.signal_csv_journal import SignalCSVJournal


def test_signal_csv_journal_creates_file_and_header(
    tmp_path,
):
    file_path = tmp_path / "signals.csv"

    journal = SignalCSVJournal(
        file_path=file_path
    )

    journal.record_signal(
        symbol="INFY",
        signal="BUY",
        entry_price=1500.0,
        stop_loss=1480.0,
        target_price=1540.0,
        timestamp=datetime(
            2026,
            7,
            15,
            10,
            25,
            0,
        ),
    )

    assert file_path.exists()

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(
            csv.DictReader(csv_file)
        )

    assert len(rows) == 1

    assert rows[0]["timestamp"] == (
        "2026-07-15T10:25:00"
    )

    assert rows[0]["symbol"] == "INFY"

    assert rows[0]["signal"] == "BUY"

    assert rows[0]["entry_price"] == "1500.0"

    assert rows[0]["stop_loss"] == "1480.0"

    assert rows[0]["target_price"] == "1540.0"

    assert rows[0]["risk_status"] == (
        "NOT_EVALUATED"
    )

    assert rows[0]["trade_status"] == (
        "NOT_EXECUTED"
    )


def test_signal_csv_journal_appends_signals(
    tmp_path,
):
    file_path = tmp_path / "signals.csv"

    journal = SignalCSVJournal(
        file_path=file_path
    )

    journal.record_signal(
        symbol="INFY",
        signal="BUY",
        entry_price=1500.0,
        stop_loss=1480.0,
        target_price=1540.0,
    )

    journal.record_signal(
        symbol="TCS",
        signal="SELL",
        entry_price=3200.0,
        stop_loss=3240.0,
        target_price=3120.0,
    )

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(
            csv.DictReader(csv_file)
        )

    assert len(rows) == 2

    assert rows[0]["symbol"] == "INFY"

    assert rows[1]["symbol"] == "TCS"

    assert rows[1]["signal"] == "SELL"


def test_signal_csv_journal_normalizes_values(
    tmp_path,
):
    journal = SignalCSVJournal(
        file_path=tmp_path / "signals.csv"
    )

    record = journal.record_signal(
        symbol=" infy ",
        signal=" buy ",
        entry_price=1500,
        stop_loss=1480,
        target_price=1540,
        risk_status=" approved ",
        trade_status=" paper_executed ",
    )

    assert record["symbol"] == "INFY"

    assert record["signal"] == "BUY"

    assert record["risk_status"] == "APPROVED"

    assert record["trade_status"] == (
        "PAPER_EXECUTED"
    )


@pytest.mark.parametrize(
    "signal",
    [
        "",
        "HOLD",
        "NO_SIGNAL",
        "WAIT",
    ],
)
def test_signal_csv_journal_rejects_non_trade_signals(
    tmp_path,
    signal,
):
    journal = SignalCSVJournal(
        file_path=tmp_path / "signals.csv"
    )

    with pytest.raises(
        ValueError,
        match="signal must be BUY or SELL",
    ):
        journal.record_signal(
            symbol="INFY",
            signal=signal,
            entry_price=1500.0,
            stop_loss=1480.0,
            target_price=1540.0,
        )


def test_signal_csv_journal_rejects_empty_symbol(
    tmp_path,
):
    journal = SignalCSVJournal(
        file_path=tmp_path / "signals.csv"
    )

    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        journal.record_signal(
            symbol=" ",
            signal="BUY",
            entry_price=1500.0,
            stop_loss=1480.0,
            target_price=1540.0,
        )


def test_signal_csv_journal_creates_parent_directories(
    tmp_path,
):
    file_path = (
        tmp_path
        / "nested"
        / "logs"
        / "signals.csv"
    )

    journal = SignalCSVJournal(
        file_path=file_path
    )

    journal.record_signal(
        symbol="RELIANCE",
        signal="BUY",
        entry_price=3000.0,
        stop_loss=2950.0,
        target_price=3100.0,
    )

    assert file_path.exists()


def test_signal_csv_journal_returns_written_record(
    tmp_path,
):
    journal = SignalCSVJournal(
        file_path=tmp_path / "signals.csv"
    )

    record = journal.record_signal(
        symbol="HDFCBANK",
        signal="SELL",
        entry_price=2000.0,
        stop_loss=2020.0,
        target_price=1960.0,
        risk_status="REJECTED",
        trade_status="NOT_EXECUTED",
        timestamp=datetime(
            2026,
            7,
            15,
            11,
            30,
            0,
        ),
    )

    assert record == {
        "timestamp": "2026-07-15T11:30:00",
        "symbol": "HDFCBANK",
        "signal": "SELL",
        "entry_price": 2000.0,
        "stop_loss": 2020.0,
        "target_price": 1960.0,
        "risk_status": "REJECTED",
        "trade_status": "NOT_EXECUTED",
    }
