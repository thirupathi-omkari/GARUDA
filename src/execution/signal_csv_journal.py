"""
GARUDA Quant Lab
Module 9 Part 13F-3C

Signal CSV Journal

Purpose
-------
Persist generated trading signals to CSV for later inspection.

The journal records only actual trading signals supplied to it.
It does not generate signals, perform risk checks, execute trades,
manage positions, or send broker orders.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class SignalCSVJournal:
    """Append GARUDA trading-signal records to a CSV file."""

    FIELDNAMES = (
        "timestamp",
        "symbol",
        "signal",
        "entry_price",
        "stop_loss",
        "target_price",
        "risk_status",
        "trade_status",
    )

    def __init__(
        self,
        file_path: str | Path = "data/logs/garuda_signals.csv",
    ) -> None:
        self.file_path = Path(file_path)

    def record_signal(
        self,
        *,
        symbol: str,
        signal: str,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        risk_status: str = "NOT_EVALUATED",
        trade_status: str = "NOT_EXECUTED",
        timestamp: Optional[datetime] = None,
    ) -> dict[str, Any]:
        normalized_signal = str(signal).strip().upper()

        if normalized_signal not in {"BUY", "SELL"}:
            raise ValueError(
                "signal must be BUY or SELL"
            )

        if not str(symbol).strip():
            raise ValueError(
                "symbol must not be empty"
            )

        event_time = timestamp or datetime.now()

        record = {
            "timestamp": event_time.isoformat(
                timespec="seconds"
            ),
            "symbol": str(symbol).strip().upper(),
            "signal": normalized_signal,
            "entry_price": float(entry_price),
            "stop_loss": float(stop_loss),
            "target_price": float(target_price),
            "risk_status": str(risk_status).strip().upper(),
            "trade_status": str(trade_status).strip().upper(),
        }

        self._ensure_parent_directory()

        write_header = (
            not self.file_path.exists()
            or self.file_path.stat().st_size == 0
        )

        with self.file_path.open(
            mode="a",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=self.FIELDNAMES,
            )

            if write_header:
                writer.writeheader()

            writer.writerow(record)

        return record

    def _ensure_parent_directory(self) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
