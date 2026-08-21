"""
GARUDA — ORB+VWAP STOP-LOSS COMPARISON STUDY
Research only. No production strategy changes.

Compares the same frozen ORB+VWAP entries under:
1. 50% of ORB range stop
2. ORB boundary stop (low for BUY / high for SELL)

Target = 2R, BE/trailing OFF.
"""
from pathlib import Path
import pandas as pd

from backtesting.slippage import apply_slippage
from backtesting.transaction_costs import calculate_transaction_costs

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
RESEARCH = ROOT / "data" / "research"

SYMBOLS = ["INFY", "RELIANCE", "ICICIBANK", "TMPV", "ASHOKLEY", "OLAELEC", "SUZLON"]
ORB_SL_FRACTION = 0.50
TARGET_R = 2.0
SLIPPAGE_PCT = 0.05
COST_RATE = 0.10

OUT_DETAIL = RESEARCH / "garuda_orbvwap_sl_comparison_detail.csv"
OUT_SUMMARY = RESEARCH / "garuda_orbvwap_sl_comparison_summary.csv"
OUT_SYMBOL = RESEARCH / "garuda_orbvwap_sl_comparison_by_symbol.csv"
OUT_TIME = RESEARCH / "garuda_orbvwap_sl_comparison_by_time.csv"

def load_price(symbol):
    path = RAW / f"{symbol}_5MIN_REAL.csv"
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")
    df = pd.read_csv(path)
    df["datetime"] = (
        pd.to_datetime(df["datetime"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.tz_localize(None)
    )
    return df.sort_values("datetime").reset_index(drop=True)

def load_frozen(symbol):
    path = RESEARCH / f"{symbol}_frozen_entries_1y.csv"

    if path.exists():
        df = pd.read_csv(path)
    else:
        path = RESEARCH / "garuda_orbvwap_1year_entry_diagnostic_detail.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Frozen ORB+VWAP entries not found for {symbol}"
            )

        df = pd.read_csv(path)

        if "symbol" in df.columns:
            df = df[df["symbol"].eq(symbol)].copy()

    # Match the raw-price timestamp convention:
    # timezone-aware source -> IST -> timezone-naive.
    for column in ("signal_candle_time", "entry_candle_time"):
        if column in df.columns:
            df[column] = (
                pd.to_datetime(df[column], utc=True)
                .dt.tz_convert("Asia/Kolkata")
                .dt.tz_localize(None)
            )

    return df
    if direction == "BUY":
        gross = exit_price - entry_price
    else:
        gross = entry_price - exit_price

    costs = calculate_transaction_costs(
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=1,
        cost_rate_pct=COST_RATE,
    )

    return gross - costs

def cost_adjusted_net_pnl(entry_price, exit_price, direction):
    if direction == "BUY":
        gross = exit_price - entry_price
    else:
        gross = entry_price - exit_price

    costs = calculate_transaction_costs(
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=1,
        cost_rate_pct=COST_RATE,
    )

    return gross - costs

def simulate(session, direction, entry_idx, entry_price, stop_loss, target):
    for i in range(entry_idx, len(session)):
        c = session.iloc[i]
        hi, lo = float(c["high"]), float(c["low"])

        hit_sl = lo <= stop_loss if direction == "BUY" else hi >= stop_loss
        hit_target = hi >= target if direction == "BUY" else lo <= target

        if hit_sl and hit_target:
            return c["datetime"], stop_loss, "STOP_LOSS", True
        if hit_sl:
            return c["datetime"], stop_loss, "STOP_LOSS", False
        if hit_target:
            return c["datetime"], target, "TARGET", False

    c = session.iloc[-1]
    return c["datetime"], float(c["close"]), "END_OF_DAY", False

def main():
    print("=" * 110)
    print("GARUDA — ORB+VWAP STOP-LOSS COMPARISON STUDY")
    print("=" * 110)
    print("Baseline : same frozen ORB+VWAP entries")
    print("Variants : 50% ORB RANGE SL vs ORB HIGH/LOW SL")
    print("Target   : 2R")
    print("BE       : OFF")
    print("Trailing : OFF")
    print("Universe : 7 stocks / existing frozen ORB+VWAP entries")
    print("=" * 110)

    rows = []

    for symbol in SYMBOLS:
        price = load_price(symbol)
        frozen = load_frozen(symbol)
        print(f"{symbol:<12}: frozen={len(frozen)}")

        sessions = {
            d: g.reset_index(drop=True)
            for d, g in price.groupby(price["datetime"].dt.date)
        }

        for _, r in frozen.iterrows():
            trade_date = pd.Timestamp(r["trade_date"]).date()
            direction = str(r["direction"])
            signal_time = pd.Timestamp(r["signal_candle_time"])
            entry_time = pd.Timestamp(r["entry_candle_time"])

            session = sessions.get(trade_date)
            if session is None:
                continue

            em = session[session["datetime"].eq(entry_time)]
            if em.empty:
                continue

            entry_idx = int(em.index[0])
            raw_entry = float(em.iloc[0]["open"])
            entry_price = apply_slippage(
                price=raw_entry,
                direction=direction,
                slippage_pct=SLIPPAGE_PCT,
                is_entry=True,
            )

            orb = session[
                (session["datetime"].dt.strftime("%H:%M") >= "09:15") &
                (session["datetime"].dt.strftime("%H:%M") < "09:30")
            ]
            if orb.empty:
                continue

            orb_high = float(orb["high"].max())
            orb_low = float(orb["low"].min())
            orb_range = orb_high - orb_low
            if orb_range <= 0:
                continue

            for variant in ("ORB_50PCT", "ORB_BOUNDARY"):
                if variant == "ORB_50PCT":
                    distance = orb_range * ORB_SL_FRACTION
                    stop_loss = (
                        entry_price - distance if direction == "BUY"
                        else entry_price + distance
                    )
                else:
                    stop_loss = orb_low if direction == "BUY" else orb_high

                initial_risk = abs(entry_price - stop_loss)
                if initial_risk <= 0:
                    continue

                target = (
                    entry_price + TARGET_R * initial_risk
                    if direction == "BUY"
                    else entry_price - TARGET_R * initial_risk
                )

                exit_time, exit_price, exit_reason, ambiguous = simulate(
                    session, direction, entry_idx, entry_price, stop_loss, target
                )
                net_pnl = cost_adjusted_net_pnl(
                    entry_price, exit_price, direction
                )
                net_r = net_pnl / initial_risk

                rows.append({
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "direction": direction,
                    "signal_candle_time": signal_time,
                    "entry_candle_time": entry_time,
                    "entry_hour": entry_time.strftime("%H:%M"),
                    "entry_price": entry_price,
                    "orb_high": orb_high,
                    "orb_low": orb_low,
                    "orb_range": orb_range,
                    "stop_loss": stop_loss,
                    "initial_risk": initial_risk,
                    "target": target,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "ambiguous": ambiguous,
                    "net_pnl": net_pnl,
                    "net_r": net_r,
                    "variant": variant,
                })

    detail = pd.DataFrame(rows)

    summaries = []
    for variant, g in detail.groupby("variant"):
        wins = int((g["exit_reason"] == "TARGET").sum())
        losses = int((g["exit_reason"] == "STOP_LOSS").sum())
        eod = int((g["exit_reason"] == "END_OF_DAY").sum())
        positive = g.loc[g["net_pnl"] > 0, "net_pnl"].sum()
        negative = -g.loc[g["net_pnl"] < 0, "net_pnl"].sum()
        summaries.append({
            "variant": variant,
            "trades": len(g),
            "stop_loss": losses,
            "target": wins,
            "end_of_day": eod,
            "win_rate_pct": wins / len(g) * 100 if len(g) else 0,
            "total_net_pnl": g["net_pnl"].sum(),
            "avg_net_pnl": g["net_pnl"].mean(),
            "total_net_r": g["net_r"].sum(),
            "avg_net_r": g["net_r"].mean(),
            "profit_factor": positive / negative if negative else float("inf"),
        })

    summary = pd.DataFrame(summaries)
    by_symbol = (
        detail.groupby(["variant", "symbol"])
        .agg(
            trades=("net_r", "size"),
            total_net_r=("net_r", "sum"),
            avg_net_r=("net_r", "mean"),
            total_net_pnl=("net_pnl", "sum"),
        )
        .reset_index()
    )
    by_time = (
        detail.groupby(["variant", "entry_hour"])
        .agg(
            trades=("net_r", "size"),
            total_net_r=("net_r", "sum"),
            avg_net_r=("net_r", "mean"),
        )
        .reset_index()
    )

    RESEARCH.mkdir(parents=True, exist_ok=True)
    detail.to_csv(OUT_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    by_symbol.to_csv(OUT_SYMBOL, index=False)
    by_time.to_csv(OUT_TIME, index=False)

    print("\n" + "=" * 110)
    print("RESULTS")
    print("=" * 110)
    print(summary.to_string(index=False))
    print("\nSaved:")
    print(f"  {OUT_DETAIL}")
    print(f"  {OUT_SUMMARY}")
    print(f"  {OUT_SYMBOL}")
    print(f"  {OUT_TIME}")
    print("\nRESEARCH ONLY — no production strategy was changed.")

if __name__ == "__main__":
    main()
