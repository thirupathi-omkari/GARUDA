import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit
import backtesting.exit_simulator as exit_module
from backtesting.pnl_calculator import calculate_trade_pnl
from backtesting.slippage import apply_slippage

DATA_FILE = PROJECT_ROOT / "data" / "raw" / "INFY_5MIN_REAL.csv"
LOCKED_ENTRY_FILE = PROJECT_ROOT / "data" / "orb_50pct_sl_2r_infy.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "orb_baseline_sl_2r_infy_same43_fixed.csv"

SYMBOL = "INFY"
TARGET_R = 2.0
COST_RATE_PCT = 0.10
SLIPPAGE_PCT = 0.05
EXPECTED_ENTRIES = 43

print()
print("=" * 100)
print("GARUDA — FIXED 43-ENTRY EXISTING ORB BASELINE SL + 2R RESEARCH")
print("=" * 100)

df = pd.read_csv(DATA_FILE)
required = {"datetime","open","high","low","close","volume"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)

print(f"Data file : {DATA_FILE}")
print(f"Rows     : {len(df)}")
print(f"From     : {df['datetime'].iloc[0]}")
print(f"To       : {df['datetime'].iloc[-1]}")

sessions = []
for _, group in df.groupby(df["datetime"].dt.date):
    session = group.sort_values("datetime").reset_index(drop=True)
    if not session.empty:
        sessions.append(session)
sessions.sort(key=lambda x: x["datetime"].iloc[0])
print(f"Sessions : {len(sessions)}")

# Hard-lock the exact simulator risk configuration.
exit_module.risk_config.break_even_enabled = False
exit_module.risk_config.trailing_stop_enabled = False

print()
print(f"BREAK-EVEN         : {exit_module.risk_config.break_even_enabled}")
print(f"TRAILING STOP      : {exit_module.risk_config.trailing_stop_enabled}")

if exit_module.risk_config.break_even_enabled or exit_module.risk_config.trailing_stop_enabled:
    raise RuntimeError("BASELINE CONFIG ERROR: BE/trailing must both be OFF.")

locked = pd.read_csv(LOCKED_ENTRY_FILE)
required_locked = {"trade_date","direction","signal_candle_time","entry_candle_time"}
missing_locked = required_locked - set(locked.columns)
if missing_locked:
    raise ValueError(f"Locked entry universe missing columns: {sorted(missing_locked)}")

if len(locked) != EXPECTED_ENTRIES:
    raise RuntimeError(
        f"LOCKED ENTRY UNIVERSE MISMATCH: expected {EXPECTED_ENTRIES}, got {len(locked)}"
    )

locked["trade_date"] = pd.to_datetime(locked["trade_date"]).dt.date
locked["signal_candle_time"] = pd.to_datetime(locked["signal_candle_time"])
locked["entry_candle_time"] = pd.to_datetime(locked["entry_candle_time"])

print()
print(f"LOCKED ENTRY UNIVERSE : {len(locked)} entries")
print(f"Entry source          : {LOCKED_ENTRY_FILE}")

session_by_date = {
    s["datetime"].dt.date.iloc[0]: s for s in sessions
}

trades = []

for idx, row in locked.iterrows():
    trade_date = row["trade_date"]
    direction = str(row["direction"]).upper()
    signal_time = pd.Timestamp(row["signal_candle_time"])
    entry_time = pd.Timestamp(row["entry_candle_time"])

    session = session_by_date.get(trade_date)
    if session is None:
        raise RuntimeError(f"Session missing: {trade_date}")

    sm = session[session["datetime"] == signal_time]
    em = session[session["datetime"] == entry_time]
    if sm.empty or em.empty:
        raise RuntimeError(
            f"Locked candle missing: signal={signal_time}, entry={entry_time}"
        )

    signal_position = int(sm.index[0])
    entry_position = int(em.index[0])
    signal_candle = session.iloc[signal_position]
    entry_candle = session.iloc[entry_position]

    # Existing ORB baseline:
    # BUY  -> ORB low
    # SELL -> ORB high
    orb = session[
        (session["datetime"].dt.strftime("%H:%M") >= "09:15") &
        (session["datetime"].dt.strftime("%H:%M") < "09:30")
    ]

    if orb.empty:
        raise RuntimeError(f"ORB unavailable: {trade_date}")

    opening_high = float(orb["high"].max())
    opening_low = float(orb["low"].min())

    raw_entry = float(entry_candle["open"])
    entry_price = apply_slippage(
        price=raw_entry,
        direction=direction,
        slippage_pct=SLIPPAGE_PCT,
        is_entry=True,
    )

    if direction == "BUY":
        stop_loss = opening_low
        initial_risk = entry_price - stop_loss
    elif direction == "SELL":
        stop_loss = opening_high
        initial_risk = stop_loss - entry_price
    else:
        raise RuntimeError(f"Invalid direction: {direction}")

    if initial_risk <= 0:
        raise RuntimeError(
            f"INVALID BASELINE RISK: {trade_date} {direction} "
            f"entry={entry_price} stop={stop_loss} risk={initial_risk}"
        )

    if direction == "BUY":
        target = entry_price + TARGET_R * initial_risk
    else:
        target = entry_price - TARGET_R * initial_risk

    trade = BacktestTrade(
        symbol=SYMBOL,
        strategy_name="ORB_VWAP_EXISTING_ORB_BASELINE",
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

    future = session.iloc[entry_position:].copy().reset_index(drop=True)

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=stop_loss,
        target=target,
    )

    if trade is None or trade.exit_price is None:
        raise RuntimeError(f"No exit: {trade_date} {direction} {entry_time}")

    # With BE/trailing OFF, STOP_LOSS must equal the original ORB stop.
    if trade.exit_reason == "STOP_LOSS":
        if abs(float(trade.exit_price) - float(stop_loss)) > 1e-9:
            raise RuntimeError(
                "BASELINE FIXED STOP INTEGRITY FAILURE: "
                f"{trade.exit_price} != {stop_loss}; "
                f"{trade_date} {direction} {entry_time}"
            )

    trade.exit_price = apply_slippage(
        price=float(trade.exit_price),
        direction=direction,
        slippage_pct=SLIPPAGE_PCT,
        is_entry=False,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=COST_RATE_PCT,
    )

    exit_time = pd.Timestamp(trade.exit_time)
    xm = session[session["datetime"] == exit_time]
    if xm.empty:
        dist = (session["datetime"] - exit_time).abs()
        exit_position = int(dist.argmin())
        exit_candle = session.iloc[exit_position]
    else:
        exit_position = int(xm.index[0])
        exit_candle = session.iloc[exit_position]

    if direction == "BUY":
        sl_touched = float(exit_candle["low"]) <= stop_loss
        target_touched = float(exit_candle["high"]) >= target
    else:
        sl_touched = float(exit_candle["high"]) >= stop_loss
        target_touched = float(exit_candle["low"]) <= target

    trade.same_candle_ambiguous = sl_touched and target_touched

    trade.signal_candle_time = signal_time
    trade.signal_candle_open = float(signal_candle["open"])
    trade.signal_candle_high = float(signal_candle["high"])
    trade.signal_candle_low = float(signal_candle["low"])
    trade.signal_candle_close = float(signal_candle["close"])

    trade.entry_candle_time = entry_time
    trade.entry_candle_open = float(entry_candle["open"])
    trade.entry_candle_high = float(entry_candle["high"])
    trade.entry_candle_low = float(entry_candle["low"])
    trade.entry_candle_close = float(entry_candle["close"])

    trade.exit_candle_time = exit_time
    trade.exit_candle_open = float(exit_candle["open"])
    trade.exit_candle_high = float(exit_candle["high"])
    trade.exit_candle_low = float(exit_candle["low"])
    trade.exit_candle_close = float(exit_candle["close"])

    trades.append(trade)

if len(trades) != EXPECTED_ENTRIES:
    raise RuntimeError(
        f"FINAL LOCKED ENTRY COUNT FAILURE: expected {EXPECTED_ENTRIES}, got {len(trades)}"
    )

print()
print(f"FINAL LOCKED ENTRY COUNT : {len(trades)} / {EXPECTED_ENTRIES}")

total = len(trades)
sl_count = sum(t.exit_reason == "STOP_LOSS" for t in trades)
target_count = sum(t.exit_reason == "TARGET" for t in trades)
eod_count = sum(t.exit_reason == "END_OF_DAY" for t in trades)
wins = sum(t.net_pnl > 0 for t in trades)
losses = sum(t.net_pnl < 0 for t in trades)
total_pnl = sum(t.net_pnl for t in trades)
avg_pnl = total_pnl / total
gp = sum(t.net_pnl for t in trades if t.net_pnl > 0)
gl = abs(sum(t.net_pnl for t in trades if t.net_pnl < 0))
pf = gp / gl if gl else float("inf")
win_rate = wins / total * 100
ambiguous = sum(bool(t.same_candle_ambiguous) for t in trades)

mfe = pd.Series(
    [float(t.mfe_r) for t in trades if getattr(t, "mfe_r", None) is not None and not pd.isna(t.mfe_r)],
    dtype=float,
)
mae = pd.Series(
    [float(t.mae_r) for t in trades if getattr(t, "mae_r", None) is not None and not pd.isna(t.mae_r)],
    dtype=float,
)

print()
print("=" * 110)
print("VALID EXISTING ORB BASELINE SL + 2R RESULTS")
print("=" * 110)
print(f"TRADES             : {total}")
print(f"STOP_LOSS          : {sl_count}")
print(f"TARGET             : {target_count}")
print(f"END_OF_DAY         : {eod_count}")
print(f"WINNING_TRADES     : {wins}")
print(f"LOSING_TRADES      : {losses}")
print(f"WIN_RATE_PCT       : {win_rate:.2f}")
print(f"AVG_PNL            : {avg_pnl:.2f}")
print(f"TOTAL_PNL          : {total_pnl:.2f}")
print(f"PROFIT_FACTOR      : {pf:.3f}")
print(f"AMBIGUOUS_CANDLES  : {ambiguous}")
print(f"AVG_MFE_R          : {mfe.mean():.3f}")
print(f"MEDIAN_MFE_R       : {mfe.median():.3f}")
print(f"P75_MFE_R          : {mfe.quantile(.75):.3f}")
print(f"P90_MFE_R          : {mfe.quantile(.90):.3f}")
print(f"AVG_MAE_R          : {mae.mean():.3f}")
print(f"MEDIAN_MAE_R       : {mae.median():.3f}")
print(f"P75_MAE_R          : {mae.quantile(.75):.3f}")
print(f"P90_MAE_R          : {mae.quantile(.90):.3f}")
print("=" * 110)

print()
print("=" * 170)
print("EXISTING ORB BASELINE — 43-ENTRY AUDIT")
print("=" * 170)
print(
    f"{'DATE':<12}{'SIDE':<6}{'ENTRY':>11}{'SL':>11}"
    f"{'RISK':>10}{'TARGET':>11}{'MFE_R':>9}{'MAE_R':>9}"
    f"{'REASON':<15}{'PNL':>10}"
)
print("-" * 170)

for t in trades:
    print(
        f"{str(t.trade_date):<12}"
        f"{t.direction:<6}"
        f"{t.entry_price:>11.2f}"
        f"{t.initial_stop_loss:>11.2f}"
        f"{t.initial_risk:>10.2f}"
        f"{t.target_price:>11.2f}"
        f"{t.mfe_r:>9.3f}"
        f"{t.mae_r:>9.3f}"
        f"{t.exit_reason:<15}"
        f"{t.net_pnl:>10.2f}"
    )

rows = []
for t in trades:
    rows.append({
        "trade_date": t.trade_date,
        "direction": t.direction,
        "signal_candle_time": t.signal_candle_time,
        "entry_candle_time": t.entry_candle_time,
        "entry_price": t.entry_price,
        "stop_loss": t.initial_stop_loss,
        "initial_risk": t.initial_risk,
        "target": t.target_price,
        "target_r": TARGET_R,
        "mfe": getattr(t, "mfe", None),
        "mae": getattr(t, "mae", None),
        "mfe_r": getattr(t, "mfe_r", None),
        "mae_r": getattr(t, "mae_r", None),
        "exit_candle_time": t.exit_candle_time,
        "exit_time": t.exit_time,
        "exit_price": t.exit_price,
        "exit_reason": t.exit_reason,
        "same_candle_ambiguous": t.same_candle_ambiguous,
        "gross_pnl": t.gross_pnl,
        "costs": t.costs,
        "net_pnl": t.net_pnl,
    })

pd.DataFrame(rows).to_csv(OUTPUT_FILE, index=False)

print()
print(f"Saved: {OUTPUT_FILE}")
print()
print("VALID EXISTING ORB BASELINE FIXED-SL RESEARCH COMPLETED")
print("=" * 100)
