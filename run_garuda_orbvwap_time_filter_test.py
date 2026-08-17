import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from indicators.vwap import calculate_vwap
from backtesting.slippage import apply_slippage
from risk.stop_losses.orb_stop import calculate_orb_stop
from backtesting.pnl_calculator import calculate_trade_pnl
from backtesting.transaction_costs import calculate_transaction_costs

SYMBOLS = [
    "INFY", "RELIANCE", "ICICIBANK", "TMPV",
    "ASHOKLEY", "OLAELEC", "SUZLON"
]

RESEARCH_DIR = ROOT / "data" / "research"
RAW_DIR = ROOT / "data" / "raw"

TARGET_R = 2.0
ORB_FRACTION = 0.50

# Time-filter hypotheses. Times are entry-candle local time.
FILTERS = {
    "NO_FILTER": None,
    "ENTRY_LE_12_15": "12:15",
    "ENTRY_LE_13_15": "13:15",
    "ENTRY_LE_14_15": "14:15",
}


def load_entries(symbol):
    path = RESEARCH_DIR / f"{symbol}_frozen_entries_1y.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    for c in ["signal_candle_time", "entry_candle_time", "trade_date"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def load_data(symbol):
    path = RAW_DIR / f"{symbol}_5MIN_REAL.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return (
        df.dropna(subset=["datetime"])
        .sort_values("datetime")
        .drop_duplicates("datetime")
        .reset_index(drop=True)
    )


def get_sessions(df):
    result = {}
    for d, g in df.groupby(df["datetime"].dt.date):
        s = g.sort_values("datetime").reset_index(drop=True)
        s = s[
            (s["datetime"].dt.time >= pd.Timestamp("09:15").time())
            & (s["datetime"].dt.time <= pd.Timestamp("15:30").time())
        ].reset_index(drop=True)
        if not s.empty:
            result[d] = calculate_vwap(s)
    return result


def orb_values(session):
    orb = session[
        (session["datetime"].dt.time >= pd.Timestamp("09:15").time())
        & (session["datetime"].dt.time < pd.Timestamp("09:30").time())
    ]
    if orb.empty:
        return np.nan, np.nan, np.nan
    hi = float(orb["high"].max())
    lo = float(orb["low"].min())
    return hi, lo, hi - lo


def simulate_trade(session, entry_row):
    d = pd.Timestamp(entry_row["trade_date"]).date()
    entry_time = pd.Timestamp(entry_row["entry_candle_time"])
    direction = str(entry_row["direction"]).upper()

    m = session[session["datetime"] == entry_time]
    if m.empty:
        raise RuntimeError(f"Entry candle not found: {entry_time}")

    idx = int(m.index[0])
    entry_candle = session.iloc[idx]

    orb_hi, orb_lo, orb_range = orb_values(session)

    if not np.isfinite(orb_range) or orb_range <= 0:
        return None

    # Use the frozen entry price exactly as supplied by the existing universe.
    entry_price = float(entry_row["entry_price"])

    if direction == "BUY":
        stop = entry_price - ORB_FRACTION * orb_range
        target = entry_price + TARGET_R * (entry_price - stop)
    else:
        stop = entry_price + ORB_FRACTION * orb_range
        target = entry_price - TARGET_R * (stop - entry_price)

    risk = abs(entry_price - stop)
    if risk <= 0:
        return None

    future = session.iloc[idx:].copy()

    exit_reason = "END_OF_DAY"
    exit_price = float(future.iloc[-1]["close"])
    exit_time = future.iloc[-1]["datetime"]

    ambiguous = False

    for _, candle in future.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])

        if direction == "BUY":
            hit_sl = low <= stop
            hit_target = high >= target
        else:
            hit_sl = high >= stop
            hit_target = low <= target

        if hit_sl and hit_target:
            # Existing GARUDA convention: conservative stop-first handling.
            exit_reason = "STOP_LOSS"
            exit_price = stop
            exit_time = candle["datetime"]
            ambiguous = True
            break
        elif hit_sl:
            exit_reason = "STOP_LOSS"
            exit_price = stop
            exit_time = candle["datetime"]
            break
        elif hit_target:
            exit_reason = "TARGET"
            exit_price = target
            exit_time = candle["datetime"]
            break

    # Use GARUDA's existing P&L/cost functions where possible.
    # The entry price is already the frozen/slippage-adjusted entry.
    gross = (
        (exit_price - entry_price)
        if direction == "BUY"
        else (entry_price - exit_price)
    )

    # Keep the same per-share research convention as the existing matrix.
    # Transaction costs are proportional to turnover.
    costs = (
        (abs(entry_price) + abs(exit_price))
        * 0.001
    )

    net = gross - costs

    mfe = (
        float(future["high"].max()) - entry_price
        if direction == "BUY"
        else entry_price - float(future["low"].min())
    )
    mae = (
        entry_price - float(future["low"].min())
        if direction == "BUY"
        else float(future["high"].max()) - entry_price
    )

    mfe = max(0.0, mfe)
    mae = max(0.0, mae)

    return {
        "trade_date": d,
        "direction": direction,
        "entry_time": entry_time,
        "entry_price": entry_price,
        "stop": stop,
        "target": target,
        "risk": risk,
        "exit_time": exit_time,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "gross_pnl": gross,
        "costs": costs,
        "net_pnl": net,
        "mfe_r": mfe / risk,
        "mae_r": mae / risk,
        "ambiguous": ambiguous,
    }


def main():
    print()
    print("=" * 120)
    print("GARUDA — ORB+VWAP TIME-OF-DAY FILTER RESEARCH")
    print("=" * 120)
    print("Frozen universe : existing 1-year entries")
    print("Symbols         : 7")
    print("Expected entries: 1,880")
    print("SL              : 50% ORB range")
    print("Target          : 2R")
    print("BE              : OFF")
    print("Trailing        : OFF")
    print("Only variable  : entry-time filter")
    print("=" * 120)

    all_rows = []

    for symbol in SYMBOLS:
        entries = load_entries(symbol)
        data = load_data(symbol)
        sessions = get_sessions(data)

        for _, row in entries.iterrows():
            d = pd.Timestamp(row["trade_date"]).date()
            session = sessions.get(d)
            if session is None:
                raise RuntimeError(f"{symbol}: missing session {d}")

            trade = simulate_trade(session, row)
            if trade is None:
                continue

            trade["SYMBOL"] = symbol
            trade["entry_minute_from_open"] = (
                trade["entry_time"].hour * 60
                + trade["entry_time"].minute
                - (9 * 60 + 15)
            )
            all_rows.append(trade)

    df = pd.DataFrame(all_rows)

    if len(df) != 1880:
        raise RuntimeError(
            f"Expected 1,880 valid baseline trades, got {len(df)}"
        )

    rows = []

    for name, cutoff in FILTERS.items():
        if cutoff is None:
            g = df.copy()
        else:
            t = pd.Timestamp(cutoff).time()
            g = df[
                df["entry_time"].dt.time <= t
            ].copy()

        pnl = g["net_pnl"].astype(float)

        gp = pnl[pnl > 0].sum()
        gl = abs(pnl[pnl < 0].sum())
        pf = gp / gl if gl > 0 else np.inf

        equity = pnl.cumsum()
        dd = equity.cummax() - equity

        rows.append({
            "FILTER": name,
            "CUTOFF": cutoff or "NONE",
            "TRADES": len(g),
            "EXCLUDED": len(df) - len(g),
            "WIN_RATE_PCT": (pnl > 0).mean() * 100,
            "TOTAL_PNL": pnl.sum(),
            "AVG_PNL": pnl.mean(),
            "PROFIT_FACTOR": pf,
            "MAX_DRAWDOWN": dd.max(),
            "STOP_LOSS": int((g["exit_reason"] == "STOP_LOSS").sum()),
            "TARGET": int((g["exit_reason"] == "TARGET").sum()),
            "END_OF_DAY": int((g["exit_reason"] == "END_OF_DAY").sum()),
            "AVG_MFE_R": g["mfe_r"].mean(),
            "AVG_MAE_R": g["mae_r"].mean(),
        })

    summary = pd.DataFrame(rows)

    # Per-symbol results for each filter.
    symbol_rows = []
    for name, cutoff in FILTERS.items():
        if cutoff is None:
            g0 = df
        else:
            g0 = df[
                df["entry_time"].dt.time
                <= pd.Timestamp(cutoff).time()
            ]

        for symbol, g in g0.groupby("SYMBOL"):
            pnl = g["net_pnl"]
            gp = pnl[pnl > 0].sum()
            gl = abs(pnl[pnl < 0].sum())

            symbol_rows.append({
                "FILTER": name,
                "SYMBOL": symbol,
                "TRADES": len(g),
                "TOTAL_PNL": pnl.sum(),
                "AVG_PNL": pnl.mean(),
                "PROFIT_FACTOR": gp / gl if gl > 0 else np.inf,
                "WIN_RATE_PCT": (pnl > 0).mean() * 100,
                "AVG_MFE_R": g["mfe_r"].mean(),
                "AVG_MAE_R": g["mae_r"].mean(),
            })

    symbol_summary = pd.DataFrame(symbol_rows)

    detail_path = RESEARCH_DIR / "garuda_orbvwap_time_filter_detail.csv"
    summary_path = RESEARCH_DIR / "garuda_orbvwap_time_filter_summary.csv"
    symbol_path = RESEARCH_DIR / "garuda_orbvwap_time_filter_by_symbol.csv"

    df.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)
    symbol_summary.to_csv(symbol_path, index=False)

    print()
    print("=" * 120)
    print("7-STOCK AGGREGATE")
    print("=" * 120)
    print(summary.to_string(index=False))

    print()
    print("=" * 120)
    print("BY SYMBOL")
    print("=" * 120)
    print(symbol_summary.to_string(index=False))

    print()
    print("=" * 120)
    print("FILES")
    print("=" * 120)
    print(detail_path)
    print(summary_path)
    print(symbol_path)


if __name__ == "__main__":
    main()
