
"""
GARUDA — STRATEGY #2 EMA 9/21 ENTRY-QUALITY FILTER STUDY

Purpose
-------
Run a controlled, frozen-universe filter study on the already-built
EMA 9/21 genuine-crossover entry universe.

The frozen universe is NOT regenerated and no future information is used
to define the filters.

Filters tested:
    NO_FILTER
    Q1_LOW / Q1_Q2 / EXCLUDE_Q4 for:
        EMA_SPREAD
        EMA21_SLOPE
        CROSSOVER_STRENGTH
        PRICE_TO_EMA21
        PRICE_TO_EMA9

For the first three "strength" features, low/high are tested in both
directions. For price-distance features, low/high are also both tested.

Each filter is then evaluated through the same MA SL × R framework:
    SL:
        SIGNAL_CANDLE
        SWING_5
        ATR_14_X1
        ATR_14_X1_5
        ATR_14_X2
    TARGET:
        1.00R .. 3.00R in 0.25R steps

Execution assumptions:
    entry slippage = 0.05%
    round-trip cost = 0.10%
    same-candle SL/target ambiguity = STOP_LOSS (conservative)

IMPORTANT:
    Filter thresholds are calculated WITHIN SYMBOL from the frozen
    entry-quality detail, so absolute price levels do not dominate.

This is an exploratory filter study. It does not select a production
filter automatically.
"""

from __future__ import annotations

import math
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

QUALITY_FILE = RESEARCH_DIR / "garuda_ma_ema9_21_entry_quality_detail.csv"
FROZEN_FILE = RESEARCH_DIR / "garuda_ma_ema9_21_frozen_entries.csv"

SLIPPAGE_PCT = 0.05
COST_RATE_PCT = 0.10
ATR_PERIOD = 14
SWING_LOOKBACK = 5

SL_MODES = (
    "SIGNAL_CANDLE",
    "SWING_5",
    "ATR_14_X1",
    "ATR_14_X1_5",
    "ATR_14_X2",
)
TARGET_RS = [round(x, 2) for x in np.arange(1.0, 3.001, 0.25)]

SYMBOL_FILES = {
    "INFY": "INFY_5MIN_REAL.csv",
    "RELIANCE": "RELIANCE_5MIN_REAL.csv",
    "ICICIBANK": "ICICIBANK_5MIN_REAL.csv",
    "TMPV": "TMPV_5MIN_REAL.csv",
    "ASHOKLEY": "ASHOKLEY_5MIN_REAL.csv",
    "OLAELEC": "OLAELEC_5MIN_REAL.csv",
    "SUZLON": "SUZLON_5MIN_REAL.csv",
}

FEATURES = {
    "EMA_SPREAD": "ema_spread_atr",
    "EMA21_SLOPE": "ema21_slope_abs_atr",
    "CROSSOVER_STRENGTH": "ema_spread_change_abs_atr",
    "PRICE_TO_EMA21": "close_ema21_distance_atr",
    "PRICE_TO_EMA9": "close_ema9_distance_atr",
}


def load_price(symbol):
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
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Asia/Kolkata")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=required).sort_values("datetime").reset_index(drop=True)

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
    return df


def add_filter_columns(detail):
    d = detail.copy()
    for feature, col in FEATURES.items():
        # Thresholds are within-symbol, derived only from the frozen entries.
        d[f"{feature}_q"] = (
            d.groupby("symbol")[col]
            .transform(lambda s: pd.qcut(
                s.rank(method="first"), 4,
                labels=["Q1_LOW", "Q2", "Q3", "Q4_HIGH"]
            ))
        )
    return d


def make_filter_specs():
    specs = [("NO_FILTER", None, None)]
    for feature, col in FEATURES.items():
        specs.extend([
            (f"{feature}_Q1_LOW", feature, "Q1_LOW"),
            (f"{feature}_Q1_Q2", feature, ("Q1_LOW", "Q2")),
            (f"{feature}_Q4_HIGH", feature, "Q4_HIGH"),
            (f"{feature}_Q3_Q4", feature, ("Q3", "Q4_HIGH")),
        ])
    return specs


def apply_filter(detail, feature, rule):
    if feature is None:
        return detail.copy()
    qcol = f"{feature}_q"
    if isinstance(rule, tuple):
        return detail[detail[qcol].isin(rule)].copy()
    return detail[detail[qcol] == rule].copy()


def entry_price(raw, direction):
    if direction == "BUY":
        return raw * (1 + SLIPPAGE_PCT / 100)
    return raw * (1 - SLIPPAGE_PCT / 100)


def stop_for_mode(mode, direction, signal_row, prior_history, entry):
    if mode == "SIGNAL_CANDLE":
        return float(signal_row["low"] if direction == "BUY" else signal_row["high"])

    if mode == "SWING_5":
        h = prior_history.tail(SWING_LOOKBACK)
        if len(h) < SWING_LOOKBACK:
            return math.nan
        return float(h["low"].min() if direction == "BUY" else h["high"].max())

    atr = float(signal_row["atr14"])
    if not np.isfinite(atr) or atr <= 0:
        return math.nan

    mult = {
        "ATR_14_X1": 1.0,
        "ATR_14_X1_5": 1.5,
        "ATR_14_X2": 2.0,
    }[mode]

    if direction == "BUY":
        return entry - mult * atr
    return entry + mult * atr


def simulate_trade(direction, entry, stop, future, target_r):
    risk = abs(entry - stop)
    if not np.isfinite(risk) or risk <= 0:
        return None

    target = entry + target_r * risk if direction == "BUY" else entry - target_r * risk
    mfe_r = 0.0
    mae_r = 0.0
    ambiguous = False

    if len(future) == 0:
        return ("END_OF_DAY", entry, mfe_r, mae_r, ambiguous)

    exit_price = float(future.iloc[-1]["close"])
    reason = "END_OF_DAY"

    for _, c in future.iterrows():
        high = float(c["high"])
        low = float(c["low"])

        if direction == "BUY":
            mfe_r = max(mfe_r, (high - entry) / risk)
            mae_r = max(mae_r, (entry - low) / risk)
            sl = low <= stop
            tp = high >= target
        else:
            mfe_r = max(mfe_r, (entry - low) / risk)
            mae_r = max(mae_r, (high - entry) / risk)
            sl = high >= stop
            tp = low <= target

        if sl and tp:
            ambiguous = True
            return ("STOP_LOSS", stop, mfe_r, mae_r, ambiguous)
        if sl:
            return ("STOP_LOSS", stop, mfe_r, mae_r, ambiguous)
        if tp:
            return ("TARGET", target, mfe_r, mae_r, ambiguous)

    return (reason, exit_price, mfe_r, mae_r, ambiguous)


def net_r(direction, entry, exit_price, risk):
    gross = (exit_price - entry) / risk if direction == "BUY" else (entry - exit_price) / risk
    # Approximate the same research convention: cost is based on notional
    # round-trip percentage converted to R using the actual entry risk.
    notional_cost = (entry * (COST_RATE_PCT / 100.0)) / risk
    return gross - notional_cost


def main():
    print("=" * 110)
    print("GARUDA — STRATEGY #2 EMA 9/21 ENTRY-QUALITY FILTER × SL × R STUDY")
    print("=" * 110)
    print("Frozen universe : EMA 9/21 genuine crossovers")
    print("Filters         : predefined within-symbol quartile filters")
    print("SL modes        :", ", ".join(SL_MODES))
    print("Targets         : 1.00R to 3.00R in 0.25R steps")
    print("BE / trailing   : OFF")
    print("Entry slippage  :", f"{SLIPPAGE_PCT:.2f}%")
    print("Cost rate       :", f"{COST_RATE_PCT:.2f}%")
    print("=" * 110)

    if not QUALITY_FILE.exists():
        raise RuntimeError(f"Missing quality detail file: {QUALITY_FILE}")
    if not FROZEN_FILE.exists():
        raise RuntimeError(f"Missing frozen entry file: {FROZEN_FILE}")

    detail = pd.read_csv(QUALITY_FILE)
    frozen = pd.read_csv(FROZEN_FILE)

    detail.columns = [str(c).strip().lower() for c in detail.columns]
    frozen.columns = [str(c).strip().lower() for c in frozen.columns]

    required_detail = ["symbol", "direction", "signal_time", "entry_time"] + list(FEATURES.values())
    missing = [c for c in required_detail if c not in detail.columns]
    if missing:
        raise RuntimeError(f"Quality detail missing columns: {missing}")

    required_frozen = ["symbol", "direction", "signal_time", "entry_time"]
    missing = [c for c in required_frozen if c not in frozen.columns]
    if missing:
        raise RuntimeError(f"Frozen file missing columns: {missing}")

    detail["symbol"] = detail["symbol"].astype(str).str.upper()
    detail["direction"] = detail["direction"].astype(str).str.upper()
    frozen["symbol"] = frozen["symbol"].astype(str).str.upper()
    frozen["direction"] = frozen["direction"].astype(str).str.upper()

    detail["signal_time"] = pd.to_datetime(detail["signal_time"], utc=True).dt.tz_convert("Asia/Kolkata")
    detail["entry_time"] = pd.to_datetime(detail["entry_time"], utc=True).dt.tz_convert("Asia/Kolkata")
    frozen["signal_time"] = pd.to_datetime(frozen["signal_time"], utc=True).dt.tz_convert("Asia/Kolkata")
    frozen["entry_time"] = pd.to_datetime(frozen["entry_time"], utc=True).dt.tz_convert("Asia/Kolkata")

    # Join identity is signal + entry time + symbol + direction.
    key = ["symbol", "direction", "signal_time", "entry_time"]
    if len(detail) != len(frozen):
        raise RuntimeError(f"Quality rows {len(detail)} != frozen rows {len(frozen)}")

    detail = add_filter_columns(detail)

    prices = {s: load_price(s) for s in SYMBOL_FILES}

    # Cache each frozen entry's signal/entry/future context once.
    contexts = {}
    for symbol, g in frozen.groupby("symbol"):
        price = prices[symbol]
        idx = pd.DatetimeIndex(price["datetime"])
        for _, e in g.iterrows():
            sig_pos = idx.searchsorted(e["signal_time"])
            ent_pos = idx.searchsorted(e["entry_time"])
            if sig_pos >= len(price) or ent_pos >= len(price):
                raise RuntimeError(f"{symbol}: entry time not found: {e['entry_time']}")
            if ent_pos <= sig_pos:
                raise RuntimeError(f"{symbol}: entry is not after signal: {e['signal_time']} -> {e['entry_time']}")

            signal_row = price.iloc[sig_pos]
            entry_row = price.iloc[ent_pos]
            prior = price.iloc[:sig_pos]
            future = price.iloc[ent_pos:].copy()

            contexts[(symbol, e["direction"], e["signal_time"], e["entry_time"])] = (
                signal_row, entry_row, prior, future
            )

    filter_specs = make_filter_specs()
    detail_by_key = {
        (r["symbol"], r["direction"], r["signal_time"], r["entry_time"]): r
        for _, r in detail.iterrows()
    }

    rows = []
    for i, (filter_name, feature, rule) in enumerate(filter_specs, 1):
        selected = apply_filter(detail, feature, rule)
        selected_keys = [
            (r["symbol"], r["direction"], r["signal_time"], r["entry_time"])
            for _, r in selected.iterrows()
        ]

        print(f"\n[{i:02d}/{len(filter_specs):02d}] {filter_name}: {len(selected_keys)} entries")

        for sl_mode in SL_MODES:
            for target_r in TARGET_RS:
                stop_count = target_count = eod_count = ambiguous_count = invalid_count = 0
                total_net_r = 0.0
                sum_mfe = 0.0
                sum_mae = 0.0
                trades = 0
                wins = 0
                gross_profit_r = 0.0
                gross_loss_r = 0.0
                equity = 0.0
                peak = 0.0
                max_dd = 0.0

                for k in selected_keys:
                    symbol, direction, signal_time, entry_time = k
                    signal_row, raw_entry_row, prior, future = contexts[k]
                    raw_entry = float(raw_entry_row["open"])
                    entry = entry_price(raw_entry, direction)
                    stop = stop_for_mode(sl_mode, direction, signal_row, prior, entry)

                    if not np.isfinite(stop):
                        invalid_count += 1
                        continue

                    risk = abs(entry - stop)
                    if risk <= 0:
                        invalid_count += 1
                        continue

                    result = simulate_trade(direction, entry, stop, future, target_r)
                    if result is None:
                        invalid_count += 1
                        continue

                    reason, exit_price, mfe_r, mae_r, ambiguous = result
                    nr = net_r(direction, entry, exit_price, risk)

                    trades += 1
                    total_net_r += nr
                    sum_mfe += mfe_r
                    sum_mae += mae_r
                    if nr > 0:
                        wins += 1
                        gross_profit_r += nr
                    elif nr < 0:
                        gross_loss_r += -nr

                    if reason == "STOP_LOSS":
                        stop_count += 1
                    elif reason == "TARGET":
                        target_count += 1
                    else:
                        eod_count += 1
                    if ambiguous:
                        ambiguous_count += 1

                    equity += nr
                    peak = max(peak, equity)
                    max_dd = max(max_dd, peak - equity)

                pf = gross_profit_r / gross_loss_r if gross_loss_r > 0 else np.nan
                rows.append({
                    "filter": filter_name,
                    "feature": feature or "",
                    "rule": str(rule) if rule is not None else "",
                    "selected_entries": len(selected_keys),
                    "sl_mode": sl_mode,
                    "target_r": target_r,
                    "trades": trades,
                    "invalid_risk_entries": invalid_count,
                    "stop_loss": stop_count,
                    "target": target_count,
                    "end_of_day": eod_count,
                    "ambiguous_candles": ambiguous_count,
                    "win_rate_pct": 100.0 * wins / trades if trades else np.nan,
                    "total_net_r": total_net_r,
                    "avg_net_r": total_net_r / trades if trades else np.nan,
                    "profit_factor": pf,
                    "max_drawdown_r": max_dd,
                    "avg_mfe_r": sum_mfe / trades if trades else np.nan,
                    "avg_mae_r": sum_mae / trades if trades else np.nan,
                })

    results = pd.DataFrame(rows)

    # Symbol-level summary at every filter/SL/R cell.
    symbol_rows = []
    for filter_name, feature, rule in filter_specs:
        selected = apply_filter(detail, feature, rule)
        selected_keys = [
            (r["symbol"], r["direction"], r["signal_time"], r["entry_time"])
            for _, r in selected.iterrows()
        ]
        for sl_mode in SL_MODES:
            for target_r in TARGET_RS:
                for symbol in SYMBOL_FILES:
                    keys = [k for k in selected_keys if k[0] == symbol]
                    if not keys:
                        continue
                    equity = peak = max_dd = total = gp = gl = 0.0
                    wins = trades = stops = targets = eods = ambiguous = invalid = 0
                    for k in keys:
                        signal_row, raw_entry_row, prior, future = contexts[k]
                        direction = k[1]
                        entry = entry_price(float(raw_entry_row["open"]), direction)
                        stop = stop_for_mode(sl_mode, direction, signal_row, prior, entry)
                        if not np.isfinite(stop) or abs(entry - stop) <= 0:
                            invalid += 1
                            continue
                        result = simulate_trade(direction, entry, stop, future, target_r)
                        if result is None:
                            invalid += 1
                            continue
                        reason, exit_price, mfe_r, mae_r, amb = result
                        nr = net_r(direction, entry, exit_price, abs(entry-stop))
                        trades += 1
                        total += nr
                        gp += max(nr, 0)
                        gl += max(-nr, 0)
                        wins += int(nr > 0)
                        stops += int(reason == "STOP_LOSS")
                        targets += int(reason == "TARGET")
                        eods += int(reason == "END_OF_DAY")
                        ambiguous += int(amb)
                        equity += nr
                        peak = max(peak, equity)
                        max_dd = max(max_dd, peak-equity)
                    symbol_rows.append({
                        "filter": filter_name,
                        "symbol": symbol,
                        "sl_mode": sl_mode,
                        "target_r": target_r,
                        "trades": trades,
                        "invalid_risk_entries": invalid,
                        "stop_loss": stops,
                        "target": targets,
                        "end_of_day": eods,
                        "ambiguous_candles": ambiguous,
                        "win_rate_pct": 100*wins/trades if trades else np.nan,
                        "total_net_r": total,
                        "avg_net_r": total/trades if trades else np.nan,
                        "profit_factor": gp/gl if gl > 0 else np.nan,
                        "max_drawdown_r": max_dd,
                    })

    by_symbol = pd.DataFrame(symbol_rows)

    # Compact filter-level table at the best locked baseline cell:
    # SWING_5 + 2R is intentionally shown alongside the full matrix,
    # because it was the strongest family in the prior MA matrix.
    filter_2r = results[
        (results["sl_mode"] == "SWING_5") &
        (results["target_r"] == 2.0)
    ].sort_values(["profit_factor", "total_net_r"], ascending=False)

    detail_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_filter_sl_target_detail.csv"
    summary_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_filter_sl_target_summary.csv"
    symbol_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_filter_by_symbol.csv"
    filter2r_path = RESEARCH_DIR / "garuda_ma_ema9_21_entry_filter_2r_summary.csv"

    results.to_csv(detail_path, index=False)
    results.groupby(
        ["filter", "sl_mode", "target_r"], as_index=False
    ).first().to_csv(summary_path, index=False)
    by_symbol.to_csv(symbol_path, index=False)
    filter_2r.to_csv(filter2r_path, index=False)

    print("\n" + "=" * 110)
    print("TOP FILTER CELLS — SWING_5 + 2.00R")
    print("=" * 110)
    cols = [
        "filter", "selected_entries", "trades", "win_rate_pct",
        "total_net_r", "avg_net_r", "profit_factor",
        "max_drawdown_r", "stop_loss", "target", "end_of_day",
    ]
    print(filter_2r[cols].head(20).to_string(index=False))

    print("\n" + "=" * 110)
    print("OUTPUT FILES")
    print("=" * 110)
    print(f"Detail     : {detail_path}")
    print(f"Summary    : {summary_path}")
    print(f"By symbol  : {symbol_path}")
    print(f"2R summary : {filter2r_path}")
    print("=" * 110)
    print("VALIDATION: frozen EMA 9/21 entry universe reused; filters use signal-candle features only.")
    print("No filter is automatically promoted to production.")


if __name__ == "__main__":
    main()
