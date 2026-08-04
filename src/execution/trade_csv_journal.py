import csv
from pathlib import Path
from datetime import datetime


class TradeCSVJournal:

    FIELDNAMES = [
        "timestamp",
        "symbol",
        "side",
        "quantity",
        "entry_price",
        "exit_price",
        "stop_loss",
        "target",
        "holding_time",
        "exit_reason",
        "realized_pnl",
    ]

    def __init__(
        self,
        file_path="data/logs/trade_history.csv",
    ):

        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def record_trade(
        self,
        *,
        symbol,
        side,
        quantity,
        entry_price,
        exit_price,
        stop_loss,
        target,
        holding_time,
        exit_reason,
        realized_pnl,
    ):

        write_header = (
            not self.file_path.exists()
            or self.file_path.stat().st_size == 0
        )

        with self.file_path.open(
            "a",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.FIELDNAMES,
            )

            if write_header:
                writer.writeheader()

            writer.writerow(
                {
                    "timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "stop_loss": stop_loss,
                    "target": target,
                    "holding_time": str(holding_time).split(".")[0],
                    "exit_reason": exit_reason,
                    "realized_pnl": realized_pnl,
                }
            )