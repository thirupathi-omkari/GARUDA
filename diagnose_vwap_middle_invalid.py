import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from indicators.vwap import calculate_vwap

SYMBOL = "INFY"

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

ENTRY_FILE = (
    PROJECT_ROOT
    / "data"
    / "research"
    / "INFY_frozen_entries_1y.csv"
)

print()
print("=" * 110)
print("GARUDA — VWAP-MIDDLE INVALID-RISK DIAGNOSTIC")
print("=" * 110)

df = pd.read_csv(DATA_FILE)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)

entries = pd.read_csv(ENTRY_FILE)
entries["trade_date"] = pd.to_datetime(entries["trade_date"]).dt.date
entries["entry_candle_time"] = pd.to_datetime(entries["entry_candle_time"])
entries["signal_candle_time"] = pd.to_datetime(entries["signal_candle_time"])

invalid = []

for trade_date, group in df.groupby(df["datetime"].dt.date):

    session = (
        group
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    if session.empty:
        continue

    data = calculate_vwap(session)

    day_entries = entries[
        entries["trade_date"] == trade_date
    ]

    for _, row in day_entries.iterrows():

        matches = session[
            session["datetime"]
            == row["entry_candle_time"]
        ]

        if matches.empty:
            continue

        idx = int(matches.index[0])
        candle = session.iloc[idx]

        entry_price = float(row["entry_price"])
        entry_vwap = float(data.iloc[idx]["vwap"])
        direction = str(row["direction"]).upper()

        if direction == "BUY":
            risk = entry_price - entry_vwap
        else:
            risk = entry_vwap - entry_price

        if risk <= 0:
            invalid.append(
                {
                    "trade_date": trade_date,
                    "direction": direction,
                    "signal_time": row["signal_candle_time"],
                    "entry_time": row["entry_candle_time"],
                    "entry_open_raw": float(candle["open"]),
                    "entry_price_after_slippage": entry_price,
                    "entry_vwap": entry_vwap,
                    "risk": risk,
                    "entry_high": float(candle["high"]),
                    "entry_low": float(candle["low"]),
                    "entry_close": float(candle["close"]),
                    "signal_vwap": float(row["signal_vwap"]),
                }
            )

print()
print(f"Frozen entries checked : {len(entries)}")
print(f"Invalid VWAP risks     : {len(invalid)}")
print()

if invalid:
    result = pd.DataFrame(invalid)

    print(
        result.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}"
        )
    )

    output = (
        PROJECT_ROOT
        / "data"
        / "research"
        / "vwap_middle_invalid_diagnostic_infy.csv"
    )

    result.to_csv(
        output,
        index=False,
    )

    print()
    print(f"Diagnostic saved: {output}")

    print()
    print("INTERPRETATION:")
    print(
        "The ORB+VWAP signal can be valid on the signal candle "
        "while the next candle opens on the wrong side of VWAP."
    )
    print(
        "For such a trade, entry-candle VWAP is not a valid protective "
        "stop without adding an extra rule/buffer."
    )
    print(
        "This script does NOT alter or exclude the trade."
    )

else:
    print("No invalid VWAP-middle risk found.")

print("=" * 110)
