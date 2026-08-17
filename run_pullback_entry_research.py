import pandas as pd
from pathlib import Path


# ==========================================================
# GARUDA PULLBACK ENTRY RESEARCH
#
# Counterfactual research only.
#
# Original signal:
#     ORB + VWAP breakout / breakdown
#
# New hypothetical entry:
#     1. Wait for initial favorable move.
#     2. Wait for pullback.
#     3. Wait for resumption confirmation.
#     4. Enter at NEXT candle OPEN.
#     5. Structural SL = pullback swing extreme.
#     6. Target = 2R from the NEW entry.
#
# IMPORTANT:
# This script does NOT modify GARUDA production code.
# ==========================================================


# ==========================================================
# PATHS
# ==========================================================

ROOT = Path(__file__).resolve().parent

TRADE_FILE = (
    ROOT
    / "data"
    / "signal_candle_sl_2r_infy.csv"
)

MARKET_FILE = (
    ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "pullback_entry_research_infy.csv"
)


# ==========================================================
# CONFIGURATION
# ==========================================================

SYMBOL = "INFY"

TARGET_R = 2.0

COST_RATE_PCT = 0.10
SLIPPAGE_PCT = 0.05

# Initial favorable movement measured using
# the ORIGINAL trade's initial risk.
INITIAL_MOVE_LEVELS = [
    0.50,
    0.75,
    1.00,
]

# Pullback depth measured from the favorable extreme.
PULLBACK_LEVELS = [
    0.25,
    0.50,
    0.75,
]


# ==========================================================
# LOAD DATA
# ==========================================================

if not TRADE_FILE.exists():
    raise FileNotFoundError(
        f"Trade file not found:\n{TRADE_FILE}"
    )

if not MARKET_FILE.exists():
    raise FileNotFoundError(
        f"Market file not found:\n{MARKET_FILE}"
    )


trades = pd.read_csv(
    TRADE_FILE
)

candles = pd.read_csv(
    MARKET_FILE
)


# ==========================================================
# DATETIME
# ==========================================================

for column in [
    "signal_candle_time",
    "entry_time",
    "exit_time",
]:
    if column in trades.columns:
        trades[column] = pd.to_datetime(
            trades[column]
        )


candles["datetime"] = pd.to_datetime(
    candles["datetime"]
)


candles = (
    candles
    .sort_values("datetime")
    .reset_index(drop=True)
)


# ==========================================================
# REQUIRED COLUMNS
# ==========================================================

required_trade_columns = {
    "trade_date",
    "direction",
    "signal_candle_time",
    "entry_time",
    "entry_price",
    "initial_risk",
}


missing_trade = (
    required_trade_columns
    - set(trades.columns)
)

if missing_trade:
    raise ValueError(
        "Missing columns in signal CSV: "
        + str(sorted(missing_trade))
    )


required_market_columns = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
}

missing_market = (
    required_market_columns
    - set(candles.columns)
)

if missing_market:
    raise ValueError(
        "Missing columns in market CSV: "
        + str(sorted(missing_market))
    )


# ==========================================================
# HELPERS
# ==========================================================

def favorable_move_r(
    direction,
    entry_price,
    price,
    risk,
):
    if direction == "BUY":
        return (
            price - entry_price
        ) / risk

    return (
        entry_price - price
    ) / risk


def adverse_move_r(
    direction,
    entry_price,
    price,
    risk,
):
    if direction == "BUY":
        return (
            entry_price - price
        ) / risk

    return (
        price - entry_price
    ) / risk


def apply_entry_slippage(
    direction,
    price,
):
    """
    BUY  -> pay slightly higher
    SELL -> receive slightly lower
    """

    if direction == "BUY":
        return (
            price
            * (1.0 + SLIPPAGE_PCT / 100.0)
        )

    return (
        price
        * (1.0 - SLIPPAGE_PCT / 100.0)
    )


def apply_exit_slippage(
    direction,
    price,
):
    """
    BUY exit = SELL
    SELL exit = BUY
    """

    if direction == "BUY":
        return (
            price
            * (1.0 - SLIPPAGE_PCT / 100.0)
        )

    return (
        price
        * (1.0 + SLIPPAGE_PCT / 100.0)
    )


def calculate_net_pnl(
    direction,
    entry_price,
    exit_price,
):
    if direction == "BUY":
        gross = (
            exit_price
            - entry_price
        )

    else:
        gross = (
            entry_price
            - exit_price
        )

    turnover = (
        entry_price
        + exit_price
    )

    costs = (
        turnover
        * COST_RATE_PCT
        / 100.0
    )

    return (
        gross
        - costs
    )


def candle_hits_stop(
    direction,
    candle,
    stop_loss,
):
    if direction == "BUY":
        return (
            float(candle["low"])
            <= stop_loss
        )

    return (
        float(candle["high"])
        >= stop_loss
    )


def candle_hits_target(
    direction,
    candle,
    target,
):
    if direction == "BUY":
        return (
            float(candle["high"])
            >= target
        )

    return (
        float(candle["low"])
        <= target
    )


# ==========================================================
# MAIN RESEARCH
# ==========================================================

results = []


print()
print("=" * 120)
print(
    "GARUDA — COUNTERFACTUAL PULLBACK ENTRY RESEARCH"
)
print("=" * 120)

print(
    f"Original signals analysed : {len(trades)}"
)

print(
    f"Initial move levels       : {INITIAL_MOVE_LEVELS}"
)

print(
    f"Pullback levels            : {PULLBACK_LEVELS}"
)

print(
    f"Target                     : {TARGET_R}R"
)

print()


# ==========================================================
# EACH ORIGINAL SIGNAL
# ==========================================================

for trade_index, original in trades.iterrows():

    direction = str(
        original["direction"]
    ).upper()

    if direction not in (
        "BUY",
        "SELL",
    ):
        continue


    signal_time = pd.Timestamp(
        original["signal_candle_time"]
    )

    original_entry_time = pd.Timestamp(
        original["entry_time"]
    )

    original_entry_price = float(
        original["entry_price"]
    )

    original_risk = float(
        original["initial_risk"]
    )

    trade_date = str(
        original["trade_date"]
    )


    if original_risk <= 0:
        continue


    # ======================================================
    # ALL CANDLES AFTER ORIGINAL SIGNAL
    #
    # IMPORTANT:
    # We DO NOT stop at the original trade exit.
    #
    # This is a counterfactual strategy:
    #
    # "What if we had NOT entered the original trade?"
    # ======================================================

    session_date = (
        signal_time.date()
    )


    session = candles[
        candles["datetime"].dt.date
        == session_date
    ].copy()


    session = (
        session[
            session["datetime"]
            >= signal_time
        ]
        .sort_values("datetime")
        .reset_index(drop=True)
    )


    if session.empty:
        continue


    # ======================================================
    # TEST EACH VARIANT
    # ======================================================

    for initial_move_r in INITIAL_MOVE_LEVELS:

        for pullback_r in PULLBACK_LEVELS:

            # --------------------------------------------------
            # STATE
            # --------------------------------------------------

            initial_move_reached = False

            initial_move_time = None

            favorable_extreme = None

            favorable_extreme_time = None

            pullback_reached = False

            pullback_time = None

            pullback_level_price = None

            pullback_extreme = None

            pullback_confirmation = False

            confirmation_time = None

            confirmation_index = None

            hypothetical_entry_time = None

            hypothetical_entry_price = None

            structural_stop = None

            hypothetical_target = None

            exit_time = None

            exit_price = None

            exit_reason = None

            ambiguous_exit = False

            mfe = 0.0

            mae = 0.0


            # --------------------------------------------------
            # PHASE 1
            #
            # WAIT FOR INITIAL FAVORABLE MOVE
            # --------------------------------------------------

            for i in range(
                len(session)
            ):

                candle = session.iloc[i]

                dt = candle["datetime"]

                high = float(
                    candle["high"]
                )

                low = float(
                    candle["low"]
                )


                if not initial_move_reached:

                    if direction == "BUY":

                        move = (
                            high
                            - original_entry_price
                        )

                    else:

                        move = (
                            original_entry_price
                            - low
                        )


                    move_r = (
                        move
                        / original_risk
                    )


                    if move_r >= initial_move_r:

                        initial_move_reached = True

                        initial_move_time = dt


                        if direction == "BUY":

                            favorable_extreme = high

                        else:

                            favorable_extreme = low


                        favorable_extreme_time = dt

                        continue


                # --------------------------------------------------
                # PHASE 2
                #
                # UPDATE FAVORABLE EXTREME
                # --------------------------------------------------

                if initial_move_reached:

                    new_extreme = False


                    if direction == "BUY":

                        if (
                            high
                            > favorable_extreme
                        ):

                            favorable_extreme = high

                            favorable_extreme_time = dt

                            new_extreme = True

                    else:

                        if (
                            low
                            < favorable_extreme
                        ):

                            favorable_extreme = low

                            favorable_extreme_time = dt

                            new_extreme = True


                    # --------------------------------------------------
                    # DO NOT allow same candle to create extreme AND
                    # trigger pullback.
                    # --------------------------------------------------

                    if new_extreme:
                        continue


                    # --------------------------------------------------
                    # PULLBACK LEVEL
                    # --------------------------------------------------

                    if direction == "BUY":

                        pullback_level_price = (
                            favorable_extreme
                            - (
                                pullback_r
                                * original_risk
                            )
                        )

                    else:

                        pullback_level_price = (
                            favorable_extreme
                            + (
                                pullback_r
                                * original_risk
                            )
                        )


                    # --------------------------------------------------
                    # PHASE 3
                    #
                    # WAIT FOR PULLBACK
                    # --------------------------------------------------

                    if not pullback_reached:

                        if direction == "BUY":

                            touched = (
                                low
                                <= pullback_level_price
                            )

                        else:

                            touched = (
                                high
                                >= pullback_level_price
                            )


                        if touched:

                            pullback_reached = True

                            pullback_time = dt

                            pullback_extreme = (
                                low
                                if direction == "BUY"
                                else high
                            )

                            continue


                    # --------------------------------------------------
                    # PHASE 4
                    #
                    # AFTER PULLBACK
                    #
                    # We wait for RESUMPTION confirmation.
                    #
                    # BUY:
                    #     close > previous candle high
                    #
                    # SELL:
                    #     close < previous candle low
                    #
                    # Entry:
                    #     NEXT candle OPEN
                    # --------------------------------------------------

                    if (
                        pullback_reached
                        and not pullback_confirmation
                        and i > 0
                    ):

                        previous = session.iloc[
                            i - 1
                        ]


                        previous_high = float(
                            previous["high"]
                        )

                        previous_low = float(
                            previous["low"]
                        )

                        close = float(
                            candle["close"]
                        )


                        if direction == "BUY":

                            confirmation = (
                                close
                                > previous_high
                            )

                        else:

                            confirmation = (
                                close
                                < previous_low
                            )


                        if confirmation:

                            # ------------------------------------------
                            # We cannot enter on this candle's close
                            # because that would use information from
                            # the completed candle.
                            #
                            # Enter NEXT candle OPEN.
                            # ------------------------------------------

                            if (
                                i + 1
                                >= len(session)
                            ):
                                break


                            next_candle = session.iloc[
                                i + 1
                            ]


                            hypothetical_entry_time = (
                                next_candle["datetime"]
                            )


                            hypothetical_entry_price = (
                                apply_entry_slippage(
                                    direction,
                                    float(
                                        next_candle[
                                            "open"
                                        ]
                                    ),
                                )
                            )


                            # ------------------------------------------
                            # Structural SL
                            #
                            # Use the pullback swing extreme.
                            # ------------------------------------------

                            if direction == "BUY":

                                structural_stop = (
                                    pullback_extreme
                                )

                            else:

                                structural_stop = (
                                    pullback_extreme
                                )


                            new_risk = abs(
                                hypothetical_entry_price
                                - structural_stop
                            )


                            # Invalid structure
                            if new_risk <= 0:

                                exit_reason = (
                                    "INVALID_RISK"
                                )

                                break


                            if direction == "BUY":

                                hypothetical_target = (
                                    hypothetical_entry_price
                                    + (
                                        TARGET_R
                                        * new_risk
                                    )
                                )

                            else:

                                hypothetical_target = (
                                    hypothetical_entry_price
                                    - (
                                        TARGET_R
                                        * new_risk
                                    )
                                )


                            pullback_confirmation = True

                            confirmation_time = dt

                            confirmation_index = i

                            break


            # ======================================================
            # NO CONFIRMED ENTRY
            # ======================================================

            if not pullback_confirmation:

                results.append(
                    {
                        "trade_index":
                            trade_index + 1,

                        "trade_date":
                            trade_date,

                        "direction":
                            direction,

                        "signal_time":
                            signal_time,

                        "original_entry_time":
                            original_entry_time,

                        "original_entry_price":
                            original_entry_price,

                        "original_risk":
                            original_risk,

                        "initial_move_r":
                            initial_move_r,

                        "pullback_r":
                            pullback_r,

                        "initial_move_reached":
                            initial_move_reached,

                        "initial_move_time":
                            initial_move_time,

                        "favorable_extreme":
                            favorable_extreme,

                        "favorable_extreme_time":
                            favorable_extreme_time,

                        "pullback_reached":
                            pullback_reached,

                        "pullback_time":
                            pullback_time,

                        "pullback_level":
                            pullback_level_price,

                        "pullback_extreme":
                            pullback_extreme,

                        "confirmation":
                            False,

                        "confirmation_time":
                            confirmation_time,

                        "entry_time":
                            None,

                        "entry_price":
                            None,

                        "structural_stop":
                            None,

                        "new_risk":
                            None,

                        "target":
                            None,

                        "exit_time":
                            None,

                        "exit_price":
                            None,

                        "exit_reason":
                            "NO_ENTRY",

                        "ambiguous_exit":
                            False,

                        "mfe_r":
                            None,

                        "mae_r":
                            None,

                        "net_pnl":
                            None,
                    }
                )

                continue


            # ======================================================
            # HYPOTHETICAL TRADE MANAGEMENT
            #
            # Start AFTER entry candle.
            # ======================================================

            entry_index = (
                confirmation_index
                + 1
            )


            entry_candle = session.iloc[
                entry_index
            ]


            entry_price = (
                hypothetical_entry_price
            )

            stop_loss = (
                structural_stop
            )

            target = (
                hypothetical_target
            )

            new_risk = abs(
                entry_price
                - stop_loss
            )


            # ======================================================
            # MFE / MAE AFTER HYPOTHETICAL ENTRY
            # ======================================================

            max_favorable = 0.0
            max_adverse = 0.0


            for j in range(
                entry_index,
                len(session)
            ):

                candle = session.iloc[j]

                dt = candle["datetime"]

                high = float(
                    candle["high"]
                )

                low = float(
                    candle["low"]
                )


                # --------------------------------------------------
                # MFE / MAE
                # --------------------------------------------------

                if direction == "BUY":

                    favorable = (
                        high
                        - entry_price
                    )

                    adverse = (
                        entry_price
                        - low
                    )

                else:

                    favorable = (
                        entry_price
                        - low
                    )

                    adverse = (
                        high
                        - entry_price
                    )


                max_favorable = max(
                    max_favorable,
                    max(
                        0.0,
                        favorable,
                    ),
                )

                max_adverse = max(
                    max_adverse,
                    max(
                        0.0,
                        adverse,
                    ),
                )


                # --------------------------------------------------
                # EXIT DETECTION
                # --------------------------------------------------

                stop_hit = (
                    candle_hits_stop(
                        direction,
                        candle,
                        stop_loss,
                    )
                )

                target_hit = (
                    candle_hits_target(
                        direction,
                        candle,
                        target,
                    )
                )


                # --------------------------------------------------
                # BOTH HIT SAME CANDLE
                #
                # OHLC data cannot tell which happened first.
                #
                # Conservative research assumption:
                # STOP FIRST.
                # --------------------------------------------------

                if (
                    stop_hit
                    and target_hit
                ):

                    ambiguous_exit = True

                    exit_time = dt

                    exit_reason = (
                        "AMBIGUOUS_STOP_FIRST"
                    )

                    exit_price = (
                        apply_exit_slippage(
                            direction,
                            stop_loss,
                        )
                    )

                    break


                if stop_hit:

                    exit_time = dt

                    exit_reason = (
                        "STOP_LOSS"
                    )

                    exit_price = (
                        apply_exit_slippage(
                            direction,
                            stop_loss,
                        )
                    )

                    break


                if target_hit:

                    exit_time = dt

                    exit_reason = (
                        "TARGET"
                    )

                    exit_price = (
                        apply_exit_slippage(
                            direction,
                            target,
                        )

                    )

                    break


            # ======================================================
            # END OF DAY
            # ======================================================

            if exit_reason is None:

                last_candle = (
                    session.iloc[-1]
                )

                exit_time = (
                    last_candle["datetime"]
                )

                exit_price = (
                    apply_exit_slippage(
                        direction,
                        float(
                            last_candle[
                                "close"
                            ]
                        ),
                    )
                )

                exit_reason = (
                    "END_OF_DAY"
                )


            # ======================================================
            # R-METRICS
            # ======================================================

            mfe_r = (
                max_favorable
                / new_risk
            )

            mae_r = (
                max_adverse
                / new_risk
            )


            # ======================================================
            # PNL
            # ======================================================

            net_pnl = calculate_net_pnl(
                direction,
                entry_price,
                exit_price,
            )


            # ======================================================
            # STORE
            # ======================================================

            results.append(
                {
                    "trade_index":
                        trade_index + 1,

                    "trade_date":
                        trade_date,

                    "direction":
                        direction,

                    "signal_time":
                        signal_time,

                    "original_entry_time":
                        original_entry_time,

                    "original_entry_price":
                        original_entry_price,

                    "original_risk":
                        original_risk,

                    "initial_move_r":
                        initial_move_r,

                    "pullback_r":
                        pullback_r,

                    "initial_move_reached":
                        initial_move_reached,

                    "initial_move_time":
                        initial_move_time,

                    "favorable_extreme":
                        favorable_extreme,

                    "favorable_extreme_time":
                        favorable_extreme_time,

                    "pullback_reached":
                        pullback_reached,

                    "pullback_time":
                        pullback_time,

                    "pullback_level":
                        pullback_level_price,

                    "pullback_extreme":
                        pullback_extreme,

                    "confirmation":
                        True,

                    "confirmation_time":
                        confirmation_time,

                    "entry_time":
                        hypothetical_entry_time,

                    "entry_price":
                        entry_price,

                    "structural_stop":
                        stop_loss,

                    "new_risk":
                        new_risk,

                    "target":
                        target,

                    "exit_time":
                        exit_time,

                    "exit_price":
                        exit_price,

                    "exit_reason":
                        exit_reason,

                    "ambiguous_exit":
                        ambiguous_exit,

                    "mfe_r":
                        mfe_r,

                    "mae_r":
                        mae_r,

                    "net_pnl":
                        net_pnl,
                }
            )


# ==========================================================
# DATAFRAME
# ==========================================================

result_df = pd.DataFrame(
    results
)


if result_df.empty:

    print(
        "No research results generated."
    )

    raise SystemExit(1)


# ==========================================================
# SUMMARY
# ==========================================================

summary_rows = []


for initial_move_r in INITIAL_MOVE_LEVELS:

    for pullback_r in PULLBACK_LEVELS:

        subset = result_df[
            (
                result_df[
                    "initial_move_r"
                ]
                == initial_move_r
            )
            &
            (
                result_df[
                    "pullback_r"
                ]
                == pullback_r
            )
        ]


        initial_count = int(
            subset[
                "initial_move_reached"
            ].sum()
        )


        pullback_count = int(
            subset[
                "pullback_reached"
            ].sum()
        )


        entry_count = int(
            subset[
                "confirmation"
            ].sum()
        )


        entered = subset[
            subset[
                "confirmation"
            ]
        ]


        target_count = int(
            (
                entered[
                    "exit_reason"
                ]
                == "TARGET"
            ).sum()
        )


        stop_count = int(
            entered[
                "exit_reason"
            ]
            .isin(
                [
                    "STOP_LOSS",
                    "AMBIGUOUS_STOP_FIRST",
                ]
            )
            .sum()
        )


        eod_count = int(
            (
                entered[
                    "exit_reason"
                ]
                == "END_OF_DAY"
            ).sum()
        )


        ambiguous_count = int(
            entered[
                "ambiguous_exit"
            ].sum()
        )


        winning_count = int(
            (
                entered[
                    "net_pnl"
                ]
                > 0
            ).sum()
        )


        losing_count = int(
            (
                entered[
                    "net_pnl"
                ]
                < 0
            ).sum()
        )


        total_pnl = (
            entered[
                "net_pnl"
            ]
            .sum()
        )


        avg_pnl = (
            entered[
                "net_pnl"
            ]
            .mean()
            if entry_count
            else 0.0
        )


        win_rate = (
            winning_count
            / entry_count
            * 100
            if entry_count
            else 0.0
        )


        gross_profit = (
            entered.loc[
                entered[
                    "net_pnl"
                ] > 0,
                "net_pnl",
            ]
            .sum()
        )


        gross_loss = abs(
            entered.loc[
                entered[
                    "net_pnl"
                ] < 0,
                "net_pnl",
            ]
            .sum()
        )


        profit_factor = (
            gross_profit
            / gross_loss
            if gross_loss > 0
            else float("inf")
        )


        avg_mfe = (
            entered[
                "mfe_r"
            ].mean()
            if entry_count
            else float("nan")
        )


        avg_mae = (
            entered[
                "mae_r"
            ].mean()
            if entry_count
            else float("nan")
        )


        target_pct = (
            target_count
            / entry_count
            * 100
            if entry_count
            else 0.0
        )


        summary_rows.append(
            {
                "INITIAL_MOVE_R":
                    initial_move_r,

                "PULLBACK_R":
                    pullback_r,

                "INITIAL_MOVE_COUNT":
                    initial_count,

                "PULLBACK_COUNT":
                    pullback_count,

                "ENTRY_COUNT":
                    entry_count,

                "TARGET":
                    target_count,

                "STOP_LOSS":
                    stop_count,

                "END_OF_DAY":
                    eod_count,

                "AMBIGUOUS":
                    ambiguous_count,

                "WINNING_TRADES":
                    winning_count,

                "LOSING_TRADES":
                    losing_count,

                "WIN_RATE_PCT":
                    win_rate,

                "TARGET_RATE_PCT":
                    target_pct,

                "AVG_MFE_R":
                    avg_mfe,

                "AVG_MAE_R":
                    avg_mae,

                "AVG_PNL":
                    avg_pnl,

                "TOTAL_PNL":
                    total_pnl,

                "PROFIT_FACTOR":
                    profit_factor,
            }
        )


summary_df = pd.DataFrame(
    summary_rows
)


# ==========================================================
# PRINT SUMMARY
# ==========================================================

print()
print("=" * 145)
print(
    "PULLBACK ENTRY RESEARCH — ALL VARIANTS"
)
print("=" * 145)

print(
    summary_df.to_string(
        index=False,
        float_format=lambda x:
            f"{x:.2f}"
    )
)


# ==========================================================
# BEST VARIANTS
# ==========================================================

print()
print("=" * 145)
print(
    "BEST PULLBACK ENTRY VARIANTS"
)
print("=" * 145)


best = (
    summary_df[
        summary_df[
            "ENTRY_COUNT"
        ] >= 5
    ]
    .sort_values(
        [
            "PROFIT_FACTOR",
            "TOTAL_PNL",
        ],
        ascending=False,
    )
)


if best.empty:

    print(
        "No variant produced at least 5 entries."
    )

else:

    print(
        best.to_string(
            index=False,
            float_format=lambda x:
                f"{x:.2f}"
        )
    )


# ==========================================================
# STANDARD VARIANT
# ==========================================================

standard = result_df[
    (
        result_df[
            "initial_move_r"
        ]
        == 0.50
    )
    &
    (
        result_df[
            "pullback_r"
        ]
        == 0.50
    )
]


standard_entries = standard[
    standard[
        "confirmation"
    ]
]


print()
print("=" * 145)
print(
    "STANDARD 0.5R MOVE -> 0.5R PULLBACK -> CONFIRMATION -> 2R"
)
print("=" * 145)

print(
    f"Original signals       : "
    f"{len(standard)}"
)

print(
    f"Initial 0.5R reached   : "
    f"{int(standard['initial_move_reached'].sum())}"
)

print(
    f"0.5R pullback reached  : "
    f"{int(standard['pullback_reached'].sum())}"
)

print(
    f"Confirmed entries      : "
    f"{len(standard_entries)}"
)

print(
    f"Targets                : "
    f"{int((standard_entries['exit_reason'] == 'TARGET').sum())}"
)

print(
    f"Stop losses            : "
    f"{int(standard_entries['exit_reason'].isin(['STOP_LOSS', 'AMBIGUOUS_STOP_FIRST']).sum())}"
)

print(
    f"End of day             : "
    f"{int((standard_entries['exit_reason'] == 'END_OF_DAY').sum())}"
)

print(
    f"Ambiguous              : "
    f"{int(standard_entries['ambiguous_exit'].sum())}"
)

if len(standard_entries):

    winners = int(
        (
            standard_entries[
                "net_pnl"
            ]
            > 0
        ).sum()
    )

    win_rate = (
        winners
        / len(standard_entries)
        * 100
    )

    print(
        f"Win rate               : "
        f"{win_rate:.2f}%"
    )

    print(
        f"Average PNL            : "
        f"{standard_entries['net_pnl'].mean():.2f}"
    )

    print(
        f"Total PNL              : "
        f"{standard_entries['net_pnl'].sum():.2f}"
    )


# ==========================================================
# INDIVIDUAL AUDIT
# ==========================================================

print()
print("=" * 190)
print(
    "INDIVIDUAL PULLBACK ENTRY AUDIT — STANDARD 0.5R / 0.5R"
)
print("=" * 190)

if standard_entries.empty:

    print(
        "No confirmed entries."
    )

else:

    audit_columns = [
        "trade_date",
        "direction",
        "signal_time",
        "initial_move_time",
        "favorable_extreme_time",
        "pullback_time",
        "confirmation_time",
        "entry_time",
        "entry_price",
        "structural_stop",
        "new_risk",
        "target",
        "exit_time",
        "exit_price",
        "exit_reason",
        "mfe_r",
        "mae_r",
        "net_pnl",
    ]


    print(
        standard_entries[
            audit_columns
        ].to_string(
            index=False,
            float_format=lambda x:
                f"{x:.3f}"
        )
    )


# ==========================================================
# SAVE
# ==========================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 100)
print(
    "Saved:"
)

print(
    OUTPUT_FILE
)

print("=" * 100)