import numpy as np
import pandas as pd

from backtesting.session_backtester import (
    run_session_backtest,
)

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)

import strategy.orb_vwap_strategy as strategy_module
import backtesting.exit_simulator as exit_module


# ==========================================================
# CONFIGURATION
# ==========================================================

DATA_FILE = "data/raw/INFY_5MIN_REAL.csv"

MODES = [
    "ORB",
    "SWING",
    "ATR",
]


# ==========================================================
# LOAD DATA
# ==========================================================

df = pd.read_csv(DATA_FILE)

df["datetime"] = pd.to_datetime(
    df["datetime"]
)

df = df.sort_values(
    "datetime"
).reset_index(drop=True)


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
        sessions.append(session)


sessions.sort(
    key=lambda x: x["datetime"].iloc[0]
)

# ==========================================================
# BUILD ATR WARM-UP CONTEXT
# ==========================================================

ATR_WARMUP_CANDLES = 14

session_contexts = []

for session_index, session_data in enumerate(
    sessions[1:],
    start=1,
):

    if session_index == 0:

        historical_context = pd.DataFrame(
            columns=session_data.columns
        )

    else:

        previous_sessions = pd.concat(
            sessions[
                max(
                    0,
                    session_index - 5,
                ):session_index
            ],
            ignore_index=True,
        )

        historical_context = (
            previous_sessions
            .tail(ATR_WARMUP_CANDLES)
            .copy()
            .reset_index(drop=True)
        )

    session_contexts.append(
        (
            session_data,
            historical_context,
        )
    )


# ==========================================================
# IMPORTANT:
# RAW SL ANALYSIS ONLY
#
# Disable BE and trailing so that we measure the
# structural stop-loss behaviour without management
# logic changing the result.
# ==========================================================

exit_module.risk_config.break_even_enabled = False

exit_module.risk_config.trailing_stop_enabled = False


# ==========================================================
# HEADER
# ==========================================================

print()
print("=" * 110)
print("GARUDA INFY STOP-LOSS + MFE/MAE ANALYSIS")
print("=" * 110)

print(
    f"DATA FILE          : {DATA_FILE}"
)

print(
    f"ROWS               : {len(df)}"
)

print(
    f"TRADING SESSIONS   : {len(sessions)}"
)

print(
    f"FROM               : {df['datetime'].iloc[0]}"
)

print(
    f"TO                 : {df['datetime'].iloc[-1]}"
)

print(
    "BREAK-EVEN         : DISABLED"
)

print(
    "TRAILING STOP      : DISABLED"
)

print("=" * 110)


# ==========================================================
# FINAL COMPARISON STORAGE
# ==========================================================

comparison_rows = []

all_mode_trades = {}


# ==========================================================
# RUN EACH STOP-LOSS MODE
# ==========================================================

for mode in MODES:

    print()
    print()
    print("#" * 110)
    print(
        f"SL MODE: {mode}"
    )
    print("#" * 110)

    # ------------------------------------------------------
    # Set active stop-loss mode
    # ------------------------------------------------------

    strategy_module.risk_config.active_stop_loss_mode = mode

    trades = []


    # ------------------------------------------------------
    # Run all sessions
    # ------------------------------------------------------

    for session_data, historical_context in session_contexts:

        trade = run_session_backtest(
            symbol="INFY",
            strategy=ORBVWAPStrategy(),
            session_data=session_data,
            stop_loss_pct=1.0,
            target_pct=2.0,
            cost_rate_pct=0.10,
            slippage_pct=0.05,
            historical_context=historical_context,
        )

        if trade is not None:
            trades.append(trade)

    if mode == "ATR":

        print()
        print("=" * 100)
        print("ATR INITIAL-RISK DIAGNOSTIC")
        print("=" * 100)

        for trade in trades:

            print(
                "DATE:",
                trade.trade_date,
                "| DIR:",
                trade.direction,
                "| ENTRY:",
                trade.entry_price,
                "| SL:",
                trade.initial_stop_loss,
                "| INITIAL_RISK:",
                trade.initial_risk,
                "| MFE_R:",
                trade.mfe_r,
                "| MAE_R:",
                trade.mae_r,
                "| EXIT:",
                trade.exit_reason,
            )

        print("=" * 100)

        print()
        print("=" * 100)
        print("ATR NaN DIAGNOSTIC")
        print("=" * 100)

        for trade in trades:

            if (
                pd.isna(trade.initial_stop_loss)
                or pd.isna(trade.initial_risk)
                or pd.isna(trade.mfe_r)
                or pd.isna(trade.mae_r)
            ):

                print(
                    "DATE:",
                    trade.trade_date,
                    "| DIR:",
                    trade.direction,
                    "| ENTRY:",
                    trade.entry_price,
                    "| SL:",
                    trade.initial_stop_loss,
                    "| INITIAL_RISK:",
                    trade.initial_risk,
                    "| MFE:",
                    trade.mfe,
                    "| MAE:",
                    trade.mae,
                    "| MFE_R:",
                    trade.mfe_r,
                    "| MAE_R:",
                    trade.mae_r,
                    "| EXIT:",
                    trade.exit_reason,
                )

        print("=" * 100)
    # ------------------------------------------------------
    # No trades protection
    # ------------------------------------------------------

    if not trades:

        print(
            "NO TRADES GENERATED"
        )

        continue


    # ======================================================
    # BASIC EXIT STATISTICS
    # ======================================================

    stop_count = sum(
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


    # ======================================================
    # P&L STATISTICS
    # ======================================================

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
        total_pnl / len(trades)
    )

    win_rate = (
        winning_count
        / len(trades)
        * 100
    )


    # ======================================================
    # MFE / MAE ARRAYS
    # ======================================================

    mfe_values = np.array(
        [
            trade.mfe
            for trade in trades
            if trade.mfe is not None
        ],
        dtype=float,
    )

    mae_values = np.array(
        [
            trade.mae
            for trade in trades
            if trade.mae is not None
        ],
        dtype=float,
    )

    mfe_r_values = np.array(
        [
            trade.mfe_r
            for trade in trades
            if trade.mfe_r is not None
        ],
        dtype=float,
    )

    mae_r_values = np.array(
        [
            trade.mae_r
            for trade in trades
            if trade.mae_r is not None
        ],
        dtype=float,
    )


    # ======================================================
    # MFE / MAE SAMPLE
    # ======================================================

    print()
    print("-" * 110)
    print("MFE / MAE SAMPLE")
    print("-" * 110)

    print(
        f"{'DATE':<12}"
        f"{'DIR':<6}"
        f"{'ENTRY':>10}"
        f"{'SL':>10}"
        f"{'MFE':>10}"
        f"{'MAE':>10}"
        f"{'MFE_R':>10}"
        f"{'MAE_R':>10}"
        f"{'EXIT':<15}"
    )

    print("-" * 110)


    for trade in trades[:10]:

        print(
            f"{str(trade.trade_date):<12}"
            f"{trade.direction:<6}"
            f"{trade.entry_price:>10.2f}"
            f"{trade.initial_stop_loss:>10.2f}"
            f"{trade.mfe:>10.3f}"
            f"{trade.mae:>10.3f}"
            f"{trade.mfe_r:>10.3f}"
            f"{trade.mae_r:>10.3f}"
            f"{trade.exit_reason:<15}"
        )


    # ======================================================
    # MFE / MAE SUMMARY
    # ======================================================

    print()
    print("-" * 110)
    print("MFE / MAE SUMMARY")
    print("-" * 110)

    print(
        f"MFE COUNT          : {len(mfe_r_values)}"
    )

    print(
        f"MAE COUNT          : {len(mae_r_values)}"
    )

    if len(mfe_r_values) > 0:

        print(
            f"AVG MFE_R          : "
            f"{mfe_r_values.mean():.3f}"
        )

        print(
            f"MEDIAN MFE_R       : "
            f"{np.median(mfe_r_values):.3f}"
        )

        print(
            f"P75 MFE_R          : "
            f"{np.percentile(mfe_r_values, 75):.3f}"
        )

        print(
            f"P90 MFE_R          : "
            f"{np.percentile(mfe_r_values, 90):.3f}"
        )

    else:

        print(
            "MFE statistics unavailable."
        )


    if len(mae_r_values) > 0:

        print(
            f"AVG MAE_R          : "
            f"{mae_r_values.mean():.3f}"
        )

        print(
            f"MEDIAN MAE_R       : "
            f"{np.median(mae_r_values):.3f}"
        )

        print(
            f"P75 MAE_R          : "
            f"{np.percentile(mae_r_values, 75):.3f}"
        )

        print(
            f"P90 MAE_R          : "
            f"{np.percentile(mae_r_values, 90):.3f}"
        )

    else:

        print(
            "MAE statistics unavailable."
        )


    # ======================================================
    # EXIT STATISTICS
    # ======================================================

    print()
    print("-" * 110)
    print("EXIT / PERFORMANCE SUMMARY")
    print("-" * 110)

    print(
        f"TRADES             : {len(trades)}"
    )

    print(
        f"STOP_LOSS          : {stop_count}"
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

    all_mode_trades[mode] = trades.copy()
    # ======================================================
    # SAVE COMPARISON ROW
    # ======================================================

    comparison_rows.append(
        {
            "SL_MODE": mode,
            "TRADES": len(trades),
            "STOP_LOSS": stop_count,
            "TARGET": target_count,
            "END_OF_DAY": eod_count,
            "WINNING_TRADES": winning_count,
            "LOSING_TRADES": losing_count,
            "WIN_RATE_PCT": round(
                win_rate,
                2,
            ),
            "AVG_MFE_R": round(
                mfe_r_values.mean(),
                3,
            )
            if len(mfe_r_values)
            else np.nan,
            "MEDIAN_MFE_R": round(
                np.median(mfe_r_values),
                3,
            )
            if len(mfe_r_values)
            else np.nan,
            "P75_MFE_R": round(
                np.percentile(
                    mfe_r_values,
                    75,
                ),
                3,
            )
            if len(mfe_r_values)
            else np.nan,
            "P90_MFE_R": round(
                np.percentile(
                    mfe_r_values,
                    90,
                ),
                3,
            )
            if len(mfe_r_values)
            else np.nan,
            "AVG_MAE_R": round(
                mae_r_values.mean(),
                3,
            )
            if len(mae_r_values)
            else np.nan,
            "MEDIAN_MAE_R": round(
                np.median(mae_r_values),
                3,
            )
            if len(mae_r_values)
            else np.nan,
            "P75_MAE_R": round(
                np.percentile(
                    mae_r_values,
                    75,
                ),
                3,
            )
            if len(mae_r_values)
            else np.nan,
            "P90_MAE_R": round(
                np.percentile(
                    mae_r_values,
                    90,
                ),
                3,
            )
            if len(mae_r_values)
            else np.nan,
            "AVG_PNL": round(
                avg_pnl,
                2,
            ),
            "TOTAL_PNL": round(
                total_pnl,
                2,
            ),
        }
    )


# ==========================================================
# FINAL COMPARISON
# ==========================================================

comparison = pd.DataFrame(
    comparison_rows
)


print()
print()
print("=" * 140)
print("FINAL SL + MFE/MAE COMPARISON")
print("=" * 140)

print(
    comparison.to_string(
        index=False
    )
)

print("=" * 140)


# ==========================================================
# TARGET FEASIBILITY ANALYSIS
# ==========================================================

TARGET_MULTIPLES = [
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
    1.75,
    2.00,
]

print()
print("=" * 110)
print("TARGET FEASIBILITY BY SL MODE")
print("=" * 110)

target_rows = []

for mode, mode_trades in all_mode_trades.items():

    valid_trades = [
        trade
        for trade in mode_trades
        if (
            trade.initial_risk is not None
            and not pd.isna(trade.initial_risk)
            and trade.initial_risk > 0
            and trade.mfe_r is not None
            and not pd.isna(trade.mfe_r)
        )
    ]

    row = {
        "SL_MODE": mode,
        "TRADES": len(valid_trades),
    }

    for multiple in TARGET_MULTIPLES:

        reached = sum(
            1
            for trade in valid_trades
            if trade.mfe_r >= multiple
        )

        percentage = (
            reached / len(valid_trades) * 100
            if valid_trades
            else float("nan")
        )

        column_name = (
            f"REACH_{str(multiple).replace('.', '_')}R_PCT"
        )

        row[column_name] = round(
            percentage,
            2,
        )

    target_rows.append(row)


target_feasibility_df = pd.DataFrame(
    target_rows
)

print(
    target_feasibility_df.to_string(
        index=False
    )
)

target_feasibility_df.to_csv(
    "data/sl_target_feasibility_infy_26session.csv",
    index=False,
)

print()
print(
    "Saved: "
    "data/sl_target_feasibility_infy_26session.csv"
)

# ==========================================================
# SAVE RESULTS
# ==========================================================

output_file = (
    "data/sl_mfe_mae_infy_30d.csv"
)

comparison.to_csv(
    output_file,
    index=False,
)

print()
print(
    f"Saved: {output_file}"
)
print()