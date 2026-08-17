"""
GARUDA — STRATEGY #2 MA SL × R-TARGET MATRIX RESEARCH

Frozen entry universe:
    EMA 9 / EMA 21 genuine crossover
    5-minute
    next candle OPEN entry
    BUY + SELL

Research variables:
    SL:
        SIGNAL_CANDLE
        SWING_5
        ATR_14_X1
        ATR_14_X1_5
        ATR_14_X2

    TARGET:
        1.00R .. 3.00R in 0.25R steps

No BE, no trailing.
Each frozen entry is evaluated independently.
The entry universe itself is never changed.

Execution assumptions are aligned with the existing GARUDA research:
    entry slippage = 0.05%
    round-trip transaction cost = 0.10%
    same-candle SL/target ambiguity is reported and resolved
    conservatively in favor of STOP_LOSS.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"

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


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    aliases = {
        "timestamp": "datetime",
        "time": "datetime",
        "date": "datetime",
        "side": "direction",
        "signal": "direction",
    }
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]
    return df


def require(df, columns, label):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"{label} is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )


def load_price(symbol):
    path = DATA_DIR / SYMBOL_FILES[symbol]
    df = normalize_columns(pd.read_csv(path))
    require(df, ["datetime", "open", "high", "low", "close"], str(path))
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Asia/Kolkata")
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    return df.sort_values("datetime").reset_index(drop=True)


def add_atr(df):
    out = df.copy()
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            out["high"] - out["low"],
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    # Match GARUDA's simple rolling ATR style used by the research stack.
    out["atr_14"] = tr.rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean()
    return out


def entry_price_with_slippage(raw, direction):
    if direction == "BUY":
        return raw * (1.0 + SLIPPAGE_PCT / 100.0)
    return raw * (1.0 - SLIPPAGE_PCT / 100.0)


def stop_for_mode(mode, direction, signal_row, history, entry_price):
    if mode == "SIGNAL_CANDLE":
        return float(signal_row["low"] if direction == "BUY" else signal_row["high"])

    if mode == "SWING_5":
        # Stop is based only on candles strictly before the signal candle.
        h = history.tail(SWING_LOOKBACK)
        if len(h) < SWING_LOOKBACK:
            return math.nan
        return float(h["low"].min() if direction == "BUY" else h["high"].max())

    atr = float(signal_row["atr_14"]) if pd.notna(signal_row["atr_14"]) else math.nan
    if not np.isfinite(atr):
        return math.nan

    multiplier = {
        "ATR_14_X1": 1.0,
        "ATR_14_X1_5": 1.5,
        "ATR_14_X2": 2.0,
    }[mode]

    if direction == "BUY":
        return entry_price - multiplier * atr
    return entry_price + multiplier * atr


def simulate(entry_row, signal_row, future, stop, target_r):
    direction = entry_row["direction"]
    entry = float(entry_row["entry_price"])
    risk = abs(entry - stop)

    if not np.isfinite(risk) or risk <= 0:
        return None

    target = entry + target_r * risk if direction == "BUY" else entry - target_r * risk

    exit_reason = "END_OF_DAY"
    exit_price = float(future.iloc[-1]["close"]) if len(future) else entry

    mfe = 0.0
    mae = 0.0
    ambiguous = False

    for _, c in future.iterrows():
        high = float(c["high"])
        low = float(c["low"])

        if direction == "BUY":
            mfe = max(mfe, (high - entry) / risk)
            mae = max(mae, (entry - low) / risk)
            sl_hit = low <= stop
            target_hit = high >= target
            if sl_hit and target_hit:
                ambiguous = True
                exit_reason = "STOP_LOSS"
                exit_price = stop
                break
            if sl_hit:
                exit_reason = "STOP_LOSS"
                exit_price = stop
                break
            if target_hit:
                exit_reason = "TARGET"
                exit_price = target
                break
        else:
            mfe = max(mfe, (entry - low) / risk)
            mae = max(mae, (high - entry) / risk)
            sl_hit = high >= stop
            target_hit = low <= target
            if sl_hit and target_hit:
                ambiguous = True
                exit_reason = "STOP_LOSS"
                exit_price = stop
                break
            if sl_hit:
                exit_reason = "STOP_LOSS"
                exit_price = stop
                break
            if target_hit:
                exit_reason = "TARGET"
                exit_price = target
                break

    if exit_reason == "END_OF_DAY" and len(future):
        last = future.iloc[-1]
        exit_price = float(last["close"])

    # Apply adverse exit slippage.
    if direction == "BUY":
        slipped_exit = exit_price * (1.0 - SLIPPAGE_PCT / 100.0)
        gross = (slipped_exit - entry) / risk
    else:
        slipped_exit = exit_price * (1.0 + SLIPPAGE_PCT / 100.0)
        gross = (entry - slipped_exit) / risk

    # Cost is normalized to initial-risk R for comparability.
    notional_cost = (entry + abs(slipped_exit)) * (COST_RATE_PCT / 100.0)
    cost_r = notional_cost / risk
    net_r = gross - cost_r

    return {
        "exit_reason": exit_reason,
        "exit_price": slipped_exit,
        "mfe_r": mfe,
        "mae_r": mae,
        "gross_r": gross,
        "cost_r": cost_r,
        "net_r": net_r,
        "ambiguous": ambiguous,
        "risk": risk,
        "stop_loss": stop,
        "target": target,
    }


def max_drawdown(values):
    eq = np.cumsum(values)
    peak = np.maximum.accumulate(np.r_[0.0, eq])[1:]
    dd = peak - eq
    return float(dd.max()) if len(dd) else 0.0


def main():
    print("=" * 110)
    print("GARUDA — STRATEGY #2 MA SL × R-TARGET MATRIX RESEARCH")
    print("=" * 110)
    print("Frozen universe : EMA 9/21 genuine crossovers")
    print("Stocks          : 7")
    print("SL modes        :", ", ".join(SL_MODES))
    print("Targets         : 1.00R to 3.00R in 0.25R steps")
    print("BE / trailing   : OFF")
    print(f"Entry slippage  : {SLIPPAGE_PCT:.2f}%")
    print(f"Cost rate       : {COST_RATE_PCT:.2f}%")
    print("=" * 110)

    frozen = normalize_columns(pd.read_csv(FROZEN_FILE))
    require(
        frozen,
        ["symbol", "direction", "signal_time", "entry_time"],
        str(FROZEN_FILE),
    )

    frozen["signal_time"] = pd.to_datetime(frozen["signal_time"], utc=True).dt.tz_convert("Asia/Kolkata")
    frozen["entry_time"] = pd.to_datetime(frozen["entry_time"], utc=True).dt.tz_convert("Asia/Kolkata")
    frozen["direction"] = frozen["direction"].astype(str).str.upper()

    # Entry price is reconstructed from the actual next candle open to keep
    # the frozen universe independent of any risk calculation.
    all_detail = []

    for symbol in SYMBOL_FILES:
        entries = frozen[frozen["symbol"].astype(str).str.upper() == symbol].copy()
        if entries.empty:
            continue

        price = add_atr(load_price(symbol))
        price_index = pd.DatetimeIndex(price["datetime"])

        print(f"\n{'-' * 100}\n{symbol}: {len(entries)} frozen entries")

        for _, e in entries.sort_values("entry_time").iterrows():
            signal_time = e["signal_time"]
            entry_time = e["entry_time"]

            signal_pos = price_index.searchsorted(signal_time)
            entry_pos = price_index.searchsorted(entry_time)

            if signal_pos >= len(price) or entry_pos >= len(price):
                continue

            signal_row = price.iloc[signal_pos]
            entry_row_price = price.iloc[entry_pos]
            raw_entry = float(entry_row_price["open"])
            direction = e["direction"]
            entry_price = entry_price_with_slippage(raw_entry, direction)

            # Same-session signal/entry validation.
            if signal_row["datetime"].date() != entry_row_price["datetime"].date():
                continue

            session_mask = price["datetime"].dt.date == entry_row_price["datetime"].date()
            session = price.loc[session_mask].reset_index(drop=True)
            local_signal = session.index[session["datetime"] == signal_row["datetime"]]
            local_entry = session.index[session["datetime"] == entry_row_price["datetime"]]
            if len(local_signal) == 0 or len(local_entry) == 0:
                continue

            si = int(local_signal[0])
            ei = int(local_entry[0])
            future = session.iloc[ei:].copy()
            history = price.iloc[:signal_pos].copy()

            for sl_mode in SL_MODES:
                stop = stop_for_mode(
                    sl_mode, direction, signal_row, history, entry_price
                )
                for target_r in TARGET_RS:
                    sim = simulate(
                        entry_row={
                            "direction": direction,
                            "entry_price": entry_price,
                        },
                        signal_row=signal_row,
                        future=future,
                        stop=stop,
                        target_r=target_r,
                    )

                    row = {
                        "symbol": symbol,
                        "trade_date": entry_row_price["datetime"].date(),
                        "direction": direction,
                        "signal_time": signal_row["datetime"],
                        "entry_time": entry_row_price["datetime"],
                        "raw_entry_price": raw_entry,
                        "entry_price": entry_price,
                        "sl_mode": sl_mode,
                        "target_r": target_r,
                    }

                    if sim is None:
                        row.update({
                            "valid_risk": False,
                            "risk": np.nan,
                            "stop_loss": stop,
                            "target": np.nan,
                            "exit_reason": "INVALID_RISK",
                            "exit_price": np.nan,
                            "mfe_r": np.nan,
                            "mae_r": np.nan,
                            "gross_r": np.nan,
                            "cost_r": np.nan,
                            "net_r": np.nan,
                            "ambiguous": False,
                        })
                    else:
                        row.update({
                            "valid_risk": True,
                            **sim,
                        })

                    all_detail.append(row)

    detail = pd.DataFrame(all_detail)
    if detail.empty:
        raise RuntimeError("No MA SL/target research rows were generated.")

    detail_path = RESEARCH_DIR / "garuda_ma_ema9_21_sl_target_matrix_detail.csv"
    detail.to_csv(detail_path, index=False)

    valid = detail[detail["valid_risk"]].copy()

    summary_rows = []
    for (sl_mode, target_r), g in valid.groupby(["sl_mode", "target_r"], sort=True):
        net = g["net_r"].astype(float)
        wins = net > 0
        gross_profit = net[net > 0].sum()
        gross_loss = -net[net < 0].sum()
        pf = gross_profit / gross_loss if gross_loss > 0 else np.inf

        summary_rows.append({
            "sl_mode": sl_mode,
            "target_r": target_r,
            "frozen_entries": int(len(detail[(detail["sl_mode"] == sl_mode) & (detail["target_r"] == target_r)])),
            "valid_entries": int(len(g)),
            "invalid_risk_entries": int((~detail[(detail["sl_mode"] == sl_mode) & (detail["target_r"] == target_r)]["valid_risk"]).sum()),
            "trades": int(len(g)),
            "stop_loss": int((g["exit_reason"] == "STOP_LOSS").sum()),
            "target": int((g["exit_reason"] == "TARGET").sum()),
            "end_of_day": int((g["exit_reason"] == "END_OF_DAY").sum()),
            "ambiguous_candles": int(g["ambiguous"].sum()),
            "win_rate_pct": float(wins.mean() * 100),
            "total_net_r": float(net.sum()),
            "avg_net_r": float(net.mean()),
            "profit_factor": float(pf),
            "max_drawdown_r": max_drawdown(net.to_numpy()),
            "avg_mfe_r": float(g["mfe_r"].mean()),
            "p90_mfe_r": float(g["mfe_r"].quantile(0.90)),
            "avg_mae_r": float(g["mae_r"].mean()),
            "p90_mae_r": float(g["mae_r"].quantile(0.90)),
        })

    summary = pd.DataFrame(summary_rows)
    summary_path = RESEARCH_DIR / "garuda_ma_ema9_21_sl_target_matrix_summary.csv"
    summary.to_csv(summary_path, index=False)

    by_symbol_rows = []
    for (sl_mode, target_r, symbol), g in valid.groupby(["sl_mode", "target_r", "symbol"], sort=True):
        net = g["net_r"]
        gp = net[net > 0].sum()
        gl = -net[net < 0].sum()
        by_symbol_rows.append({
            "sl_mode": sl_mode,
            "target_r": target_r,
            "symbol": symbol,
            "trades": len(g),
            "total_net_r": float(net.sum()),
            "avg_net_r": float(net.mean()),
            "profit_factor": float(gp / gl) if gl > 0 else np.inf,
            "win_rate_pct": float((net > 0).mean() * 100),
            "stop_loss": int((g.exit_reason == "STOP_LOSS").sum()),
            "target": int((g.exit_reason == "TARGET").sum()),
            "end_of_day": int((g.exit_reason == "END_OF_DAY").sum()),
            "avg_mfe_r": float(g.mfe_r.mean()),
            "avg_mae_r": float(g.mae_r.mean()),
        })

    by_symbol = pd.DataFrame(by_symbol_rows)
    by_symbol_path = RESEARCH_DIR / "garuda_ma_ema9_21_sl_target_matrix_by_symbol.csv"
    by_symbol.to_csv(by_symbol_path, index=False)

    top = summary.sort_values(
        ["profit_factor", "total_net_r"],
        ascending=[False, False],
    ).head(10)

    print("\n" + "=" * 110)
    print("TOP CELLS BY PROFIT FACTOR")
    print("=" * 110)
    print(top.to_string(index=False))

    print("\n" + "=" * 110)
    print("OUTPUT FILES")
    print("=" * 110)
    print("Detail     :", detail_path)
    print("Summary    :", summary_path)
    print("By symbol  :", by_symbol_path)
    print("=" * 110)


if __name__ == "__main__":
    main()
