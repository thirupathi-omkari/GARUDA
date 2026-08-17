import sys
from pathlib import Path
from datetime import date

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

from backtesting.backtest_trade import (
    BacktestTrade,
)

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

SYMBOL = "INFY"

TARGET_R = 2.0

COST_RATE_PCT = 0.10

SLIPPAGE_PCT = 0.05

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "orb_50pct_sl_2r_infy_fixed.csv"
)

OPENING_START_TIME = "09:15"

OPENING_END_TIME = "09:30"


# ==========================================================
# LOAD DATA
# ==========================================================

print()
print("=" * 80)
print("GARUDA — 50% ORB-RANGE SL + 2R RESEARCH")
print("=" * 80)

print()
print(f"Data file : {DATA_FILE}")

if not DATA_FILE.exists():

    raise FileNotFoundError(
        f"Market data file not found: {DATA_FILE}"
    )


df = pd.read_csv(
    DATA_FILE
)

required_columns = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
}

missing_columns = (
    required_columns
    - set(df.columns)
)

if missing_columns:

    raise ValueError(
        "Missing required columns: "
        f"{sorted(missing_columns)}"
    )


df["datetime"] = pd.to_datetime(
    df["datetime"]
)

df = (
    df
    .sort_values("datetime")
    .reset_index(drop=True)
)


print(
    f"Rows     : {len(df)}"
)

print(
    f"From     : {df['datetime'].iloc[0]}"
)

print(
    f"To       : {df['datetime'].iloc[-1]}"
)


# ==========================================================
# PREPARE DAILY SESSIONS
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

        sessions.append(
            session
        )


sessions.sort(
    key=lambda x:
        x["datetime"].iloc[0]
)


print(
    f"Sessions : {len(sessions)}"
)

print("=" * 80)


# ==========================================================
# LOCKED RESEARCH EXIT CONFIGURATION
#
# This experiment is fixed-SL only:
#   - Break-even OFF
#   - Trailing OFF
#
# We modify the SAME risk_config instance used by
# backtesting.exit_simulator, not a separate RiskConfig.
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
        "RESEARCH CONFIG ERROR: break-even must be OFF."
    )

if exit_module.risk_config.trailing_stop_enabled:
    raise RuntimeError(
        "RESEARCH CONFIG ERROR: trailing stop must be OFF."
    )

# ==========================================================
# TRADE COLLECTION
# ==========================================================

trades = []

invalid_risk_count = 0

no_entry_candle_count = 0

ambiguous_count = 0


# ==========================================================
# PROCESS EACH SESSION
# ==========================================================

for session in sessions:

    if len(session) < 5:
        continue


    # ------------------------------------------------------
    # VWAP
    #
    # Use GARUDA's actual VWAP implementation.
    # ------------------------------------------------------

    data_with_vwap = (
        calculate_vwap(session)
    )

    if (
        data_with_vwap is None
        or data_with_vwap.empty
    ):
        continue


    # ------------------------------------------------------
    # ORB
    #
    # GARUDA's opening range is:
    #
    # 09:15
    # 09:20
    # 09:25
    #
    # 09:30 is excluded because end_time is exclusive.
    # ------------------------------------------------------

    opening_data = (
        get_opening_range_data(
            session_data=session,
            start_time=(
                OPENING_START_TIME
            ),
            end_time=(
                OPENING_END_TIME
            ),
        )
    )

    if (
        opening_data is None
        or opening_data.empty
    ):
        continue


    opening_high = float(
        opening_data["high"].max()
    )

    opening_low = float(
        opening_data["low"].min()
    )


    opening_last_time = (
        opening_data["datetime"].iloc[-1]
    )


    # ------------------------------------------------------
    # FIND FIRST POST-ORB CANDLE
    # ------------------------------------------------------

    post_orb_indices = (
        session.index[
            session["datetime"]
            > opening_last_time
        ]
        .tolist()
    )

    if not post_orb_indices:
        continue


    # ------------------------------------------------------
    # POSITION CONTROL
    #
    # We scan from the first post-ORB candle.
    #
    # After a trade closes, scanning resumes AFTER the
    # exit candle.
    #
    # Therefore only one position can be active.
    # ------------------------------------------------------

    scan_index = post_orb_indices[0]


    while (
        scan_index
        < len(session) - 1
    ):


        # ==================================================
        # SIGNAL CANDLE
        # ==================================================

        signal_candle = (
            data_with_vwap.iloc[
                scan_index
            ]
        )

        signal_time = (
            signal_candle["datetime"]
        )

        signal_close = float(
            signal_candle["close"]
        )

        signal_vwap = float(
            signal_candle["vwap"]
        )


        # ==================================================
        # PREVIOUS CANDLE STATE
        # ==================================================

        if scan_index > 0:

            previous_candle = (
                data_with_vwap.iloc[
                    scan_index - 1
                ]
            )

            previous_close = float(
                previous_candle["close"]
            )

            previous_vwap = float(
                previous_candle["vwap"]
            )

        else:

            previous_close = None

            previous_vwap = None


        # ==================================================
        # CURRENT CONFIRMATION
        # ==================================================

        current_long = (
            signal_close > opening_high
            and
            signal_close > signal_vwap
        )

        current_short = (
            signal_close < opening_low
            and
            signal_close < signal_vwap
        )


        # ==================================================
        # PREVIOUS CONFIRMATION
        #
        # This prevents repeated signals while price
        # simply remains above/below ORB + VWAP.
        # ==================================================

        previous_long = False

        previous_short = False

        if previous_close is not None:

            previous_long = (
                previous_close
                > opening_high
                and
                previous_close
                > previous_vwap
            )

            previous_short = (
                previous_close
                < opening_low
                and
                previous_close
                < previous_vwap
            )


        # ==================================================
        # NEW TRANSITION
        # ==================================================

        new_long_signal = (
            current_long
            and not previous_long
        )

        new_short_signal = (
            current_short
            and not previous_short
        )


        if not (
            new_long_signal
            or new_short_signal
        ):

            scan_index += 1

            continue


        # ==================================================
        # DIRECTION
        # ==================================================

        if new_long_signal:

            direction = "BUY"

        else:

            direction = "SELL"


        # ==================================================
        # ENTRY CANDLE
        #
        # Entry occurs at the NEXT candle OPEN.
        # ==================================================

        entry_index = (
            scan_index + 1
        )

        if (
            entry_index
            >= len(session)
        ):

            no_entry_candle_count += 1

            break


        entry_candle = (
            session.iloc[
                entry_index
            ]
        )


        # ==================================================
        # RAW ENTRY
        # ==================================================

        raw_entry_price = float(
            entry_candle["open"]
        )


        # ==================================================
        # ENTRY SLIPPAGE
        #
        # Same GARUDA slippage implementation.
        # ==================================================

        entry_price = apply_slippage(
            price=raw_entry_price,
            direction=direction,
            slippage_pct=SLIPPAGE_PCT,
            is_entry=True,
        )


        # ==================================================
        # 50% ORB-RANGE STOP
        #
        # LONG:
        #     SL = entry - 50% of ORB range
        #
        # SHORT:
        #     SL = entry + 50% of ORB range
        #
        # IMPORTANT:
        # Entry logic is unchanged. The stop is the only
        # research variable changed from the source runner.
        # ==================================================

        opening_range = (
            opening_high
            - opening_low
        )

        half_orb_range = (
            0.50 * opening_range
        )

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


        # ==================================================
        # INVALID RISK
        #
        # If entry opens at or beyond the structural SL,
        # there is no valid positive-risk trade.
        # ==================================================

        if initial_risk <= 0:

            invalid_risk_count += 1

            scan_index += 1

            continue


        # ==================================================
        # TARGET = 2R
        # ==================================================

        if direction == "BUY":

            target = (
                entry_price
                + (
                    TARGET_R
                    * initial_risk
                )
            )

        else:

            target = (
                entry_price
                - (
                    TARGET_R
                    * initial_risk
                )
            )


        # ==================================================
        # CREATE GARUDA BACKTEST TRADE DIRECTLY
        #
        # We deliberately do NOT use simulate_entry()
        # here because this is a research-only structural
        # stop experiment and the stop/target are determined
        # after the actual slipped entry price.
        # ==================================================

        trade = BacktestTrade(
            symbol=SYMBOL,
            strategy_name="ORB_VWAP",
            trade_date=(
                entry_candle["datetime"].date()
            ),
            direction=direction,
            entry_time=(
                entry_candle["datetime"]
            ),
            entry_price=entry_price,
            quantity=1,
        )


        # ==================================================
        # STORE RESEARCH LEVELS
        # ==================================================

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


        # ==================================================
        # FUTURE CANDLES
        #
        # IMPORTANT:
        #
        # Entry candle is included because the position
        # exists from its OPEN.
        # ==================================================

        future_candles = (
            session
            .iloc[entry_index:]
            .copy()
            .reset_index(drop=True)
        )


        if future_candles.empty:

            scan_index += 1

            continue


        # ==================================================
        # EXIT SIMULATION
        #
        # Use GARUDA's existing exit simulator.
        # ==================================================

        trade = simulate_trade_exit(
            trade=trade,
            future_candles=future_candles,
            stop_loss=stop_loss,
            target=target,
        )

        # --------------------------------------------------
        # FIXED-STOP INTEGRITY CHECK
        #
        # With BE/trailing OFF, a STOP_LOSS exit must occur
        # at the original structural SL before exit slippage.
        # --------------------------------------------------

        if (
            trade is not None
            and trade.exit_reason == "STOP_LOSS"
        ):
            if abs(
                float(trade.exit_price)
                - float(stop_loss)
            ) > 1e-9:
                raise RuntimeError(
                    "FIXED STOP INTEGRITY FAILURE: "
                    f"exit_price={trade.exit_price} "
                    f"!= initial_stop={stop_loss}. "
                    "The experiment is contaminated by dynamic "
                    "stop movement."
                )


        if trade is None:

            scan_index += 1

            continue


        # ==================================================
        # EXIT PRICE CHECK
        # ==================================================

        if trade.exit_price is None:

            scan_index += 1

            continue


        # ==================================================
        # EXIT SLIPPAGE
        # ==================================================

        raw_exit_price = float(
            trade.exit_price
        )

        trade.exit_price = (
            apply_slippage(
                price=raw_exit_price,
                direction=direction,
                slippage_pct=SLIPPAGE_PCT,
                is_entry=False,
            )
        )


        # ==================================================
        # FINAL P&L
        # ==================================================

        trade = calculate_trade_pnl(
            trade=trade,
            cost_rate_pct=COST_RATE_PCT,
        )


        # ==================================================
        # EXIT CANDLE
        # ==================================================

        exit_time = pd.Timestamp(
            trade.exit_time
        )

        exit_matches = session[
            session["datetime"]
            == exit_time
        ]


        if exit_matches.empty:

            time_difference = (
                session["datetime"]
                - exit_time
            ).abs()

            exit_position = int(
                time_difference.argmin()
            )

            exit_candle = (
                session.iloc[
                    exit_position
                ]
            )

        else:

            exit_position = int(
                exit_matches.index[0]
            )

            exit_candle = (
                session.iloc[
                    exit_position
                ]
            )


        # ==================================================
        # EXIT CANDLE OHLC
        # ==================================================

        exit_open = float(
            exit_candle["open"]
        )

        exit_high = float(
            exit_candle["high"]
        )

        exit_low = float(
            exit_candle["low"]
        )

        exit_close = float(
            exit_candle["close"]
        )


        # ==================================================
        # SAME-CANDLE AMBIGUITY
        #
        # For research reporting only.
        #
        # The actual GARUDA exit simulator determines
        # the official exit reason.
        # ==================================================

        if direction == "BUY":

            sl_touched = (
                exit_low
                <= stop_loss
            )

            target_touched = (
                exit_high
                >= target
            )

        else:

            sl_touched = (
                exit_high
                >= stop_loss
            )

            target_touched = (
                exit_low
                <= target
            )


        same_candle_ambiguous = (
            sl_touched
            and target_touched
        )


        if same_candle_ambiguous:

            ambiguous_count += 1


        # ==================================================
        # RESEARCH AUDIT ATTRIBUTES
        # ==================================================

        trade.signal_candle_time = (
            signal_time
        )

        trade.signal_candle_open = (
            float(
                signal_candle["open"]
            )
        )

        trade.signal_candle_high = (
            float(
                signal_candle["high"]
            )
        )

        trade.signal_candle_low = (
            float(
                signal_candle["low"]
            )
        )

        trade.signal_candle_close = (
            float(
                signal_candle["close"]
            )
        )

        trade.signal_candle_vwap = (
            signal_vwap
        )

        trade.entry_candle_time = (
            entry_candle["datetime"]
        )

        trade.entry_candle_open = (
            float(
                entry_candle["open"]
            )
        )

        trade.entry_candle_high = (
            float(
                entry_candle["high"]
            )
        )

        trade.entry_candle_low = (
            float(
                entry_candle["low"]
            )
        )

        trade.entry_candle_close = (
            float(
                entry_candle["close"]
            )
        )

        trade.exit_candle_time = (
            exit_candle["datetime"]
        )

        trade.exit_candle_open = (
            exit_open
        )

        trade.exit_candle_high = (
            exit_high
        )

        trade.exit_candle_low = (
            exit_low
        )

        trade.exit_candle_close = (
            exit_close
        )

        trade.same_candle_ambiguous = (
            same_candle_ambiguous
        )


        # ==================================================
        # STORE TRADE
        # ==================================================

        trades.append(
            trade
        )


        # ==================================================
        # RESUME SCANNING AFTER EXIT
        #
        # This is INSIDE the while loop.
        #
        # No overlapping positions.
        # ==================================================

        scan_index = (
            exit_position + 1
        )


# ==========================================================
# NO TRADES
# ==========================================================

if not trades:

    print()
    print(
        "NO VALID TRADES GENERATED."
    )

    print(
        f"Invalid risk setups : "
        f"{invalid_risk_count}"
    )

    raise SystemExit(0)


# ==========================================================
# LOCKED TRADE-UNIVERSE CHECK
# ==========================================================

if len(trades) != 61:
    raise RuntimeError(
        "LOCKED TRADE UNIVERSE MISMATCH: "
        f"expected 61 trades, got {len(trades)}. "
        "No result will be accepted as the 50% ORB comparison."
    )

print()
print("LOCKED TRADE UNIVERSE VERIFIED: 61 trades")

# ==========================================================
# STATISTICS
# ==========================================================

total_trades = len(
    trades
)

stop_loss_count = sum(
    trade.exit_reason
    == "STOP_LOSS"
    for trade in trades
)

target_count = sum(
    trade.exit_reason
    == "TARGET"
    for trade in trades
)

eod_count = sum(
    trade.exit_reason
    == "END_OF_DAY"
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
    total_pnl
    / total_trades
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


mfe_values = [
    float(trade.mfe_r)
    for trade in trades
    if getattr(
        trade,
        "mfe_r",
        None,
    ) is not None
    and not pd.isna(
        trade.mfe_r
    )
]


mae_values = [
    float(trade.mae_r)
    for trade in trades
    if getattr(
        trade,
        "mae_r",
        None,
    ) is not None
    and not pd.isna(
        trade.mae_r
    )
]


def percentage(
    numerator,
    denominator,
):

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100.0
    )


mfe_series = (
    pd.Series(mfe_values)
    if mfe_values
    else pd.Series(
        dtype=float
    )
)

mae_series = (
    pd.Series(mae_values)
    if mae_values
    else pd.Series(
        dtype=float
    )
)


# ==========================================================
# SUMMARY
# ==========================================================

print()
print("=" * 110)
print(
    "NEW ORB/VWAP TRANSITION + "
    "STRUCTURAL SL + 2R RESULTS"
)
print("=" * 110)

print(
    f"TRADES             : "
    f"{total_trades}"
)

print(
    f"STOP_LOSS          : "
    f"{stop_loss_count}"
)

print(
    f"TARGET             : "
    f"{target_count}"
)

print(
    f"END_OF_DAY         : "
    f"{eod_count}"
)

print(
    f"WINNING_TRADES     : "
    f"{winning_count}"
)

print(
    f"LOSING_TRADES      : "
    f"{losing_count}"
)

print(
    f"WIN_RATE_PCT       : "
    f"{percentage(winning_count, total_trades):.2f}"
)

print(
    f"AVG_PNL            : "
    f"{avg_pnl:.2f}"
)

print(
    f"TOTAL_PNL          : "
    f"{total_pnl:.2f}"
)

print(
    f"PROFIT_FACTOR      : "
    f"{profit_factor:.3f}"
)

print(
    f"AMBIGUOUS_CANDLES  : "
    f"{ambiguous_count}"
)

print(
    f"INVALID_RISK       : "
    f"{invalid_risk_count}"
)

print(
    f"AVG_MFE_R          : "
    f"{mfe_series.mean():.3f}"
)

print(
    f"MEDIAN_MFE_R       : "
    f"{mfe_series.median():.3f}"
)

print(
    f"P75_MFE_R          : "
    f"{mfe_series.quantile(.75):.3f}"
)

print(
    f"P90_MFE_R          : "
    f"{mfe_series.quantile(.90):.3f}"
)

print(
    f"AVG_MAE_R          : "
    f"{mae_series.mean():.3f}"
)

print(
    f"MEDIAN_MAE_R       : "
    f"{mae_series.median():.3f}"
)

print(
    f"P75_MAE_R          : "
    f"{mae_series.quantile(.75):.3f}"
)

print(
    f"P90_MAE_R          : "
    f"{mae_series.quantile(.90):.3f}"
)

print("=" * 110)


# ==========================================================
# INDIVIDUAL TRADE AUDIT
# ==========================================================

print()
print("=" * 180)
print(
    "INDIVIDUAL TRADE AUDIT"
)
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
# SAVE DETAILED CSV
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
                getattr(
                    trade,
                    "mfe",
                    None,
                ),

            "mae":
                getattr(
                    trade,
                    "mae",
                    None,
                ),

            "mfe_r":
                getattr(
                    trade,
                    "mfe_r",
                    None,
                ),

            "mae_r":
                getattr(
                    trade,
                    "mae_r",
                    None,
                ),

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


results_df = pd.DataFrame(
    rows
)


results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ==========================================================
# FINAL
# ==========================================================

print()
print(
    f"Saved: {OUTPUT_FILE}"
)

print()
print(
    "Research script completed successfully."
)

print("=" * 80)