import sys
from pathlib import Path

import pandas as pd


# ==========================================================
# PROJECT PATH
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


# ==========================================================
# GARUDA MODULES
# ==========================================================

from backtesting.backtest_trade import BacktestTrade

from backtesting.exit_simulator import (
    simulate_trade_exit,
)

import backtesting.exit_simulator as exit_module

from backtesting.pnl_calculator import (
    calculate_trade_pnl,
)

from backtesting.slippage import (
    apply_slippage,
)

from indicators.vwap import (
    calculate_vwap,
)

from strategy.session_utils import (
    get_opening_range_data,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

# This file was produced by the original research runner and
# contains the exact 43 ORB+VWAP signal/entry records.
LOCKED_ENTRY_FILE = (
    PROJECT_ROOT
    / "data"
    / "orb_50pct_sl_2r_infy.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "orb_50pct_sl_2r_infy_same43_fixed.csv"
)

SYMBOL = "INFY"

TARGET_R = 2.0
COST_RATE_PCT = 0.10
SLIPPAGE_PCT = 0.05

OPENING_START_TIME = "09:15"
OPENING_END_TIME = "09:30"

EXPECTED_ENTRIES = 43


# ==========================================================
# HEADER
# ==========================================================

print()
print("=" * 100)
print(
    "GARUDA — FIXED 43-ENTRY 50% ORB-RANGE SL + 2R RESEARCH"
)
print("=" * 100)


# ==========================================================
# LOAD MARKET DATA
# ==========================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Market data file not found: {DATA_FILE}"
    )

df = pd.read_csv(DATA_FILE)

required_columns = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
}

missing_columns = (
    required_columns - set(df.columns)
)

if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

df["datetime"] = pd.to_datetime(df["datetime"])

df = (
    df
    .sort_values("datetime")
    .reset_index(drop=True)
)

print(f"Data file : {DATA_FILE}")
print(f"Rows     : {len(df)}")
print(f"From     : {df['datetime'].iloc[0]}")
print(f"To       : {df['datetime'].iloc[-1]}")


# ==========================================================
# PREPARE SESSIONS
# ==========================================================

sessions = []

for session_date, group in df.groupby(
    df["datetime"].dt.date
):

    session = (
        group
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    if not session.empty:
        sessions.append(session)

sessions.sort(
    key=lambda x: x["datetime"].iloc[0]
)

print(f"Sessions : {len(sessions)}")


# ==========================================================
# LOCK EXIT MANAGEMENT
#
# The existing exit simulator owns the RiskConfig instance
# used for break-even and trailing-stop updates. We modify
# THAT exact instance.
# ==========================================================

exit_module.risk_config.break_even_enabled = False
exit_module.risk_config.trailing_stop_enabled = False

print()
print(
    "BREAK-EVEN         : "
    f"{exit_module.risk_config.break_even_enabled}"
)

print(
    "TRAILING STOP      : "
    f"{exit_module.risk_config.trailing_stop_enabled}"
)

if exit_module.risk_config.break_even_enabled:
    raise RuntimeError(
        "RESEARCH CONFIG ERROR: break-even is not OFF."
    )

if exit_module.risk_config.trailing_stop_enabled:
    raise RuntimeError(
        "RESEARCH CONFIG ERROR: trailing stop is not OFF."
    )


# ==========================================================
# LOAD LOCKED 43-ENTRY UNIVERSE
#
# IMPORTANT:
# We do NOT rescan signals while changing the SL.
#
# If signal generation and exit scanning are coupled, changing
# the exit can change the next signal that gets selected.
# That would invalidate an apples-to-apples SL comparison.
#
# Therefore the exact signal/entry universe is frozen here.
# ==========================================================

if not LOCKED_ENTRY_FILE.exists():
    raise FileNotFoundError(
        "Locked entry universe not found: "
        f"{LOCKED_ENTRY_FILE}"
    )

locked = pd.read_csv(
    LOCKED_ENTRY_FILE
)

required_locked_columns = {
    "trade_date",
    "direction",
    "signal_candle_time",
    "entry_candle_time",
}

missing_locked = (
    required_locked_columns
    - set(locked.columns)
)

if missing_locked:
    raise ValueError(
        "Locked entry universe is missing columns: "
        f"{sorted(missing_locked)}"
    )

if len(locked) != EXPECTED_ENTRIES:
    raise RuntimeError(
        "LOCKED ENTRY UNIVERSE MISMATCH: "
        f"expected {EXPECTED_ENTRIES}, got {len(locked)}"
    )

locked["trade_date"] = pd.to_datetime(
    locked["trade_date"]
).dt.date

locked["signal_candle_time"] = pd.to_datetime(
    locked["signal_candle_time"]
)

locked["entry_candle_time"] = pd.to_datetime(
    locked["entry_candle_time"]
)

print()
print(
    "LOCKED ENTRY UNIVERSE : "
    f"{len(locked)} entries"
)
print(
    "Entry source          : "
    f"{LOCKED_ENTRY_FILE}"
)


# ==========================================================
# SESSION LOOKUP
# ==========================================================

session_by_date = {
    session["datetime"].dt.date.iloc[0]: session
    for session in sessions
}


# ==========================================================
# REPLAY EXACT SAME 43 ENTRIES
# ==========================================================

trades = []

for locked_index, locked_entry in locked.iterrows():

    trade_date = locked_entry["trade_date"]

    direction = str(
        locked_entry["direction"]
    ).upper()

    signal_time = pd.Timestamp(
        locked_entry["signal_candle_time"]
    )

    entry_time = pd.Timestamp(
        locked_entry["entry_candle_time"]
    )

    if direction not in ("BUY", "SELL"):
        raise RuntimeError(
            f"Invalid direction at locked row "
            f"{locked_index}: {direction}"
        )

    session = session_by_date.get(
        trade_date
    )

    if session is None:
        raise RuntimeError(
            f"Locked entry session not found: {trade_date}"
        )

    signal_matches = session[
        session["datetime"] == signal_time
    ]

    entry_matches = session[
        session["datetime"] == entry_time
    ]

    if signal_matches.empty:
        raise RuntimeError(
            "Locked signal candle not found: "
            f"{signal_time}"
        )

    if entry_matches.empty:
        raise RuntimeError(
            "Locked entry candle not found: "
            f"{entry_time}"
        )

    signal_position = int(
        signal_matches.index[0]
    )

    entry_position = int(
        entry_matches.index[0]
    )

    signal_candle = session.iloc[
        signal_position
    ]

    entry_candle = session.iloc[
        entry_position
    ]


    # ------------------------------------------------------
    # Recompute ORB from raw market data.
    # ------------------------------------------------------

    opening_data = get_opening_range_data(
        session_data=session,
        start_time=OPENING_START_TIME,
        end_time=OPENING_END_TIME,
    )

    if opening_data is None or opening_data.empty:
        raise RuntimeError(
            f"Opening range unavailable: {trade_date}"
        )

    opening_high = float(
        opening_data["high"].max()
    )

    opening_low = float(
        opening_data["low"].min()
    )

    opening_range = (
        opening_high - opening_low
    )

    half_orb_range = (
        opening_range * 0.50
    )


    # ------------------------------------------------------
    # Entry
    #
    # Use the exact locked entry candle and the existing
    # GARUDA adverse-slippage implementation.
    # ------------------------------------------------------

    raw_entry_price = float(
        entry_candle["open"]
    )

    entry_price = apply_slippage(
        price=raw_entry_price,
        direction=direction,
        slippage_pct=SLIPPAGE_PCT,
        is_entry=True,
    )


    # ------------------------------------------------------
    # 50% ORB SL
    # ------------------------------------------------------

    if direction == "BUY":

        stop_loss = (
            entry_price
            - half_orb_range
        )

        initial_risk = (
            entry_price
            - stop_loss
        )

    else:

        stop_loss = (
            entry_price
            + half_orb_range
        )

        initial_risk = (
            stop_loss
            - entry_price
        )

    if initial_risk <= 0:
        raise RuntimeError(
            "Invalid initial risk: "
            f"{trade_date} {direction} {entry_time}"
        )


    # ------------------------------------------------------
    # Dynamic 2R target from actual initial risk
    # ------------------------------------------------------

    if direction == "BUY":

        target = (
            entry_price
            + TARGET_R * initial_risk
        )

    else:

        target = (
            entry_price
            - TARGET_R * initial_risk
        )


    # ------------------------------------------------------
    # Create GARUDA BacktestTrade
    # ------------------------------------------------------

    trade = BacktestTrade(
        symbol=SYMBOL,
        strategy_name=(
            "ORB_VWAP_50PCT_ORB_FIXED"
        ),
        trade_date=trade_date,
        direction=direction,
        entry_time=entry_time,
        entry_price=entry_price,
        quantity=1,
    )

    trade.initial_stop_loss = (
        stop_loss
    )

    trade.initial_risk = (
        initial_risk
    )

    trade.target_price = (
        target
    )

    trade.target_r = (
        TARGET_R
    )


    # ------------------------------------------------------
    # Entry candle is included because position exists from
    # its open.
    # ------------------------------------------------------

    future_candles = (
        session
        .iloc[entry_position:]
        .copy()
        .reset_index(drop=True)
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future_candles,
        stop_loss=stop_loss,
        target=target,
    )

    if trade is None:
        raise RuntimeError(
            f"No exit generated: "
            f"{trade_date} {direction} {entry_time}"
        )

    if trade.exit_price is None:
        raise RuntimeError(
            f"Exit price missing: "
            f"{trade_date} {direction} {entry_time}"
        )


    # ------------------------------------------------------
    # FIXED-STOP INTEGRITY
    #
    # With BE and trailing OFF, a STOP_LOSS must be exactly
    # the original 50% ORB stop BEFORE exit slippage.
    # ------------------------------------------------------

    if trade.exit_reason == "STOP_LOSS":

        if abs(
            float(trade.exit_price)
            - float(stop_loss)
        ) > 1e-9:

            raise RuntimeError(
                "FIXED STOP INTEGRITY FAILURE: "
                f"date={trade_date}, "
                f"direction={direction}, "
                f"exit={trade.exit_price}, "
                f"initial_stop={stop_loss}"
            )


    # ------------------------------------------------------
    # Exit slippage
    # ------------------------------------------------------

    trade.exit_price = apply_slippage(
        price=float(trade.exit_price),
        direction=direction,
        slippage_pct=SLIPPAGE_PCT,
        is_entry=False,
    )


    # ------------------------------------------------------
    # Final P&L
    # ------------------------------------------------------

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=COST_RATE_PCT,
    )


    # ------------------------------------------------------
    # Exit candle audit
    # ------------------------------------------------------

    exit_time = pd.Timestamp(
        trade.exit_time
    )

    exit_matches = session[
        session["datetime"] == exit_time
    ]

    if exit_matches.empty:

        distances = (
            session["datetime"]
            - exit_time
        ).abs()

        exit_position = int(
            distances.argmin()
        )

        exit_candle = session.iloc[
            exit_position
        ]

    else:

        exit_position = int(
            exit_matches.index[0]
        )

        exit_candle = session.iloc[
            exit_position
        ]


    if direction == "BUY":

        sl_touched = (
            float(exit_candle["low"])
            <= stop_loss
        )

        target_touched = (
            float(exit_candle["high"])
            >= target
        )

    else:

        sl_touched = (
            float(exit_candle["high"])
            >= stop_loss
        )

        target_touched = (
            float(exit_candle["low"])
            <= target
        )

    trade.same_candle_ambiguous = (
        sl_touched
        and target_touched
    )


    # ------------------------------------------------------
    # Audit fields
    # ------------------------------------------------------

    trade.signal_candle_time = (
        signal_time
    )

    trade.signal_candle_open = float(
        signal_candle["open"]
    )

    trade.signal_candle_high = float(
        signal_candle["high"]
    )

    trade.signal_candle_low = float(
        signal_candle["low"]
    )

    trade.signal_candle_close = float(
        signal_candle["close"]
    )

    # Calculate VWAP only for audit/reporting.
    data_with_vwap = calculate_vwap(
        session
    )

    trade.signal_candle_vwap = float(
        data_with_vwap.iloc[
            signal_position
        ]["vwap"]
    )

    trade.entry_candle_time = (
        entry_time
    )

    trade.entry_candle_open = float(
        entry_candle["open"]
    )

    trade.entry_candle_high = float(
        entry_candle["high"]
    )

    trade.entry_candle_low = float(
        entry_candle["low"]
    )

    trade.entry_candle_close = float(
        entry_candle["close"]
    )

    trade.exit_candle_time = exit_time

    trade.exit_candle_open = float(
        exit_candle["open"]
    )

    trade.exit_candle_high = float(
        exit_candle["high"]
    )

    trade.exit_candle_low = float(
        exit_candle["low"]
    )

    trade.exit_candle_close = float(
        exit_candle["close"]
    )

    trades.append(trade)


# ==========================================================
# FINAL LOCK CHECK
# ==========================================================

if len(trades) != EXPECTED_ENTRIES:
    raise RuntimeError(
        "FINAL LOCKED ENTRY COUNT FAILURE: "
        f"expected {EXPECTED_ENTRIES}, "
        f"got {len(trades)}"
    )

print()
print(
    "FINAL LOCKED ENTRY COUNT : "
    f"{len(trades)} / {EXPECTED_ENTRIES}"
)


# ==========================================================
# STATISTICS
# ==========================================================

total_trades = len(trades)

stop_loss_count = sum(
    trade.exit_reason == "STOP_LOSS"
    for trade in trades
)

target_count = sum(
    trade.exit_reason == "TARGET"
    for trade in trades
)

eod_count = sum(
    trade.exit_reason == "END_OF_DAY"
    for trade in trades
)

winning_count = sum(
    trade.net_pnl > 0
    for trade in trades
)

losing_count = sum(
    trade.net_pnl < 0
    for trade in trades
)

total_pnl = sum(
    trade.net_pnl
    for trade in trades
)

avg_pnl = (
    total_pnl / total_trades
)

gross_profit = sum(
    trade.net_pnl
    for trade in trades
    if trade.net_pnl > 0
)

gross_loss = abs(
    sum(
        trade.net_pnl
        for trade in trades
        if trade.net_pnl < 0
    )
)

profit_factor = (
    gross_profit / gross_loss
    if gross_loss > 0
    else float("inf")
)

win_rate = (
    winning_count
    / total_trades
    * 100
)

ambiguous_count = sum(
    bool(trade.same_candle_ambiguous)
    for trade in trades
)

mfe_r_values = [
    float(trade.mfe_r)
    for trade in trades
    if getattr(trade, "mfe_r", None) is not None
    and not pd.isna(trade.mfe_r)
]

mae_r_values = [
    float(trade.mae_r)
    for trade in trades
    if getattr(trade, "mae_r", None) is not None
    and not pd.isna(trade.mae_r)
]

mfe_series = pd.Series(
    mfe_r_values,
    dtype=float,
)

mae_series = pd.Series(
    mae_r_values,
    dtype=float,
)


# ==========================================================
# SUMMARY
# ==========================================================

print()
print("=" * 110)
print(
    "VALID 50% ORB-RANGE SL + 2R RESULTS"
)
print("=" * 110)

print(
    f"TRADES             : {total_trades}"
)

print(
    f"STOP_LOSS          : {stop_loss_count}"
)

print(
    f"TARGET             : {target_count}"
)

print(
    f"END_OF_DAY         : {eod_count}"
)

print(
    f"WINNING_TRADES     : {winning_count}"
)

print(
    f"LOSING_TRADES      : {losing_count}"
)

print(
    f"WIN_RATE_PCT       : {win_rate:.2f}"
)

print(
    f"AVG_PNL            : {avg_pnl:.2f}"
)

print(
    f"TOTAL_PNL          : {total_pnl:.2f}"
)

print(
    f"PROFIT_FACTOR      : {profit_factor:.3f}"
)

print(
    f"AMBIGUOUS_CANDLES  : {ambiguous_count}"
)

print(
    f"AVG_MFE_R          : {mfe_series.mean():.3f}"
)

print(
    f"MEDIAN_MFE_R       : {mfe_series.median():.3f}"
)

print(
    f"P75_MFE_R          : {mfe_series.quantile(.75):.3f}"
)

print(
    f"P90_MFE_R          : {mfe_series.quantile(.90):.3f}"
)

print(
    f"AVG_MAE_R          : {mae_series.mean():.3f}"
)

print(
    f"MEDIAN_MAE_R       : {mae_series.median():.3f}"
)

print(
    f"P75_MAE_R          : {mae_series.quantile(.75):.3f}"
)

print(
    f"P90_MAE_R          : {mae_series.quantile(.90):.3f}"
)

print("=" * 110)


# ==========================================================
# TRADE AUDIT
# ==========================================================

print()
print("=" * 180)
print("FIXED 43-ENTRY TRADE AUDIT")
print("=" * 180)

print(
    f"{'DATE':<12}"
    f"{'SIDE':<6}"
    f"{'SIGNAL':<22}"
    f"{'ENTRY':<22}"
    f"{'EXIT':<22}"
    f"{'ENTRY_PX':>11}"
    f"{'SL':>11}"
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


# ==========================================================
# SAVE CSV
# ==========================================================

rows = []

for trade in trades:

    rows.append(
        {
            "trade_date":
                trade.trade_date,

            "direction":
                trade.direction,

            "signal_candle_time":
                trade.signal_candle_time,

            "signal_candle_open":
                trade.signal_candle_open,

            "signal_candle_high":
                trade.signal_candle_high,

            "signal_candle_low":
                trade.signal_candle_low,

            "signal_candle_close":
                trade.signal_candle_close,

            "signal_candle_vwap":
                trade.signal_candle_vwap,

            "entry_candle_time":
                trade.entry_candle_time,

            "entry_candle_open":
                trade.entry_candle_open,

            "entry_candle_high":
                trade.entry_candle_high,

            "entry_candle_low":
                trade.entry_candle_low,

            "entry_candle_close":
                trade.entry_candle_close,

            "entry_time":
                trade.entry_time,

            "entry_price":
                trade.entry_price,

            "stop_loss":
                trade.initial_stop_loss,

            "initial_risk":
                trade.initial_risk,

            "target":
                trade.target_price,

            "target_r":
                TARGET_R,

            "mfe":
                getattr(trade, "mfe", None),

            "mae":
                getattr(trade, "mae", None),

            "mfe_r":
                getattr(trade, "mfe_r", None),

            "mae_r":
                getattr(trade, "mae_r", None),

            "exit_candle_time":
                trade.exit_candle_time,

            "exit_candle_open":
                trade.exit_candle_open,

            "exit_candle_high":
                trade.exit_candle_high,

            "exit_candle_low":
                trade.exit_candle_low,

            "exit_candle_close":
                trade.exit_candle_close,

            "exit_time":
                trade.exit_time,

            "exit_price":
                trade.exit_price,

            "exit_reason":
                trade.exit_reason,

            "same_candle_ambiguous":
                trade.same_candle_ambiguous,

            "gross_pnl":
                trade.gross_pnl,

            "costs":
                trade.costs,

            "net_pnl":
                trade.net_pnl,
        }
    )

results_df = pd.DataFrame(rows)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print(
    f"Saved: {OUTPUT_FILE}"
)

print()
print(
    "VALID 50% ORB FIXED-SL RESEARCH COMPLETED"
)

print("=" * 100)
