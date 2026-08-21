"""
GARUDA — ORB+VWAP + EMA9/21 REGIME FILTER STUDY

Research-only. Does NOT modify GARUDA production code.

Comparison:
1) Existing frozen ORB+VWAP entry universe (baseline)
2) Same frozen entries, but only when:
   BUY  -> EMA9 > EMA21 on the signal candle close
   SELL -> EMA9 < EMA21 on the signal candle close

Execution held constant:
- 50% ORB-range stop
- 2R target
- 0.05% adverse entry slippage
- 0.10% transaction cost
- BE OFF
- trailing OFF
- same frozen entry candles
"""

from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit
import backtesting.exit_simulator as exit_module
from backtesting.pnl_calculator import calculate_trade_pnl
from backtesting.slippage import apply_slippage


RAW = ROOT / "data" / "raw"
RESEARCH = ROOT / "data" / "research"

SYMBOLS = [
    "INFY", "RELIANCE", "ICICIBANK", "TMPV",
    "ASHOKLEY", "OLAELEC", "SUZLON",
]

TARGET_R = 2.0
ORB_SL_FRACTION = 0.50
SLIPPAGE_PCT = 0.05
COST_RATE_PCT = 0.10

OUT_DETAIL = RESEARCH / "garuda_orbvwap_ema_regime_orb_boundary_detail.csv"
OUT_SUMMARY = RESEARCH / "garuda_orbvwap_ema_regime_orb_boundary_summary.csv"
OUT_SYMBOL = RESEARCH / "garuda_orbvwap_ema_regime_orb_boundary_by_symbol.csv"
OUT_TIME = RESEARCH / "garuda_orbvwap_ema_regime_orb_boundary_by_time.csv"


def pick_col(df, names, required=True):
    for name in names:
        if name in df.columns:
            return name
    if required:
        raise RuntimeError(
            f"Could not find any of {names}. Available columns: {list(df.columns)}"
        )
    return None


def load_frozen_entries(symbol):
    candidates = [
        RESEARCH / f"{symbol}_frozen_entries_1y.csv",
        RESEARCH / "garuda_orbvwap_1year_entry_diagnostic_detail.csv",
    ]

    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            f"No frozen ORB/VWAP entry file found for {symbol}"
        )

    df = pd.read_csv(path)

    # The aggregate diagnostic detail can contain all symbols.
    if "symbol" in df.columns:
        df = df[df["symbol"].astype(str).str.upper() == symbol].copy()

    date_col = pick_col(df, ["trade_date", "date"])
    direction_col = pick_col(df, ["direction", "side"])
    signal_col = pick_col(df, ["signal_candle_time", "signal_time"])
    entry_col = pick_col(df, ["entry_candle_time", "entry_time"])

    out = pd.DataFrame({
        "trade_date": pd.to_datetime(df[date_col]).dt.date,
        "direction": df[direction_col].astype(str).str.upper(),
        "signal_candle_time": (
            pd.to_datetime(df[signal_col], utc=True)
            .dt.tz_convert("Asia/Kolkata")
            .dt.tz_localize(None)
        ),
        "entry_candle_time": (
            pd.to_datetime(df[entry_col], utc=True)
            .dt.tz_convert("Asia/Kolkata")
            .dt.tz_localize(None)
        ),
    })

    out = out[out["direction"].isin(["BUY", "SELL"])].copy()

    # Defensive deduplication: same underlying frozen entry must be one trade.
    out = out.drop_duplicates(
        subset=["trade_date", "direction", "signal_candle_time", "entry_candle_time"]
    )

    return out.sort_values("entry_candle_time").reset_index(drop=True)


def load_price(symbol):
    path = RAW / f"{symbol}_5MIN_REAL.csv"
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")

    df = pd.read_csv(path)
    required = {"datetime", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"{symbol}: missing raw columns {sorted(missing)}")

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    df = df.sort_values("datetime").reset_index(drop=True)

    # EMA is calculated on the complete historical series, then sampled
    # only at the frozen signal candle. No future information is used.
    df["ema9"] = df["close"].ewm(span=9, adjust=False, min_periods=9).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False, min_periods=21).mean()

    return df


def session_map(df):
    return {
        d: g.sort_values("datetime").reset_index(drop=True)
        for d, g in df.groupby(df["datetime"].dt.date)
    }


def metrics(trades):
    if not trades:
        return {
            "trades": 0, "stop_loss": 0, "target": 0, "end_of_day": 0,
            "wins": 0, "losses": 0, "win_rate_pct": 0.0,
            "total_net_pnl": 0.0, "avg_net_pnl": 0.0,
            "total_net_r": 0.0, "avg_net_r": 0.0,
            "profit_factor": 0.0, "max_drawdown_r": 0.0,
            "avg_mfe_r": 0.0, "p90_mfe_r": 0.0,
            "avg_mae_r": 0.0, "p90_mae_r": 0.0,
        }

    df = pd.DataFrame(trades)
    net = pd.to_numeric(df["net_pnl"], errors="coerce")
    r = pd.to_numeric(df["net_r"], errors="coerce")

    wins = int((net > 0).sum())
    losses = int((net < 0).sum())
    gross_profit = float(net[net > 0].sum())
    gross_loss = float(-net[net < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    equity = r.cumsum()
    drawdown = equity - equity.cummax()
    max_dd = float(-drawdown.min()) if len(drawdown) else 0.0

    return {
        "trades": len(df),
        "stop_loss": int((df["exit_reason"] == "STOP_LOSS").sum()),
        "target": int((df["exit_reason"] == "TARGET").sum()),
        "end_of_day": int((df["exit_reason"] == "END_OF_DAY").sum()),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": wins / len(df) * 100.0,
        "total_net_pnl": float(net.sum()),
        "avg_net_pnl": float(net.mean()),
        "total_net_r": float(r.sum()),
        "avg_net_r": float(r.mean()),
        "profit_factor": pf,
        "max_drawdown_r": max_dd,
        "avg_mfe_r": float(df["mfe_r"].mean()),
        "p90_mfe_r": float(df["mfe_r"].quantile(0.90)),
        "avg_mae_r": float(df["mae_r"].mean()),
        "p90_mae_r": float(df["mae_r"].quantile(0.90)),
    }


def run_symbol(symbol):
    price = load_price(symbol)
    sessions = session_map(price)
    frozen = load_frozen_entries(symbol)

    print(f"{symbol:<12}: frozen={len(frozen)}")

    results = []

    for _, row in frozen.iterrows():
        trade_date = row["trade_date"]
        direction = row["direction"]
        signal_time = pd.Timestamp(row["signal_candle_time"])
        entry_time = pd.Timestamp(row["entry_candle_time"])

        session = sessions.get(trade_date)
        if session is None:
            raise RuntimeError(f"{symbol}: missing session {trade_date}")

        sm = session[session["datetime"] == signal_time]
        em = session[session["datetime"] == entry_time]

        if sm.empty or em.empty:
            raise RuntimeError(
                f"{symbol}: frozen candle missing "
                f"signal={signal_time}, entry={entry_time}"
            )

        signal_idx = int(sm.index[0])
        entry_idx = int(em.index[0])
        signal = session.iloc[signal_idx]
        entry = session.iloc[entry_idx]

        ema9 = signal["ema9"]
        ema21 = signal["ema21"]

        ema_available = (
            pd.notna(ema9)
            and pd.notna(ema21)
        )

        if ema_available:
            ema9 = float(ema9)
            ema21 = float(ema21)

            regime_ok = (
                (direction == "BUY" and ema9 > ema21) or
                (direction == "SELL" and ema9 < ema21)
            )
        else:
            regime_ok = False

        raw_entry = float(entry["open"])
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
            raise RuntimeError(f"{symbol}: ORB unavailable {trade_date}")

        orb_high = float(orb["high"].max())
        orb_low = float(orb["low"].min())
        orb_range = orb_high - orb_low
        # --------------------------------------------------
        # ORB HIGH/LOW STOP
        #
        # BUY  -> stop at ORB LOW
        # SELL -> stop at ORB HIGH
        # --------------------------------------------------

        stop_loss = (
            orb_low
            if direction == "BUY"
            else orb_high
        )

        sl_distance = abs(entry_price - stop_loss)

        if sl_distance <= 0:
            raise RuntimeError(
                f"{symbol}: invalid ORB boundary risk "
                f"{trade_date} {direction} "
                f"entry={entry_price} "
                f"orb_high={orb_high} "
                f"orb_low={orb_low}"
            )

        initial_risk = abs(entry_price - stop_loss)

        target = (
            entry_price + TARGET_R * initial_risk
            if direction == "BUY"
            else entry_price - TARGET_R * initial_risk
        )

        trade = BacktestTrade(
            symbol=symbol,
            strategy_name="ORB_VWAP_ORB_BOUNDARY_EMA_REGIME_RESEARCH",
            trade_date=trade_date,
            direction=direction,
            entry_time=entry_time,
            entry_price=entry_price,
            quantity=1,
        )

        trade.initial_stop_loss = stop_loss
        trade.initial_risk = initial_risk
        trade.target_price = target
        trade.target_r = TARGET_R

        future = session.iloc[entry_idx:].copy().reset_index(drop=True)

        completed = simulate_trade_exit(
            trade=trade,
            future_candles=future,
            stop_loss=stop_loss,
            target=target,
        )

        if completed is None or completed.exit_price is None:
            raise RuntimeError(
                f"{symbol}: no exit for {trade_date} {direction} {entry_time}"
            )

        # Use project's P&L calculator for consistency.
        completed = calculate_trade_pnl(
            trade=completed,
            cost_rate_pct=COST_RATE_PCT,
        )

        net_pnl = float(getattr(completed, "net_pnl", 0.0))
        net_r = net_pnl / initial_risk if initial_risk > 0 else 0.0

        results.append({
            "symbol": symbol,
            "trade_date": trade_date,
            "direction": direction,
            "signal_candle_time": signal_time,
            "entry_candle_time": entry_time,
            "entry_hour": entry_time.strftime("%H:%M"),
            "ema9": ema9,
            "ema21": ema21,
            "ema_regime_ok": regime_ok,
            "entry_price": entry_price,
            "orb_high": orb_high,
            "orb_low": orb_low,
            "orb_range": orb_range,
            "stop_loss": stop_loss,
            "initial_risk": initial_risk,
            "target": target,
            "exit_time": completed.exit_time,
            "exit_price": completed.exit_price,
            "exit_reason": completed.exit_reason,
            "ambiguous": bool(getattr(completed, "same_candle_ambiguous", False)),
            "mfe_r": float(getattr(completed, "mfe_r", 0.0) or 0.0),
            "mae_r": float(getattr(completed, "mae_r", 0.0) or 0.0),
            "net_pnl": net_pnl,
            "net_r": net_r,
        })

    return results


def main():
    exit_module.risk_config.break_even_enabled = False
    exit_module.risk_config.trailing_stop_enabled = False

    print("=" * 110)
    print("GARUDA — ORB+VWAP + EMA9/21 REGIME FILTER STUDY")
    print("=" * 110)
    print("Baseline : all frozen ORB+VWAP entries")
    print("Filter   : BUY EMA9>EMA21 / SELL EMA9<EMA21 at signal close")
    print("SL       : ORB HIGH/LOW")
    print("Target   : 2R")
    print("BE       : OFF")
    print("Trailing : OFF")
    print("Universe : 7 stocks / existing frozen ORB+VWAP entries")
    print("=" * 110)

    all_rows = []
    for symbol in SYMBOLS:
        all_rows.extend(run_symbol(symbol))

    detail = pd.DataFrame(all_rows)

    if len(detail) == 0:
        raise RuntimeError("No trades produced.")

    # Baseline and filtered subsets use the SAME frozen trades.
    baseline = detail.copy()
    filtered = detail[detail["ema_regime_ok"]].copy()

    baseline["variant"] = "BASELINE_ORBVWAP"
    filtered["variant"] = "ORBVWAP_EMA_REGIME"

    combined = pd.concat([baseline, filtered], ignore_index=True)

    summary_rows = []
    for variant, group in combined.groupby("variant"):
        m = metrics(group.to_dict("records"))
        summary_rows.append({"variant": variant, **m})

    summary = pd.DataFrame(summary_rows)

    # Symbol comparison.
    symbol_rows = []
    for symbol in SYMBOLS:
        for variant, group in [
            ("BASELINE_ORBVWAP", baseline[baseline["symbol"] == symbol]),
            ("ORBVWAP_EMA_REGIME", filtered[filtered["symbol"] == symbol]),
        ]:
            m = metrics(group.to_dict("records"))
            symbol_rows.append({
                "symbol": symbol,
                "variant": variant,
                **m,
            })

    by_symbol = pd.DataFrame(symbol_rows)

    # Entry-time comparison.
    time_rows = []
    for hour, group in baseline.groupby("entry_hour"):
        base = metrics(group.to_dict("records"))
        filt = filtered[filtered["entry_hour"] == hour]
        fm = metrics(filt.to_dict("records"))
        time_rows.append({
            "entry_time": hour,
            "baseline_trades": base["trades"],
            "baseline_pf": base["profit_factor"],
            "baseline_avg_net_r": base["avg_net_r"],
            "baseline_total_net_r": base["total_net_r"],
            "filtered_trades": fm["trades"],
            "filtered_pf": fm["profit_factor"],
            "filtered_avg_net_r": fm["avg_net_r"],
            "filtered_total_net_r": fm["total_net_r"],
        })

    by_time = pd.DataFrame(time_rows).sort_values("entry_time")

    RESEARCH.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    by_symbol.to_csv(OUT_SYMBOL, index=False)
    by_time.to_csv(OUT_TIME, index=False)

    print()
    print("=" * 110)
    print("RESULTS")
    print("=" * 110)
    print(summary.to_string(index=False))

    print()
    print("=" * 110)
    print("EMA FILTER RETENTION")
    print("=" * 110)
    print(f"Baseline frozen entries : {len(baseline)}")
    print(f"EMA-filtered entries   : {len(filtered)}")
    print(f"Retention               : {len(filtered) / len(baseline) * 100:.2f}%")

    print()
    print("Saved:")
    print(f"  {OUT_DETAIL}")
    print(f"  {OUT_SUMMARY}")
    print(f"  {OUT_SYMBOL}")
    print(f"  {OUT_TIME}")
    print()
    print("RESEARCH ONLY — no production strategy was changed.")


if __name__ == "__main__":
    main()
