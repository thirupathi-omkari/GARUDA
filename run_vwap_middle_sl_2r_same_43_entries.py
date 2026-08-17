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
from indicators.vwap import calculate_vwap

DATA_FILE = PROJECT_ROOT / "data" / "raw" / "INFY_5MIN_REAL.csv"
LOCKED_ENTRY_FILE = PROJECT_ROOT / "data" / "orb_50pct_sl_2r_infy.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "vwap_middle_sl_2r_infy_same43_fixed.csv"

SYMBOL = "INFY"
TARGET_R = 2.0
COST_RATE_PCT = 0.10
SLIPPAGE_PCT = 0.05
EXPECTED_ENTRIES = 43


print()
print("=" * 100)
print("GARUDA — FIXED 43-ENTRY VWAP-MIDDLE SL + 2R RESEARCH")
print("=" * 100)

# ----------------------------------------------------------
# Load data
# ----------------------------------------------------------
if not DATA_FILE.exists():
    raise FileNotFoundError(DATA_FILE)

df = pd.read_csv(DATA_FILE)
required = {"datetime", "open", "high", "low", "close", "volume"}
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
for session_date, group in df.groupby(df["datetime"].dt.date):
    session = group.sort_values("datetime").reset_index(drop=True)
    if not session.empty:
        sessions.append(session)

sessions.sort(key=lambda x: x["datetime"].iloc[0])
print(f"Sessions : {len(sessions)}")

# ----------------------------------------------------------
# Hard-lock BE and trailing OFF in the exact simulator config
# ----------------------------------------------------------
exit_module.risk_config.break_even_enabled = False
exit_module.risk_config.trailing_stop_enabled = False

print()
print(f"BREAK-EVEN         : {exit_module.risk_config.break_even_enabled}")
print(f"TRAILING STOP      : {exit_module.risk_config.trailing_stop_enabled}")

if exit_module.risk_config.break_even_enabled:
    raise RuntimeError("RESEARCH CONFIG ERROR: break-even is not OFF.")
if exit_module.risk_config.trailing_stop_enabled:
    raise RuntimeError("RESEARCH CONFIG ERROR: trailing stop is not OFF.")

# ----------------------------------------------------------
# Freeze exact 43 signal/entry records
# ----------------------------------------------------------
if not LOCKED_ENTRY_FILE.exists():
    raise FileNotFoundError(LOCKED_ENTRY_FILE)

locked = pd.read_csv(LOCKED_ENTRY_FILE)

required_locked = {
    "trade_date",
    "direction",
    "signal_candle_time",
    "entry_candle_time",
}
missing_locked = required_locked - set(locked.columns)
if missing_locked:
    raise ValueError(
        f"Locked entry universe missing columns: {sorted(missing_locked)}"
    )

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
    session["datetime"].dt.date.iloc[0]: session
    for session in sessions
}

trades = []
invalid_risk = []

# ----------------------------------------------------------
# Replay exactly the same 43 entries
# ----------------------------------------------------------
for locked_index, row in locked.iterrows():

    trade_date = row["trade_date"]
    direction = str(row["direction"]).upper()
    signal_time = pd.Timestamp(row["signal_candle_time"])
    entry_time = pd.Timestamp(row["entry_candle_time"])

    if direction not in ("BUY", "SELL"):
        raise RuntimeError(
            f"Invalid direction at locked row {locked_index}: {direction}"
        )

    session = session_by_date.get(trade_date)
    if session is None:
        raise RuntimeError(f"Session missing for {trade_date}")

    signal_matches = session[session["datetime"] == signal_time]
    entry_matches = session[session["datetime"] == entry_time]

    if signal_matches.empty:
        raise RuntimeError(f"Signal candle not found: {signal_time}")
    if entry_matches.empty:
        raise RuntimeError(f"Entry candle not found: {entry_time}")

    signal_position = int(signal_matches.index[0])
    entry_position = int(entry_matches.index[0])

    signal_candle = session.iloc[signal_position]
    entry_candle = session.iloc[entry_position]

    # ------------------------------------------------------
    # VWAP is calculated from the full session using the
    # existing GARUDA VWAP implementation. We take the
    # VWAP value from the ENTRY candle, exactly as requested.
    # ------------------------------------------------------
    data_with_vwap = calculate_vwap(session)

    entry_vwap = float(
        data_with_vwap.iloc[entry_position]["vwap"]
    )

    raw_entry_price = float(entry_candle["open"])

    entry_price = apply_slippage(
        price=raw_entry_price,
        direction=direction,
        slippage_pct=SLIPPAGE_PCT,
        is_entry=True,
    )

    # ------------------------------------------------------
    # VWAP-MIDDLE STOP
    #
    # BUY  -> VWAP below entry
    # SELL -> VWAP above entry
    #
    # If VWAP is on the wrong side, the trade is invalid for
    # this SL hypothesis. We do NOT flip, buffer, or substitute
    # another stop.
    # ------------------------------------------------------
    if direction == "BUY":
        stop_loss = entry_vwap
        initial_risk = entry_price - stop_loss
    else:
        stop_loss = entry_vwap
        initial_risk = stop_loss - entry_price

    if not pd.notna(stop_loss) or initial_risk <= 0:
        invalid_risk.append(
            {
                "trade_index": locked_index,
                "trade_date": trade_date,
                "direction": direction,
                "signal_time": signal_time,
                "entry_time": entry_time,
                "entry_price": entry_price,
                "entry_vwap": entry_vwap,
                "initial_risk": initial_risk,
            }
        )
        continue

    # ------------------------------------------------------
    # 2R target
    # ------------------------------------------------------
    if direction == "BUY":
        target = entry_price + TARGET_R * initial_risk
    else:
        target = entry_price - TARGET_R * initial_risk

    trade = BacktestTrade(
        symbol=SYMBOL,
        strategy_name="ORB_VWAP_VWAP_MIDDLE_FIXED",
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

    future_candles = (
        session.iloc[entry_position:]
        .copy()
        .reset_index(drop=True)
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future_candles,
        stop_loss=stop_loss,
        target=target,
    )

    if trade is None or trade.exit_price is None:
        raise RuntimeError(
            f"No exit generated for {trade_date} {direction} {entry_time}"
        )

    # ------------------------------------------------------
    # Fixed-stop integrity check
    # ------------------------------------------------------
    if trade.exit_reason == "STOP_LOSS":
        if abs(float(trade.exit_price) - float(stop_loss)) > 1e-9:
            raise RuntimeError(
                "FIXED VWAP STOP INTEGRITY FAILURE: "
                f"date={trade_date}, direction={direction}, "
                f"exit={trade.exit_price}, initial_stop={stop_loss}"
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
    exit_matches = session[session["datetime"] == exit_time]

    if exit_matches.empty:
        distances = (session["datetime"] - exit_time).abs()
        exit_position = int(distances.argmin())
        exit_candle = session.iloc[exit_position]
    else:
        exit_position = int(exit_matches.index[0])
        exit_candle = session.iloc[exit_position]

    if direction == "BUY":
        sl_touched = float(exit_candle["low"]) <= stop_loss
        target_touched = float(exit_candle["high"]) >= target
    else:
        sl_touched = float(exit_candle["high"]) >= stop_loss
        target_touched = float(exit_candle["low"]) <= target

    trade.same_candle_ambiguous = sl_touched and target_touched

    # Audit fields
    trade.signal_candle_time = signal_time
    trade.signal_candle_open = float(signal_candle["open"])
    trade.signal_candle_high = float(signal_candle["high"])
    trade.signal_candle_low = float(signal_candle["low"])
    trade.signal_candle_close = float(signal_candle["close"])
    trade.signal_candle_vwap = float(
        data_with_vwap.iloc[signal_position]["vwap"]
    )

    trade.entry_candle_time = entry_time
    trade.entry_candle_open = float(entry_candle["open"])
    trade.entry_candle_high = float(entry_candle["high"])
    trade.entry_candle_low = float(entry_candle["low"])
    trade.entry_candle_close = float(entry_candle["close"])
    trade.entry_candle_vwap = entry_vwap

    trade.exit_candle_time = exit_time
    trade.exit_candle_open = float(exit_candle["open"])
    trade.exit_candle_high = float(exit_candle["high"])
    trade.exit_candle_low = float(exit_candle["low"])
    trade.exit_candle_close = float(exit_candle["close"])

    trades.append(trade)

# ----------------------------------------------------------
# Invalid-risk reporting
# ----------------------------------------------------------
if invalid_risk:
    print()
    print("=" * 100)
    print("VWAP-MIDDLE INVALID-RISK TRADES")
    print("=" * 100)
    print(f"INVALID RISK COUNT : {len(invalid_risk)}")
    print()
    for item in invalid_risk:
        print(
            f"{item['trade_date']} {item['direction']} "
            f"entry={item['entry_price']:.5f} "
            f"vwap={item['entry_vwap']:.5f} "
            f"risk={item['initial_risk']:.5f}"
        )
    print("=" * 100)

# For an apples-to-apples comparison, every locked entry must
# produce a valid VWAP stop. We do not silently drop trades.
if invalid_risk:
    raise RuntimeError(
        "VWAP-MIDDLE TEST INVALID: "
        f"{len(invalid_risk)} of {EXPECTED_ENTRIES} locked entries "
        "have non-positive/invalid initial risk. "
        "No performance result will be accepted."
    )

if len(trades) != EXPECTED_ENTRIES:
    raise RuntimeError(
        "FINAL LOCKED ENTRY COUNT FAILURE: "
        f"expected {EXPECTED_ENTRIES}, got {len(trades)}"
    )

print()
print(
    f"FINAL LOCKED ENTRY COUNT : {len(trades)} / {EXPECTED_ENTRIES}"
)

# ----------------------------------------------------------
# Statistics
# ----------------------------------------------------------
total_trades = len(trades)

stop_loss_count = sum(
    trade.exit_reason == "STOP_LOSS" for trade in trades
)
target_count = sum(
    trade.exit_reason == "TARGET" for trade in trades
)
eod_count = sum(
    trade.exit_reason == "END_OF_DAY" for trade in trades
)

winning_count = sum(
    trade.net_pnl > 0 for trade in trades
)
losing_count = sum(
    trade.net_pnl < 0 for trade in trades
)

total_pnl = sum(
    trade.net_pnl for trade in trades
)
avg_pnl = total_pnl / total_trades

gross_profit = sum(
    trade.net_pnl for trade in trades if trade.net_pnl > 0
)
gross_loss = abs(
    sum(
        trade.net_pnl for trade in trades if trade.net_pnl < 0
    )
)

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else float("inf")
)

win_rate = winning_count / total_trades * 100

ambiguous_count = sum(
    bool(trade.same_candle_ambiguous) for trade in trades
)

mfe = pd.Series(
    [
        float(trade.mfe_r)
        for trade in trades
        if getattr(trade, "mfe_r", None) is not None
        and not pd.isna(trade.mfe_r)
    ],
    dtype=float,
)

mae = pd.Series(
    [
        float(trade.mae_r)
        for trade in trades
        if getattr(trade, "mae_r", None) is not None
        and not pd.isna(trade.mae_r)
    ],
    dtype=float,
)

print()
print("=" * 110)
print("VALID VWAP-MIDDLE SL + 2R RESULTS")
print("=" * 110)
print(f"TRADES             : {total_trades}")
print(f"STOP_LOSS          : {stop_loss_count}")
print(f"TARGET             : {target_count}")
print(f"END_OF_DAY         : {eod_count}")
print(f"WINNING_TRADES     : {winning_count}")
print(f"LOSING_TRADES      : {losing_count}")
print(f"WIN_RATE_PCT       : {win_rate:.2f}")
print(f"AVG_PNL            : {avg_pnl:.2f}")
print(f"TOTAL_PNL          : {total_pnl:.2f}")
print(f"PROFIT_FACTOR      : {profit_factor:.3f}")
print(f"AMBIGUOUS_CANDLES  : {ambiguous_count}")
print(f"AVG_MFE_R          : {mfe.mean():.3f}")
print(f"MEDIAN_MFE_R       : {mfe.median():.3f}")
print(f"P75_MFE_R          : {mfe.quantile(.75):.3f}")
print(f"P90_MFE_R          : {mfe.quantile(.90):.3f}")
print(f"AVG_MAE_R          : {mae.mean():.3f}")
print(f"MEDIAN_MAE_R       : {mae.median():.3f}")
print(f"P75_MAE_R          : {mae.quantile(.75):.3f}")
print(f"P90_MAE_R          : {mae.quantile(.90):.3f}")
print("=" * 110)

# ----------------------------------------------------------
# Trade audit
# ----------------------------------------------------------
print()
print("=" * 180)
print("FIXED 43-ENTRY VWAP-MIDDLE TRADE AUDIT")
print("=" * 180)

print(
    f"{'DATE':<12}"
    f"{'SIDE':<6}"
    f"{'SIGNAL':<22}"
    f"{'ENTRY':<22}"
    f"{'EXIT':<22}"
    f"{'ENTRY_PX':>11}"
    f"{'VWAP_SL':>11}"
    f"{'RISK':>10}"
    f"{'TARGET':>11}"
    f"{'MFE_R':>9}"
    f"{'MAE_R':>9}"
    f"{'REASON':<15}"
    f"{'AMBIG':<7}"
    f"{'PNL':>10}"
)

print("-" * 180)

for trade in trades:
    print(
        f"{str(trade.trade_date):<12}"
        f"{trade.direction:<6}"
        f"{str(trade.signal_candle_time):<22}"
        f"{str(trade.entry_time):<22}"
        f"{str(trade.exit_time):<22}"
        f"{trade.entry_price:>11.2f}"
        f"{trade.initial_stop_loss:>11.2f}"
        f"{trade.initial_risk:>10.2f}"
        f"{trade.target_price:>11.2f}"
        f"{trade.mfe_r:>9.3f}"
        f"{trade.mae_r:>9.3f}"
        f"{trade.exit_reason:<15}"
        f"{str(trade.same_candle_ambiguous):<7}"
        f"{trade.net_pnl:>10.2f}"
    )

# ----------------------------------------------------------
# Save
# ----------------------------------------------------------
rows = []

for trade in trades:
    rows.append(
        {
            "trade_date": trade.trade_date,
            "direction": trade.direction,
            "signal_candle_time": trade.signal_candle_time,
            "signal_candle_open": trade.signal_candle_open,
            "signal_candle_high": trade.signal_candle_high,
            "signal_candle_low": trade.signal_candle_low,
            "signal_candle_close": trade.signal_candle_close,
            "signal_candle_vwap": trade.signal_candle_vwap,
            "entry_candle_time": trade.entry_candle_time,
            "entry_candle_open": trade.entry_candle_open,
            "entry_candle_high": trade.entry_candle_high,
            "entry_candle_low": trade.entry_candle_low,
            "entry_candle_close": trade.entry_candle_close,
            "entry_candle_vwap": trade.entry_candle_vwap,
            "entry_time": trade.entry_time,
            "entry_price": trade.entry_price,
            "stop_loss": trade.initial_stop_loss,
            "initial_risk": trade.initial_risk,
            "target": trade.target_price,
            "target_r": TARGET_R,
            "mfe": getattr(trade, "mfe", None),
            "mae": getattr(trade, "mae", None),
            "mfe_r": getattr(trade, "mfe_r", None),
            "mae_r": getattr(trade, "mae_r", None),
            "exit_candle_time": trade.exit_candle_time,
            "exit_candle_open": trade.exit_candle_open,
            "exit_candle_high": trade.exit_candle_high,
            "exit_candle_low": trade.exit_candle_low,
            "exit_candle_close": trade.exit_candle_close,
            "exit_time": trade.exit_time,
            "exit_price": trade.exit_price,
            "exit_reason": trade.exit_reason,
            "same_candle_ambiguous": trade.same_candle_ambiguous,
            "gross_pnl": trade.gross_pnl,
            "costs": trade.costs,
            "net_pnl": trade.net_pnl,
        }
    )

pd.DataFrame(rows).to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print(f"Saved: {OUTPUT_FILE}")
print()
print("VALID VWAP-MIDDLE FIXED-SL RESEARCH COMPLETED")
print("=" * 100)
