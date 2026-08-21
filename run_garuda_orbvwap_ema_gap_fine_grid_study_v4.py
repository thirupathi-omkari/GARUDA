"""
GARUDA — ORB+VWAP + EMA9/21 FINE-GRID GAP STUDY
Research only. No production strategy changes.

Purpose:
Refine the promising EMA separation region from the first study.
Tests finer thresholds around 0.30%–0.60% and reports:
- performance by threshold
- retention
- symbol-level performance
- direction-level performance
- threshold stability

Stop = 50% ORB range
Target = 2R
BE/trailing = OFF
"""

from pathlib import Path
import pandas as pd

from backtesting.slippage import apply_slippage
from backtesting.transaction_costs import calculate_transaction_costs

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
RESEARCH = ROOT / "data" / "research"

SYMBOLS = ["INFY", "RELIANCE", "ICICIBANK", "TMPV", "ASHOKLEY", "OLAELEC", "SUZLON"]

# Fine grid around the previously promising 0.30%–0.50% region.
THRESHOLDS_PCT = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]

ORB_SL_FRACTION = 0.50
TARGET_R = 2.0
SLIPPAGE_PCT = 0.05
COST_RATE = 0.10

OUT_DETAIL = RESEARCH / "garuda_orbvwap_ema_gap_fine_grid_detail.csv"
OUT_SUMMARY = RESEARCH / "garuda_orbvwap_ema_gap_fine_grid_summary.csv"
OUT_SYMBOL = RESEARCH / "garuda_orbvwap_ema_gap_fine_grid_by_symbol.csv"
OUT_DIRECTION = RESEARCH / "garuda_orbvwap_ema_gap_fine_grid_by_direction.csv"


def load_price(symbol):
    path = RAW / f"{symbol}_5MIN_REAL.csv"
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")

    df = pd.read_csv(path)
    required = {"datetime", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"{symbol}: missing raw columns {sorted(missing)}")

    df["datetime"] = (
        pd.to_datetime(df["datetime"], utc=True)
        .dt.tz_convert("Asia/Kolkata")
        .dt.tz_localize(None)
    )
    df = df.sort_values("datetime").reset_index(drop=True)

    # Complete historical series, sampled only at the frozen signal candle.
    df["ema9"] = df["close"].ewm(
        span=9, adjust=False, min_periods=9
    ).mean()
    df["ema21"] = df["close"].ewm(
        span=21, adjust=False, min_periods=21
    ).mean()

    return df


def load_frozen(symbol):
    """
    Discover the actual frozen-entry CSV used by the GARUDA research
    workspace instead of assuming the diagnostic summary file contains
    trade-level rows.

    Required trade-level columns:
      trade_date, direction, signal_candle_time, entry_candle_time

    Expected frozen counts are locked from the proven 7-stock study.
    """
    expected_counts = {
        "INFY": 236,
        "RELIANCE": 295,
        "ICICIBANK": 270,
        "TMPV": 270,
        "ASHOKLEY": 255,
        "OLAELEC": 271,
        "SUZLON": 283,
    }

    required = {
        "trade_date",
        "direction",
        "signal_candle_time",
        "entry_candle_time",
    }

    preferred_tokens = (
        "frozen",
        "entry",
        "diagnostic",
        "orbvwap",
        "7stock",
    )

    candidates = []
    seen_paths = set()

    # Search research first, then data. The same physical file can be
    # encountered twice because RESEARCH is a child of data; deduplicate
    # by resolved path before ranking candidates.
    for root in (RESEARCH, ROOT / "data"):
        if not root.exists():
            continue

        for path in root.rglob("*.csv"):
            path = path.resolve()
            if path in seen_paths:
                continue
            seen_paths.add(path)
            try:
                cols = set(pd.read_csv(path, nrows=0).columns)
            except Exception:
                continue

            if not required.issubset(cols):
                continue

            try:
                df = pd.read_csv(path)
            except Exception:
                continue

            # Symbol can be explicit or implied by a per-symbol filename.
            if "symbol" in df.columns:
                df = df[df["symbol"].astype(str).str.upper().eq(symbol)].copy()
            else:
                stem = path.stem.upper()
                if symbol.upper() not in stem:
                    continue

            if len(df) == expected_counts[symbol]:
                score = sum(token in path.stem.lower() for token in preferred_tokens)
                candidates.append((score, path, df))

    if not candidates:
        raise FileNotFoundError(
            f"{symbol}: could not discover a trade-level frozen-entry CSV "
            f"with exactly {expected_counts[symbol]} rows and required columns "
            f"{sorted(required)} under {ROOT / 'data'}"
        )

    # Prefer the most obviously frozen-entry file. If multiple candidates
    # remain tied, fail rather than silently mixing universes.
    candidates.sort(key=lambda x: (-x[0], str(x[1])))
    best_score = candidates[0][0]
    best = [x for x in candidates if x[0] == best_score]

    if len(best) > 1:
        names = [str(x[1]) for x in best]
        raise RuntimeError(
            f"{symbol}: multiple equally ranked frozen-entry candidates: {names}"
        )

    path = best[0][1]
    df = best[0][2].copy().reset_index(drop=True)

    print(f"             frozen source={path.name}")

    return df


def net_pnl(entry_price, exit_price, direction):
    gross = (
        exit_price - entry_price
        if direction == "BUY"
        else entry_price - exit_price
    )
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
        hi = float(c["high"])
        lo = float(c["low"])

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


def pct_label(x):
    return f"{x:g}"


def main():
    print("=" * 110)
    print("GARUDA — ORB+VWAP + EMA9/21 FINE-GRID GAP STUDY")
    print("=" * 110)
    print("Stop      : 50% ORB range")
    print("Target    : 2R")
    print("Threshold : " + ", ".join(f"{x:.2f}%" for x in THRESHOLDS_PCT))
    print("BE        : OFF")
    print("Trailing  : OFF")
    print("Research only — no production strategy changes")
    print("Frozen universe: exact proven counts (236/295/270/270/255/271/283)")
    print("Frozen source discovery: trade-level CSV with exact per-symbol count")
    print("=" * 110)

    rows = []
    baseline_count = 0

    for symbol in SYMBOLS:
        price = load_price(symbol)
        frozen = load_frozen(symbol)
        print(f"{symbol:<12}: frozen={len(frozen)}")

        sessions = {
            d: g.sort_values("datetime").reset_index(drop=True)
            for d, g in price.groupby(price["datetime"].dt.date)
        }

        for _, r in frozen.iterrows():
            trade_date = pd.Timestamp(r["trade_date"]).date()
            direction = str(r["direction"]).upper()
            # Frozen-entry timestamps may be stored as +05:30 aware
            # timestamps, while load_price() intentionally uses naive
            # Asia/Kolkata timestamps. Normalize both sides identically.
            signal_time = pd.Timestamp(r["signal_candle_time"])
            entry_time = pd.Timestamp(r["entry_candle_time"])

            if signal_time.tzinfo is not None:
                signal_time = (
                    signal_time.tz_convert("Asia/Kolkata")
                    .tz_localize(None)
                )
            if entry_time.tzinfo is not None:
                entry_time = (
                    entry_time.tz_convert("Asia/Kolkata")
                    .tz_localize(None)
                )

            session = sessions.get(trade_date)
            if session is None:
                continue

            # Raw candles are naive Asia/Kolkata timestamps. Normalize the
            # frozen timestamps to the same representation.
            def normalize_kolkata(ts):
                ts = pd.Timestamp(ts)
                if ts.tzinfo is not None:
                    return ts.tz_convert("Asia/Kolkata").tz_localize(None)
                return ts

            signal_time = normalize_kolkata(signal_time)
            entry_time = normalize_kolkata(entry_time)

            sm = session[session["datetime"].eq(signal_time)]
            em = session[session["datetime"].eq(entry_time)]

            if sm.empty or em.empty:
                # Do not silently discard frozen entries. This makes any
                # apples-to-apples mismatch visible.
                raise RuntimeError(
                    f"{symbol}: frozen candle missing "
                    f"signal={signal_time}, entry={entry_time}"
                )

            signal = sm.iloc[0]
            entry_row = em.iloc[0]

            ema9 = float(signal["ema9"])
            ema21 = float(signal["ema21"])
            if pd.isna(ema9) or pd.isna(ema21):
                continue

            # Directional separation expressed as a positive percentage.
            if direction == "BUY":
                gap_pct = (ema9 - ema21) / ema21 * 100.0
                regime_ok = gap_pct > 0
            else:
                gap_pct = (ema21 - ema9) / ema21 * 100.0
                regime_ok = gap_pct > 0

            raw_entry = float(entry_row["open"])
            entry_price = apply_slippage(
                price=raw_entry,
                direction=direction,
                slippage_pct=SLIPPAGE_PCT,
                is_entry=True,
            )

            orb = session[
                (session["datetime"].dt.strftime("%H:%M") >= "09:15")
                & (session["datetime"].dt.strftime("%H:%M") < "09:30")
            ]
            if orb.empty:
                continue

            orb_high = float(orb["high"].max())
            orb_low = float(orb["low"].min())
            orb_range = orb_high - orb_low
            if orb_range <= 0:
                continue

            distance = orb_range * ORB_SL_FRACTION
            stop_loss = (
                entry_price - distance
                if direction == "BUY"
                else entry_price + distance
            )
            initial_risk = abs(entry_price - stop_loss)
            if initial_risk <= 0:
                continue

            target = (
                entry_price + TARGET_R * initial_risk
                if direction == "BUY"
                else entry_price - TARGET_R * initial_risk
            )

            entry_idx = int(em.index[0])
            exit_time, exit_price, exit_reason, ambiguous = simulate(
                session, direction, entry_idx, entry_price, stop_loss, target
            )
            pnl = net_pnl(entry_price, exit_price, direction)
            net_r = pnl / initial_risk

            baseline_count += 1

            rows.append({
                "symbol": symbol,
                "trade_date": trade_date,
                "direction": direction,
                "signal_candle_time": signal_time,
                "entry_candle_time": entry_time,
                "entry_hour": entry_time.strftime("%H:%M"),
                "ema9": ema9,
                "ema21": ema21,
                "ema_gap_pct": gap_pct,
                "regime_ok": regime_ok,
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
                "net_pnl": pnl,
                "net_r": net_r,
            })

    base = pd.DataFrame(rows)
    if base.empty:
        raise RuntimeError(
            "No valid frozen entries were produced. "
            "The frozen-entry loader returned rows, but none matched the raw "
            "session signal/entry timestamps."
        )

    summaries = []
    symbol_rows = []
    direction_rows = []

    for threshold in THRESHOLDS_PCT:
        g = base[base["ema_gap_pct"] >= threshold].copy()
        variant = f"EMA_GAP_{str(threshold).replace('.', 'P')}PCT"

        wins = int((g["exit_reason"] == "TARGET").sum())
        losses = int((g["exit_reason"] == "STOP_LOSS").sum())
        eod = int((g["exit_reason"] == "END_OF_DAY").sum())

        positive = g.loc[g["net_pnl"] > 0, "net_pnl"].sum()
        negative = -g.loc[g["net_pnl"] < 0, "net_pnl"].sum()

        summaries.append({
            "variant": variant,
            "threshold_pct": threshold,
            "trades": len(g),
            "stop_loss": losses,
            "target": wins,
            "end_of_day": eod,
            "win_rate_pct": wins / len(g) * 100 if len(g) else 0,
            "total_net_pnl": g["net_pnl"].sum(),
            "avg_net_pnl": g["net_pnl"].mean() if len(g) else 0,
            "total_net_r": g["net_r"].sum(),
            "avg_net_r": g["net_r"].mean() if len(g) else 0,
            "profit_factor": positive / negative if negative else float("inf"),
            "retention_pct": len(g) / baseline_count * 100 if baseline_count else 0,
            "avg_gap_pct": g["ema_gap_pct"].mean() if len(g) else 0,
        })

        for symbol, sg in g.groupby("symbol"):
            symbol_rows.append({
                "threshold_pct": threshold,
                "symbol": symbol,
                "trades": len(sg),
                "win_rate_pct": (sg["exit_reason"].eq("TARGET").sum() / len(sg) * 100)
                    if len(sg) else 0,
                "total_net_pnl": sg["net_pnl"].sum(),
                "total_net_r": sg["net_r"].sum(),
                "avg_net_r": sg["net_r"].mean() if len(sg) else 0,
                "profit_factor": (
                    sg.loc[sg["net_pnl"] > 0, "net_pnl"].sum()
                    / -sg.loc[sg["net_pnl"] < 0, "net_pnl"].sum()
                ) if (sg["net_pnl"] < 0).any() else float("inf"),
            })

        for direction, dg in g.groupby("direction"):
            direction_rows.append({
                "threshold_pct": threshold,
                "direction": direction,
                "trades": len(dg),
                "win_rate_pct": (dg["exit_reason"].eq("TARGET").sum() / len(dg) * 100)
                    if len(dg) else 0,
                "total_net_pnl": dg["net_pnl"].sum(),
                "total_net_r": dg["net_r"].sum(),
                "avg_net_r": dg["net_r"].mean() if len(dg) else 0,
            })

    summary = pd.DataFrame(summaries)
    by_symbol = pd.DataFrame(symbol_rows)
    by_direction = pd.DataFrame(direction_rows)

    # Annotate every eligible trade with the fine-grid thresholds it survives.
    base["thresholds_survived"] = base["ema_gap_pct"].apply(
        lambda x: ",".join(str(t) for t in THRESHOLDS_PCT if x >= t)
    )

    RESEARCH.mkdir(parents=True, exist_ok=True)
    base.to_csv(OUT_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    by_symbol.to_csv(OUT_SYMBOL, index=False)
    by_direction.to_csv(OUT_DIRECTION, index=False)

    print()
    print("=" * 110)
    print("RESULTS — FINE EMA SEPARATION GRID")
    print("=" * 110)
    print(summary.to_string(index=False))

    print()
    print("Saved:")
    print(f"  {OUT_DETAIL}")
    print(f"  {OUT_SUMMARY}")
    print(f"  {OUT_SYMBOL}")
    print(f"  {OUT_DIRECTION}")
    print()
    print("RESEARCH ONLY — no production strategy was changed.")


if __name__ == "__main__":
    main()
