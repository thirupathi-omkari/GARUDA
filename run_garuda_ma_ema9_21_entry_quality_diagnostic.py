"""
GARUDA — STRATEGY #2 EMA 9/21 ENTRY-QUALITY DIAGNOSTIC

Purpose
-------
Analyze the already-frozen EMA 9/21 crossover entry universe WITHOUT changing it.

The diagnostic measures only information available at/before the signal candle:
    1. EMA separation
    2. EMA separation normalized by ATR
    3. EMA21 slope
    4. EMA21 slope normalized by ATR
    5. Price-to-EMA21 distance normalized by ATR
    6. Price-to-EMA9 distance normalized by ATR
    7. crossover magnitude / separation change
    8. entry time-of-day
    9. direction

It does NOT apply:
    - SL
    - target
    - break-even
    - trailing
    - P&L
    - future-candle filtering

The frozen entry universe therefore remains the sole input for later
filter research.

Outputs:
    data/research/garuda_ma_ema9_21_entry_quality_detail.csv
    data/research/garuda_ma_ema9_21_entry_quality_summary.csv
    data/research/garuda_ma_ema9_21_entry_quality_by_symbol.csv
    data/research/garuda_ma_ema9_21_entry_quality_by_time.csv
    data/research/garuda_ma_ema9_21_entry_quality_thresholds.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA_DIR = ROOT / "data" / "raw"
RESEARCH_DIR = ROOT / "data" / "research"
FROZEN = RESEARCH_DIR / "garuda_ma_ema9_21_frozen_entries.csv"

SYMBOL_FILES = {
    "INFY": "INFY_5MIN_REAL.csv",
    "RELIANCE": "RELIANCE_5MIN_REAL.csv",
    "ICICIBANK": "ICICIBANK_5MIN_REAL.csv",
    "TMPV": "TMPV_5MIN_REAL.csv",
    "ASHOKLEY": "ASHOKLEY_5MIN_REAL.csv",
    "OLAELEC": "OLAELEC_5MIN_REAL.csv",
    "SUZLON": "SUZLON_5MIN_REAL.csv",
}

ATR_PERIOD = 14


def load_price(symbol: str) -> pd.DataFrame:
    path = DATA_DIR / SYMBOL_FILES[symbol]
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "timestamp" in df.columns and "datetime" not in df.columns:
        df["datetime"] = df["timestamp"]
    if "time" in df.columns and "datetime" not in df.columns:
        df["datetime"] = df["time"]

    required = ["datetime", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"{path} missing columns: {missing}")

    df["datetime"] = (
        pd.to_datetime(df["datetime"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
    )

    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = (
        df.dropna(subset=required)
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    # Indicators are calculated on the complete historical stream so the
    # EMA/ATR at a signal candle has its proper warm-up context.
    df["ema9"] = df["close"].ewm(span=9, adjust=False, min_periods=9).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False, min_periods=21).mean()

    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr14"] = tr.rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean()

    # All of these are signal-candle features.
    df["ema_spread"] = df["ema9"] - df["ema21"]
    df["ema_spread_abs"] = df["ema_spread"].abs()
    df["ema_spread_atr"] = df["ema_spread_abs"] / df["atr14"]

    df["ema21_slope"] = df["ema21"] - df["ema21"].shift(1)
    df["ema21_slope_atr"] = df["ema21_slope"] / df["atr14"]
    df["ema21_slope_abs_atr"] = df["ema21_slope"].abs() / df["atr14"]

    df["ema_spread_change"] = df["ema_spread"] - df["ema_spread"].shift(1)
    df["ema_spread_change_atr"] = df["ema_spread_change"] / df["atr14"]
    df["ema_spread_change_abs_atr"] = (
        df["ema_spread_change"].abs() / df["atr14"]
    )

    df["close_ema21_distance"] = df["close"] - df["ema21"]
    df["close_ema21_distance_abs"] = df["close_ema21_distance"].abs()
    df["close_ema21_distance_atr"] = (
        df["close_ema21_distance_abs"] / df["atr14"]
    )

    df["close_ema9_distance"] = df["close"] - df["ema9"]
    df["close_ema9_distance_abs"] = df["close_ema9_distance"].abs()
    df["close_ema9_distance_atr"] = (
        df["close_ema9_distance_abs"] / df["atr14"]
    )

    return df


def quantile_table(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"q1": np.nan, "q2": np.nan, "q3": np.nan}
    return {
        "q1": float(s.quantile(0.25)),
        "q2": float(s.quantile(0.50)),
        "q3": float(s.quantile(0.75)),
    }


def assign_quartile(series: pd.Series) -> pd.Series:
    # Rank first so duplicate values cannot make qcut fail.
    ranked = series.rank(method="first")
    return pd.qcut(
        ranked,
        4,
        labels=["Q1_LOW", "Q2", "Q3", "Q4_HIGH"],
    )


def main() -> None:
    print("=" * 108)
    print("GARUDA — STRATEGY #2 EMA 9/21 ENTRY-QUALITY DIAGNOSTIC")
    print("=" * 108)
    print("Frozen universe : EMA 9/21 genuine crossovers")
    print("Stocks          : 7")
    print("Timeframe       : 5-minute")
    print("Features        : signal-candle information only")
    print("SL / target     : NOT APPLIED")
    print("BE / trailing   : NOT APPLIED")
    print("P&L              : NOT APPLIED")
    print("=" * 108)

    frozen = pd.read_csv(FROZEN)
    frozen.columns = [str(c).strip().lower() for c in frozen.columns]

    required = ["symbol", "direction", "signal_time", "entry_time"]
    missing = [c for c in required if c not in frozen.columns]
    if missing:
        raise RuntimeError(
            f"Frozen entry file missing columns: {missing}"
        )

    frozen["symbol"] = frozen["symbol"].astype(str).str.upper()
    frozen["direction"] = frozen["direction"].astype(str).str.upper()
    frozen["signal_time"] = (
        pd.to_datetime(frozen["signal_time"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
    )
    frozen["entry_time"] = (
        pd.to_datetime(frozen["entry_time"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
    )

    rows = []

    for symbol in SYMBOL_FILES:
        entries = frozen[frozen["symbol"] == symbol].copy()
        if entries.empty:
            continue

        price = load_price(symbol)
        dt_index = pd.DatetimeIndex(price["datetime"])

        print(f"\n{'-' * 100}")
        print(f"{symbol}: {len(entries)} frozen entries")

        for _, e in entries.sort_values("signal_time").iterrows():
            sig_pos = dt_index.searchsorted(e["signal_time"])
            ent_pos = dt_index.searchsorted(e["entry_time"])

            if sig_pos >= len(price) or ent_pos >= len(price):
                raise RuntimeError(
                    f"{symbol}: frozen entry time not found in price data: "
                    f"{e['signal_time']} / {e['entry_time']}"
                )

            sig = price.iloc[sig_pos]
            ent = price.iloc[ent_pos]

            if sig["datetime"] != e["signal_time"]:
                raise RuntimeError(
                    f"{symbol}: signal timestamp mismatch: "
                    f"frozen={e['signal_time']} data={sig['datetime']}"
                )
            if ent["datetime"] != e["entry_time"]:
                raise RuntimeError(
                    f"{symbol}: entry timestamp mismatch: "
                    f"frozen={e['entry_time']} data={ent['datetime']}"
                )

            # Signal and entry must be same trading day.
            if sig["datetime"].date() != ent["datetime"].date():
                raise RuntimeError(
                    f"{symbol}: cross-session frozen entry: "
                    f"{sig['datetime']} -> {ent['datetime']}"
                )

            row = {
                "symbol": symbol,
                "trade_date": ent["datetime"].date(),
                "direction": e["direction"],
                "signal_time": sig["datetime"],
                "entry_time": ent["datetime"],
                "entry_minute": ent["datetime"].hour * 60 + ent["datetime"].minute,
                "entry_time_hhmm": ent["datetime"].strftime("%H:%M"),
                "signal_close": float(sig["close"]),
                "entry_open": float(ent["open"]),
                "ema9": float(sig["ema9"]) if pd.notna(sig["ema9"]) else np.nan,
                "ema21": float(sig["ema21"]) if pd.notna(sig["ema21"]) else np.nan,
                "atr14": float(sig["atr14"]) if pd.notna(sig["atr14"]) else np.nan,
                "ema_spread": float(sig["ema_spread"]) if pd.notna(sig["ema_spread"]) else np.nan,
                "ema_spread_abs": float(sig["ema_spread_abs"]) if pd.notna(sig["ema_spread_abs"]) else np.nan,
                "ema_spread_atr": float(sig["ema_spread_atr"]) if pd.notna(sig["ema_spread_atr"]) else np.nan,
                "ema21_slope": float(sig["ema21_slope"]) if pd.notna(sig["ema21_slope"]) else np.nan,
                "ema21_slope_atr": float(sig["ema21_slope_atr"]) if pd.notna(sig["ema21_slope_atr"]) else np.nan,
                "ema21_slope_abs_atr": float(sig["ema21_slope_abs_atr"]) if pd.notna(sig["ema21_slope_abs_atr"]) else np.nan,
                "ema_spread_change": float(sig["ema_spread_change"]) if pd.notna(sig["ema_spread_change"]) else np.nan,
                "ema_spread_change_atr": float(sig["ema_spread_change_atr"]) if pd.notna(sig["ema_spread_change_atr"]) else np.nan,
                "ema_spread_change_abs_atr": float(sig["ema_spread_change_abs_atr"]) if pd.notna(sig["ema_spread_change_abs_atr"]) else np.nan,
                "close_ema21_distance": float(sig["close_ema21_distance"]) if pd.notna(sig["close_ema21_distance"]) else np.nan,
                "close_ema21_distance_abs": float(sig["close_ema21_distance_abs"]) if pd.notna(sig["close_ema21_distance_abs"]) else np.nan,
                "close_ema21_distance_atr": float(sig["close_ema21_distance_atr"]) if pd.notna(sig["close_ema21_distance_atr"]) else np.nan,
                "close_ema9_distance": float(sig["close_ema9_distance"]) if pd.notna(sig["close_ema9_distance"]) else np.nan,
                "close_ema9_distance_abs": float(sig["close_ema9_distance_abs"]) if pd.notna(sig["close_ema9_distance_abs"]) else np.nan,
                "close_ema9_distance_atr": float(sig["close_ema9_distance_atr"]) if pd.notna(sig["close_ema9_distance_atr"]) else np.nan,
            }

            # Direction-aware versions make BUY/SELL comparisons intuitive.
            sign = 1.0 if e["direction"] == "BUY" else -1.0
            row["directional_ema21_slope_atr"] = row["ema21_slope_atr"] * sign
            row["directional_ema_spread_change_atr"] = row["ema_spread_change_atr"] * sign
            row["directional_close_ema21_distance_atr"] = row["close_ema21_distance_atr"] * sign

            rows.append(row)

    detail = pd.DataFrame(rows)
    if len(detail) != len(frozen):
        raise RuntimeError(
            f"Diagnostic row count {len(detail)} != frozen entries {len(frozen)}"
        )

    # Quartiles are calculated WITHIN SYMBOL to avoid high-price stocks
    # dominating absolute thresholds.
    metric_cols = [
        "ema_spread_atr",
        "ema21_slope_abs_atr",
        "ema_spread_change_abs_atr",
        "close_ema21_distance_atr",
        "close_ema9_distance_atr",
    ]

    for metric in metric_cols:
        detail[f"{metric}_quartile"] = (
            detail.groupby("symbol", group_keys=False)[metric]
            .transform(assign_quartile)
        )

    threshold_rows = []
    for symbol, g in detail.groupby("symbol"):
        for metric in metric_cols:
            q = quantile_table(g[metric])
            threshold_rows.append(
                {
                    "symbol": symbol,
                    "metric": metric,
                    **q,
                }
            )

    thresholds = pd.DataFrame(threshold_rows)

    # Direction/time summary — still purely descriptive.
    by_symbol = (
        detail.groupby(["symbol", "direction"])
        .agg(
            entries=("symbol", "size"),
            median_ema_spread_atr=("ema_spread_atr", "median"),
            median_ema21_slope_abs_atr=("ema21_slope_abs_atr", "median"),
            median_ema_spread_change_abs_atr=("ema_spread_change_abs_atr", "median"),
            median_close_ema21_distance_atr=("close_ema21_distance_atr", "median"),
            median_close_ema9_distance_atr=("close_ema9_distance_atr", "median"),
        )
        .reset_index()
    )

    by_time = (
        detail.groupby(["entry_time_hhmm", "direction"])
        .agg(
            entries=("symbol", "size"),
            symbols=("symbol", "nunique"),
            median_ema_spread_atr=("ema_spread_atr", "median"),
            median_ema21_slope_abs_atr=("ema21_slope_abs_atr", "median"),
            median_ema_spread_change_abs_atr=("ema_spread_change_abs_atr", "median"),
            median_close_ema21_distance_atr=("close_ema21_distance_atr", "median"),
        )
        .reset_index()
        .sort_values(["entry_time_hhmm", "direction"])
    )

    # Aggregate descriptive quartile tables.
    summary_rows = []

    specs = [
        ("EMA_SPREAD", "ema_spread_atr", False),
        ("EMA21_SLOPE", "ema21_slope_abs_atr", False),
        ("CROSSOVER_STRENGTH", "ema_spread_change_abs_atr", False),
        ("PRICE_TO_EMA21", "close_ema21_distance_atr", False),
        ("PRICE_TO_EMA9", "close_ema9_distance_atr", False),
        ("DIRECTIONAL_EMA21_SLOPE", "directional_ema21_slope_atr", True),
        ("DIRECTIONAL_CROSSOVER_CHANGE", "directional_ema_spread_change_atr", True),
    ]

    for label, metric, signed in specs:
        for direction in ["ALL", "BUY", "SELL"]:
            g = detail if direction == "ALL" else detail[detail["direction"] == direction]
            q = quantile_table(g[metric])
            summary_rows.append(
                {
                    "metric": label,
                    "column": metric,
                    "direction": direction,
                    "entries": len(g),
                    "mean": float(g[metric].mean()),
                    "median": float(g[metric].median()),
                    "p25": q["q1"],
                    "p75": q["q3"],
                    "p90": float(g[metric].quantile(0.90)),
                    "p95": float(g[metric].quantile(0.95)),
                }
            )

    summary = pd.DataFrame(summary_rows)

    detail_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_quality_detail.csv"
    summary_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_quality_summary.csv"
    symbol_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_quality_by_symbol.csv"
    time_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_quality_by_time.csv"
    threshold_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_quality_thresholds.csv"

    detail.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)
    by_symbol.to_csv(symbol_path, index=False)
    by_time.to_csv(time_path, index=False)
    thresholds.to_csv(threshold_path, index=False)

    print("\n" + "=" * 108)
    print("7-STOCK ENTRY QUALITY OVERVIEW")
    print("=" * 108)
    print(
        detail.groupby(["symbol", "direction"])
        .size()
        .unstack(fill_value=0)
        .assign(TOTAL=lambda x: x.sum(axis=1))
        .to_string()
    )

    print("\n" + "=" * 108)
    print("KEY AGGREGATE DISTRIBUTIONS")
    print("=" * 108)
    print(summary[summary["direction"] == "ALL"].to_string(index=False))

    print("\n" + "=" * 108)
    print("WITHIN-SYMBOL QUARTILE THRESHOLDS")
    print("=" * 108)
    print(thresholds.to_string(index=False))

    print("\n" + "=" * 108)
    print("OUTPUT FILES")
    print("=" * 108)
    print("Detail     :", detail_path)
    print("Summary    :", summary_path)
    print("By symbol  :", symbol_path)
    print("By time    :", time_path)
    print("Thresholds :", threshold_path)
    print("\nVALIDATION: No future candles, SL, target, BE, trailing, or P&L logic were used.")
    print("This diagnostic does NOT alter the 5,389-entry frozen EMA 9/21 universe.")
    print("=" * 108)


if __name__ == "__main__":
    main()
