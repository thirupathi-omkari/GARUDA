"""
GARUDA — Strategy #2 MA 1-Year Frozen Entry Research

Purpose:
    Build a frozen entry universe for EMA fast/slow crossover research
    across the seven GARUDA research stocks.

Initial locked hypothesis:
    MA type       : EMA
    Fast period   : 9
    Slow period   : 21
    Timeframe     : 5-minute
    Signal        : genuine crossover event
    Entry         : next candle OPEN
    BUY + SELL    : both included
    SL / target   : NOT applied here
    BE / trailing : NOT applied here

Research discipline:
    - Indicators are calculated using candles available at the signal candle.
    - Historical data before the current session is used for EMA warm-up.
    - A signal is recorded only when the fast/slow relationship actually crosses.
    - Entry is the next candle of the same trading session.
    - The frozen entry universe is the same input for all later SL/target tests.
"""

from __future__ import annotations

from pathlib import Path
import math
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "raw"
RESEARCH_DIR = ROOT / "data" / "research"

SYMBOLS = [
    "INFY",
    "RELIANCE",
    "ICICIBANK",
    "TMPV",
    "ASHOKLEY",
    "OLAELEC",
    "SUZLON",
]

FAST_PERIOD = 9
SLOW_PERIOD = 21
MA_TYPE = "EMA"

OUTPUT_DETAIL = RESEARCH_DIR / "garuda_ma_ema9_21_frozen_entries.csv"
OUTPUT_SUMMARY = RESEARCH_DIR / "garuda_ma_ema9_21_entry_summary.csv"
OUTPUT_DAILY = RESEARCH_DIR / "garuda_ma_ema9_21_entry_by_date.csv"
OUTPUT_TIME = RESEARCH_DIR / "garuda_ma_ema9_21_entry_by_time.csv"


def log(message: str = "") -> None:
    print(message)


def find_data_file(symbol: str) -> Path:
    candidates = [
        DATA_DIR / f"{symbol}_5MIN_REAL.csv",
        DATA_DIR / f"{symbol}_5MIN.csv",
        DATA_DIR / f"{symbol}_5min_real.csv",
        DATA_DIR / f"{symbol}_5min.csv",
    ]
    for path in candidates:
        if path.exists() and path.stat().st_size > 0:
            return path
    raise FileNotFoundError(
        f"No usable 5-minute data found for {symbol} in {DATA_DIR}"
    )


def normalize_data(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    df = df.copy()

    rename_map = {}
    for col in df.columns:
        lower = str(col).strip().lower()
        if lower in {"datetime", "date", "timestamp", "time"}:
            rename_map[col] = "datetime"
        elif lower == "open":
            rename_map[col] = "open"
        elif lower == "high":
            rename_map[col] = "high"
        elif lower == "low":
            rename_map[col] = "low"
        elif lower == "close":
            rename_map[col] = "close"
        elif lower == "volume":
            rename_map[col] = "volume"

    df = df.rename(columns=rename_map)

    required = ["datetime", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"{symbol}: missing required columns {missing}")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    if getattr(df["datetime"].dt, "tz", None) is None:
        # Research files are expected to represent Indian market timestamps.
        df["datetime"] = df["datetime"].dt.tz_localize(
            "Asia/Kolkata", ambiguous="NaT", nonexistent="NaT"
        )
    else:
        df["datetime"] = df["datetime"].dt.tz_convert("Asia/Kolkata")

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = (
        df.dropna(subset=required)
        .sort_values("datetime")
        .drop_duplicates(subset=["datetime"], keep="last")
        .reset_index(drop=True)
    )

    df["trade_date"] = df["datetime"].dt.date
    df["symbol"] = symbol
    return df


def add_ema(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["fast_ema"] = (
        result["close"]
        .ewm(span=FAST_PERIOD, adjust=False, min_periods=FAST_PERIOD)
        .mean()
    )
    result["slow_ema"] = (
        result["close"]
        .ewm(span=SLOW_PERIOD, adjust=False, min_periods=SLOW_PERIOD)
        .mean()
    )
    result["ema_spread"] = result["fast_ema"] - result["slow_ema"]
    result["ema_spread_pct"] = (
        result["ema_spread"] / result["slow_ema"].abs()
    ) * 100.0
    return result


def build_frozen_entries(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Replay the complete series in chronological order.

    Previous-session candles are retained for EMA warm-up, but a crossover
    is only accepted when both the signal candle and next entry candle belong
    to the same trading session.
    """
    data = add_ema(df)

    rows = []

    for i in range(1, len(data) - 1):
        prev = data.iloc[i - 1]
        signal = data.iloc[i]
        entry = data.iloc[i + 1]

        if (
            pd.isna(prev["fast_ema"])
            or pd.isna(prev["slow_ema"])
            or pd.isna(signal["fast_ema"])
            or pd.isna(signal["slow_ema"])
        ):
            continue

        # Never carry a signal into the next trading day.
        if signal["trade_date"] != entry["trade_date"]:
            continue

        buy_cross = (
            prev["fast_ema"] <= prev["slow_ema"]
            and signal["fast_ema"] > signal["slow_ema"]
        )
        sell_cross = (
            prev["fast_ema"] >= prev["slow_ema"]
            and signal["fast_ema"] < signal["slow_ema"]
        )

        if not buy_cross and not sell_cross:
            continue

        direction = "BUY" if buy_cross else "SELL"

        # Entry occurs at the next candle's open.
        rows.append(
            {
                "symbol": symbol,
                "trade_date": signal["trade_date"],
                "direction": direction,
                "signal_time": signal["datetime"],
                "entry_time": entry["datetime"],
                "signal_close": float(signal["close"]),
                "entry_open_raw": float(entry["open"]),
                "signal_fast_ema": float(signal["fast_ema"]),
                "signal_slow_ema": float(signal["slow_ema"]),
                "signal_ema_spread": float(signal["ema_spread"]),
                "signal_ema_spread_pct": float(signal["ema_spread_pct"]),
                "previous_fast_ema": float(prev["fast_ema"]),
                "previous_slow_ema": float(prev["slow_ema"]),
                "entry_close": float(entry["close"]),
                "entry_high": float(entry["high"]),
                "entry_low": float(entry["low"]),
                "entry_price": float(entry["open"]),
                "entry_vs_slow_ema": float(
                    entry["open"] - signal["slow_ema"]
                ),
                "entry_vs_slow_ema_pct": float(
                    (entry["open"] - signal["slow_ema"])
                    / abs(signal["slow_ema"])
                    * 100.0
                ),
                "signal_minute": signal["datetime"].strftime("%H:%M"),
                "entry_minute": entry["datetime"].strftime("%H:%M"),
                "ma_type": MA_TYPE,
                "fast_period": FAST_PERIOD,
                "slow_period": SLOW_PERIOD,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 100)
    print("GARUDA — STRATEGY #2 MA 1-YEAR FROZEN ENTRY RESEARCH")
    print("=" * 100)
    print(f"MA TYPE         : {MA_TYPE}")
    print(f"FAST PERIOD     : {FAST_PERIOD}")
    print(f"SLOW PERIOD     : {SLOW_PERIOD}")
    print("TIMEFRAME       : 5-minute")
    print("SIGNAL          : genuine fast/slow crossover")
    print("ENTRY           : next candle OPEN")
    print("DIRECTIONS      : BUY + SELL")
    print("SL / TARGET     : NOT APPLIED")
    print("BE / TRAILING   : NOT APPLIED")
    print("=" * 100)

    all_entries = []
    symbol_summary = []

    for symbol in SYMBOLS:
        path = find_data_file(symbol)
        df = normalize_data(pd.read_csv(path), symbol)

        entries = build_frozen_entries(symbol, df)

        sessions = df["trade_date"].nunique()
        start = df["datetime"].min()
        end = df["datetime"].max()

        print()
        print("-" * 100)
        print(f"{symbol}")
        print(f"Data     : {path}")
        print(f"Rows     : {len(df)}")
        print(f"Sessions : {sessions}")
        print(f"From     : {start}")
        print(f"To       : {end}")
        print(f"Entries  : {len(entries)}")

        if not entries.empty:
            buy = int((entries["direction"] == "BUY").sum())
            sell = int((entries["direction"] == "SELL").sum())
            print(f"BUY      : {buy}")
            print(f"SELL     : {sell}")
            print(
                f"First    : {entries['signal_time'].min()}"
            )
            print(
                f"Last     : {entries['signal_time'].max()}"
            )

            all_entries.append(entries)

        symbol_summary.append(
            {
                "symbol": symbol,
                "rows": len(df),
                "sessions": sessions,
                "data_start": start,
                "data_end": end,
                "frozen_entries": len(entries),
                "buy_entries": (
                    int((entries["direction"] == "BUY").sum())
                    if not entries.empty else 0
                ),
                "sell_entries": (
                    int((entries["direction"] == "SELL").sum())
                    if not entries.empty else 0
                ),
            }
        )

    if not all_entries:
        raise RuntimeError("No MA crossover entries were generated.")

    detail = (
        pd.concat(all_entries, ignore_index=True)
        .sort_values(["trade_date", "symbol", "signal_time"])
        .reset_index(drop=True)
    )

    detail.insert(0, "frozen_entry_id", range(1, len(detail) + 1))

    summary = pd.DataFrame(symbol_summary)

    daily = (
        detail.groupby(["trade_date", "symbol"], as_index=False)
        .agg(
            entries=("frozen_entry_id", "count"),
            buys=("direction", lambda s: int((s == "BUY").sum())),
            sells=("direction", lambda s: int((s == "SELL").sum())),
        )
        .sort_values(["trade_date", "symbol"])
    )

    by_time = (
        detail.groupby(["symbol", "entry_minute"], as_index=False)
        .agg(
            entries=("frozen_entry_id", "count"),
            buys=("direction", lambda s: int((s == "BUY").sum())),
            sells=("direction", lambda s: int((s == "SELL").sum())),
        )
        .sort_values(["symbol", "entry_minute"])
    )

    detail.to_csv(OUTPUT_DETAIL, index=False)
    summary.to_csv(OUTPUT_SUMMARY, index=False)
    daily.to_csv(OUTPUT_DAILY, index=False)
    by_time.to_csv(OUTPUT_TIME, index=False)

    print()
    print("=" * 100)
    print("7-STOCK FROZEN ENTRY UNIVERSE")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(f"TOTAL FROZEN ENTRIES : {len(detail)}")
    print(f"TOTAL BUY           : {(detail['direction'] == 'BUY').sum()}")
    print(f"TOTAL SELL          : {(detail['direction'] == 'SELL').sum()}")
    print()
    print("=" * 100)
    print("OUTPUT FILES")
    print("=" * 100)
    print(f"Detail  : {OUTPUT_DETAIL}")
    print(f"Summary : {OUTPUT_SUMMARY}")
    print(f"Daily   : {OUTPUT_DAILY}")
    print(f"By time : {OUTPUT_TIME}")
    print()
    print("VALIDATION:")
    print("The files contain only genuine EMA 9/21 crossover entries.")
    print("No SL, target, break-even, trailing stop, or P&L logic was applied.")
    print("This frozen entry universe is the input for the next MA risk/target research.")
    print("=" * 100)


if __name__ == "__main__":
    main()
