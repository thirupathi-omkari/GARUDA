import pandas as pd
from pathlib import Path


# ==========================================================
# GARUDA ORB + VWAP
# STRUCTURAL RETEST VERIFICATION
#
# RESEARCH ONLY
#
# This script does NOT modify GARUDA production code.
#
# Sequence being verified:
#
#     ORB + VWAP BREAK
#             |
#             v
#       MOVE AWAY
#             |
#             v
#         RETEST
#             |
#             v
#        REJECTION
#             |
#             v
#      CONTINUATION
#
# No R-based pullback threshold is used here.
# ==========================================================


# ==========================================================
# PATHS
# ==========================================================

ROOT = Path(__file__).resolve().parent

SIGNAL_FILE = (
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
    / "orb_vwap_retest_verification_infy.csv"
)


# ==========================================================
# CONFIGURATION
# ==========================================================

SYMBOL = "INFY"

OPENING_START = "09:15"
OPENING_END = "09:30"

# How many candles must pass after the signal candle
# before we are allowed to call a later candle a retest.
#
# This prevents the signal candle itself from being
# classified as a retest.
MIN_CANDLES_AFTER_BREAK = 1

# Maximum number of candles to display around each event
AUDIT_CONTEXT_CANDLES = 3


# ==========================================================
# LOAD DATA
# ==========================================================

if not SIGNAL_FILE.exists():
    raise FileNotFoundError(
        f"Signal file not found:\n{SIGNAL_FILE}"
    )

if not MARKET_FILE.exists():
    raise FileNotFoundError(
        f"Market file not found:\n{MARKET_FILE}"
    )


signals = pd.read_csv(
    SIGNAL_FILE
)

market = pd.read_csv(
    MARKET_FILE
)


# ==========================================================
# DATETIME
# ==========================================================

signals["signal_candle_time"] = pd.to_datetime(
    signals["signal_candle_time"]
)

signals["entry_time"] = pd.to_datetime(
    signals["entry_time"],
    errors="coerce",
)

market["datetime"] = pd.to_datetime(
    market["datetime"]
)


market = (
    market
    .sort_values("datetime")
    .reset_index(drop=True)
)


# ==========================================================
# REQUIRED COLUMNS
# ==========================================================

required_signal_columns = {
    "trade_date",
    "direction",
    "signal_candle_time",
    "entry_price",
}

missing_signal_columns = (
    required_signal_columns
    - set(signals.columns)
)

if missing_signal_columns:
    raise ValueError(
        "Missing columns in signal file: "
        + str(sorted(missing_signal_columns))
    )


required_market_columns = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
}

missing_market_columns = (
    required_market_columns
    - set(market.columns)
)

if missing_market_columns:
    raise ValueError(
        "Missing columns in market file: "
        + str(sorted(missing_market_columns))
    )


# ==========================================================
# VWAP
#
# Same basic session VWAP concept used by GARUDA:
#
# cumulative typical-price * volume
# ---------------------------------
# cumulative volume
# ==========================================================

def add_session_vwap(session):
    session = session.copy()

    typical_price = (
        session["high"]
        + session["low"]
        + session["close"]
    ) / 3.0

    pv = (
        typical_price
        * session["volume"]
    )

    cumulative_pv = pv.cumsum()

    cumulative_volume = (
        session["volume"]
        .cumsum()
    )

    session["vwap"] = (
        cumulative_pv
        / cumulative_volume
    )

    return session


# ==========================================================
# HELPER
# ==========================================================

def fmt_price(value):
    if value is None:
        return "NA"

    try:
        if pd.isna(value):
            return "NA"
    except Exception:
        pass

    return f"{float(value):.2f}"


def fmt_time(value):
    if value is None:
        return "NA"

    try:
        if pd.isna(value):
            return "NA"
    except Exception:
        pass

    return str(value)


def get_bool(value):
    return bool(value)


# ==========================================================
# RESULTS
# ==========================================================

results = []


# ==========================================================
# HEADER
# ==========================================================

print()
print("=" * 110)
print(
    "GARUDA ORB + VWAP STRUCTURAL RETEST VERIFICATION"
)
print("=" * 110)

print(
    f"Signals supplied       : {len(signals)}"
)

print(
    f"Opening range          : "
    f"{OPENING_START} <= time < {OPENING_END}"
)

print(
    "Method                 : "
    "ORB/VWAP structural zone retest"
)

print(
    "R-based pullback       : NOT USED"
)

print("=" * 110)
print()


# ==========================================================
# PROCESS EACH SIGNAL
# ==========================================================

for signal_index, signal_row in signals.iterrows():

    direction = str(
        signal_row["direction"]
    ).upper()

    signal_time = pd.Timestamp(
        signal_row["signal_candle_time"]
    )

    trade_date = signal_time.date()


    # ------------------------------------------------------
    # SESSION
    # ------------------------------------------------------

    session = market[
        market["datetime"].dt.date
        == trade_date
    ].copy()


    session = (
        session
        .sort_values("datetime")
        .reset_index(drop=True)
    )


    if session.empty:

        results.append(
            {
                "trade_index":
                    signal_index + 1,

                "trade_date":
                    trade_date,

                "direction":
                    direction,

                "signal_time":
                    signal_time,

                "signal_found":
                    False,

                "break_confirmed":
                    False,

                "move_away":
                    False,

                "retest_reached":
                    False,

                "rejection":
                    False,

                "continuation":
                    False,

                "status":
                    "NO_SESSION",
            }
        )

        continue


    # ------------------------------------------------------
    # SESSION VWAP
    # ------------------------------------------------------

    session = add_session_vwap(
        session
    )


    # ------------------------------------------------------
    # OPENING RANGE
    #
    # Same definition as GARUDA:
    #
    # 09:15 <= candle time < 09:30
    # ------------------------------------------------------

    session_time = (
        session["datetime"]
        .dt.strftime("%H:%M")
    )


    opening_data = session[
        (
            session_time
            >= OPENING_START
        )
        &
        (
            session_time
            < OPENING_END
        )
    ].copy()


    if opening_data.empty:

        results.append(
            {
                "trade_index":
                    signal_index + 1,

                "trade_date":
                    trade_date,

                "direction":
                    direction,

                "signal_time":
                    signal_time,

                "signal_found":
                    False,

                "break_confirmed":
                    False,

                "move_away":
                    False,

                "retest_reached":
                    False,

                "rejection":
                    False,

                "continuation":
                    False,

                "status":
                    "NO_OPENING_RANGE",
            }
        )

        continue


    opening_high = float(
        opening_data["high"].max()
    )

    opening_low = float(
        opening_data["low"].min()
    )


    # ------------------------------------------------------
    # SIGNAL CANDLE
    # ------------------------------------------------------

    signal_matches = session[
        session["datetime"]
        == signal_time
    ]


    if signal_matches.empty:

        results.append(
            {
                "trade_index":
                    signal_index + 1,

                "trade_date":
                    trade_date,

                "direction":
                    direction,

                "signal_time":
                    signal_time,

                "signal_found":
                    False,

                "break_confirmed":
                    False,

                "move_away":
                    False,

                "retest_reached":
                    False,

                "rejection":
                    False,

                "continuation":
                    False,

                "status":
                    "SIGNAL_CANDLE_NOT_FOUND",
            }
        )

        continue


    signal_position = (
        signal_matches.index[0]
    )


    signal_candle = (
        signal_matches.iloc[0]
    )


    signal_close = float(
        signal_candle["close"]
    )

    signal_high = float(
        signal_candle["high"]
    )

    signal_low = float(
        signal_candle["low"]
    )

    signal_vwap = float(
        signal_candle["vwap"]
    )


    # ------------------------------------------------------
    # VERIFY ACTUAL GARUDA SIGNAL CONDITION
    #
    # BUY:
    # close > ORB HIGH
    # close > VWAP
    #
    # SELL:
    # close < ORB LOW
    # close < VWAP
    # ------------------------------------------------------

    if direction == "BUY":

        break_confirmed = (
            signal_close
            > opening_high
            and
            signal_close
            > signal_vwap
        )

    elif direction == "SELL":

        break_confirmed = (
            signal_close
            < opening_low
            and
            signal_close
            < signal_vwap
        )

    else:

        break_confirmed = False


    # ------------------------------------------------------
    # BROKEN STRUCTURAL ZONE
    #
    # SELL:
    #     between ORB LOW and VWAP
    #
    # BUY:
    #     between VWAP and ORB HIGH
    # ------------------------------------------------------

    if direction == "SELL":

        zone_low = min(
            opening_low,
            signal_vwap,
        )

        zone_high = max(
            opening_low,
            signal_vwap,
        )

        broken_level_primary = (
            opening_low
        )

        broken_level_secondary = (
            signal_vwap
        )

    else:

        zone_low = min(
            opening_high,
            signal_vwap,
        )

        zone_high = max(
            opening_high,
            signal_vwap,
        )

        broken_level_primary = (
            opening_high
        )

        broken_level_secondary = (
            signal_vwap
        )


    # ------------------------------------------------------
    # INITIAL STATE
    # ------------------------------------------------------

    move_away = False

    move_away_time = None

    move_away_price = None

    favorable_extreme = None

    favorable_extreme_time = None

    retest_reached = False

    retest_time = None

    retest_price = None

    retest_candle_high = None

    retest_candle_low = None

    retest_candle_close = None

    rejection = False

    rejection_time = None

    rejection_price = None

    continuation = False

    continuation_time = None

    continuation_price = None


    # ------------------------------------------------------
    # PHASE 1
    #
    # LOOK AFTER SIGNAL CANDLE
    # ------------------------------------------------------

    future_start = (
        signal_position
        + MIN_CANDLES_AFTER_BREAK
    )


    if future_start >= len(session):

        results.append(
            {
                "trade_index":
                    signal_index + 1,

                "trade_date":
                    trade_date,

                "direction":
                    direction,

                "signal_time":
                    signal_time,

                "signal_found":
                    True,

                "break_confirmed":
                    break_confirmed,

                "move_away":
                    False,

                "retest_reached":
                    False,

                "rejection":
                    False,

                "continuation":
                    False,

                "status":
                    "NO_FUTURE_CANDLES",
            }
        )

        continue


    # ------------------------------------------------------
    # WALK FORWARD
    # ------------------------------------------------------

    for position in range(
        future_start,
        len(session),
    ):

        candle = session.iloc[
            position
        ]


        dt = candle["datetime"]

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        close = float(
            candle["close"]
        )


        # ==================================================
        # PHASE A
        #
        # FIND MOVE AWAY FROM BROKEN ZONE
        #
        # We deliberately do NOT use R.
        #
        # We simply require price to establish a favorable
        # post-break extreme outside the signal candle.
        # ==================================================

        if not move_away:

            if direction == "SELL":

                favorable_distance = (
                    zone_low
                    - low
                )

                signal_favorable_distance = (
                    zone_low
                    - signal_close
                )


                if (
                    favorable_distance
                    > signal_favorable_distance
                    and
                    low < signal_close
                ):

                    move_away = True

                    move_away_time = dt

                    move_away_price = low

                    favorable_extreme = low

                    favorable_extreme_time = dt

                    continue


            else:

                favorable_distance = (
                    high
                    - zone_high
                )

                signal_favorable_distance = (
                    signal_close
                    - zone_high
                )


                if (
                    favorable_distance
                    > signal_favorable_distance
                    and
                    high > signal_close
                ):

                    move_away = True

                    move_away_time = dt

                    move_away_price = high

                    favorable_extreme = high

                    favorable_extreme_time = dt

                    continue


        # ==================================================
        # PHASE B
        #
        # UPDATE FAVORABLE EXTREME
        #
        # Only BEFORE retest.
        # ==================================================

        if (
            move_away
            and not retest_reached
        ):

            if direction == "SELL":

                if (
                    low
                    < favorable_extreme
                ):

                    favorable_extreme = low

                    favorable_extreme_time = dt

                    continue

            else:

                if (
                    high
                    > favorable_extreme
                ):

                    favorable_extreme = high

                    favorable_extreme_time = dt

                    continue


        # ==================================================
        # PHASE C
        #
        # RETEST
        #
        # SELL:
        # price comes back UP into broken zone
        #
        # BUY:
        # price comes back DOWN into broken zone
        # ==================================================

        if (
            move_away
            and not retest_reached
        ):

            if direction == "SELL":

                retest_touched = (
                    high
                    >= zone_low
                )

            else:

                retest_touched = (
                    low
                    <= zone_high
                )


            if retest_touched:

                retest_reached = True

                retest_time = dt

                retest_price = (
                    zone_low
                    if direction == "SELL"
                    else zone_high
                )

                retest_candle_high = high

                retest_candle_low = low

                retest_candle_close = close

                # ------------------------------------------
                # DO NOT classify same candle as rejection.
                #
                # We need a subsequent candle.
                # ------------------------------------------

                continue


        # ==================================================
        # PHASE D
        #
        # REJECTION
        #
        # We use a deliberately simple, auditable definition:
        #
        # SELL:
        #   after retest, candle closes BELOW the
        #   broken-zone lower boundary.
        #
        # BUY:
        #   after retest, candle closes ABOVE the
        #   broken-zone upper boundary.
        #
        # This means the market came back to the zone
        # and subsequently closed back outside it.
        # ==================================================

        if (
            retest_reached
            and not rejection
        ):

            if direction == "SELL":

                if (
                    close
                    < zone_low
                ):

                    rejection = True

                    rejection_time = dt

                    rejection_price = close

                    continue

            else:

                if (
                    close
                    > zone_high
                ):

                    rejection = True

                    rejection_time = dt

                    rejection_price = close

                    continue


        # ==================================================
        # PHASE E
        #
        # CONTINUATION AFTER REJECTION
        #
        # SELL:
        # close below rejection candle low
        #
        # BUY:
        # close above rejection candle high
        #
        # This is only verification, NOT an entry rule.
        # ==================================================

        if (
            rejection
            and not continuation
        ):

            # Need the actual rejection candle
            rejection_rows = session[
                session["datetime"]
                == rejection_time
            ]


            if rejection_rows.empty:
                continue


            rejection_candle = (
                rejection_rows.iloc[0]
            )


            rejection_high = float(
                rejection_candle["high"]
            )

            rejection_low = float(
                rejection_candle["low"]
            )


            if direction == "SELL":

                if (
                    close
                    < rejection_low
                ):

                    continuation = True

                    continuation_time = dt

                    continuation_price = close

                    break

            else:

                if (
                    close
                    > rejection_high
                ):

                    continuation = True

                    continuation_time = dt

                    continuation_price = close

                    break


    # ======================================================
    # STATUS
    # ======================================================

    if not break_confirmed:

        status = (
            "SIGNAL_DOES_NOT_MATCH_GARUDA_LOGIC"
        )

    elif not move_away:

        status = (
            "BREAK_BUT_NO_MOVE_AWAY"
        )

    elif not retest_reached:

        status = (
            "MOVE_AWAY_BUT_NO_RETEST"
        )

    elif not rejection:

        status = (
            "RETEST_BUT_NO_REJECTION"
        )

    elif not continuation:

        status = (
            "REJECTION_BUT_NO_CONTINUATION"
        )

    else:

        status = (
            "COMPLETE_RETEST_SEQUENCE"
        )


    # ======================================================
    # STORE
    # ======================================================

    results.append(
        {
            "trade_index":
                signal_index + 1,

            "trade_date":
                trade_date,

            "direction":
                direction,

            "signal_time":
                signal_time,

            "signal_close":
                signal_close,

            "signal_high":
                signal_high,

            "signal_low":
                signal_low,

            "signal_vwap":
                signal_vwap,

            "orb_high":
                opening_high,

            "orb_low":
                opening_low,

            "broken_zone_low":
                zone_low,

            "broken_zone_high":
                zone_high,

            "broken_level_primary":
                broken_level_primary,

            "broken_level_secondary":
                broken_level_secondary,

            "signal_found":
                True,

            "break_confirmed":
                break_confirmed,

            "move_away":
                move_away,

            "move_away_time":
                move_away_time,

            "move_away_price":
                move_away_price,

            "favorable_extreme":
                favorable_extreme,

            "favorable_extreme_time":
                favorable_extreme_time,

            "retest_reached":
                retest_reached,

            "retest_time":
                retest_time,

            "retest_price":
                retest_price,

            "retest_candle_high":
                retest_candle_high,

            "retest_candle_low":
                retest_candle_low,

            "retest_candle_close":
                retest_candle_close,

            "rejection":
                rejection,

            "rejection_time":
                rejection_time,

            "rejection_price":
                rejection_price,

            "continuation":
                continuation,

            "continuation_time":
                continuation_time,

            "continuation_price":
                continuation_price,

            "status":
                status,
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
        "No results generated."
    )

    raise SystemExit(1)


# ==========================================================
# SUMMARY
# ==========================================================

total = len(result_df)

break_count = int(
    result_df[
        "break_confirmed"
    ].sum()
)

move_count = int(
    result_df[
        "move_away"
    ].sum()
)

retest_count = int(
    result_df[
        "retest_reached"
    ].sum()
)

rejection_count = int(
    result_df[
        "rejection"
    ].sum()
)

continuation_count = int(
    result_df[
        "continuation"
    ].sum()
)


# ==========================================================
# SESSION COUNTS
# ==========================================================

def distinct_sessions(df):
    if df.empty:
        return 0

    return int(
        df[
            "trade_date"
        ].nunique()
    )


break_df = result_df[
    result_df[
        "break_confirmed"
    ]
]

move_df = result_df[
    result_df[
        "move_away"
    ]
]

retest_df = result_df[
    result_df[
        "retest_reached"
    ]
]

rejection_df = result_df[
    result_df[
        "rejection"
    ]
]

complete_df = result_df[
    result_df[
        "continuation"
    ]
]


# ==========================================================
# SUMMARY OUTPUT
# ==========================================================

print()
print("=" * 100)
print(
    "STRUCTURAL ORB + VWAP RETEST SUMMARY"
)
print("=" * 100)

print(
    f"Signals analysed              : {total}"
)

print(
    f"ORB + VWAP break confirmed    : "
    f"{break_count} "
    f"({break_count / total * 100:.2f}%)"
)

print(
    f"Move away after break         : "
    f"{move_count} "
    f"({move_count / total * 100:.2f}%)"
)

print(
    f"Retest broken zone            : "
    f"{retest_count} "
    f"({retest_count / total * 100:.2f}%)"
)

print(
    f"Retest then rejection         : "
    f"{rejection_count} "
    f"({rejection_count / total * 100:.2f}%)"
)

print(
    f"Rejection then continuation   : "
    f"{continuation_count} "
    f"({continuation_count / total * 100:.2f}%)"
)

print()

print(
    f"Distinct sessions with break : "
    f"{distinct_sessions(break_df)}"
)

print(
    f"Distinct sessions with move  : "
    f"{distinct_sessions(move_df)}"
)

print(
    f"Distinct sessions with retest: "
    f"{distinct_sessions(retest_df)}"
)

print(
    f"Distinct sessions with reject: "
    f"{distinct_sessions(rejection_df)}"
)

print(
    f"Distinct sessions complete   : "
    f"{distinct_sessions(complete_df)}"
)


# ==========================================================
# CONDITIONAL RATES
# ==========================================================

print()
print("-" * 100)
print(
    "CONDITIONAL RATES"
)
print("-" * 100)


if break_count:

    print(
        "Move after confirmed break    : "
        f"{move_count / break_count * 100:.2f}%"
    )

    print(
        "Retest after move              : "
        f"{retest_count / break_count * 100:.2f}%"
    )


if move_count:

    print(
        "Retest after move              : "
        f"{retest_count / move_count * 100:.2f}%"
    )


if retest_count:

    print(
        "Rejection after retest         : "
        f"{rejection_count / retest_count * 100:.2f}%"
    )


if rejection_count:

    print(
        "Continuation after rejection   : "
        f"{continuation_count / rejection_count * 100:.2f}%"
    )


# ==========================================================
# SIDE-BY-SIDE BUY / SELL SUMMARY
# ==========================================================

print()
print("=" * 100)
print(
    "BUY / SELL RETEST SUMMARY"
)
print("=" * 100)

side_rows = []


for side in [
    "BUY",
    "SELL",
]:

    subset = result_df[
        result_df[
            "direction"
        ]
        == side
    ]


    if subset.empty:
        continue


    side_rows.append(
        {
            "SIDE":
                side,

            "SIGNALS":
                len(subset),

            "BREAK":
                int(
                    subset[
                        "break_confirmed"
                    ].sum()
                ),

            "MOVE_AWAY":
                int(
                    subset[
                        "move_away"
                    ].sum()
                ),

            "RETEST":
                int(
                    subset[
                        "retest_reached"
                    ].sum()
                ),

            "REJECTION":
                int(
                    subset[
                        "rejection"
                    ].sum()
                ),

            "CONTINUATION":
                int(
                    subset[
                        "continuation"
                    ].sum()
                ),
        }
    )


side_df = pd.DataFrame(
    side_rows
)


print(
    side_df.to_string(
        index=False
    )
)


# ==========================================================
# STATUS SUMMARY
# ==========================================================

print()
print("=" * 100)
print(
    "SEQUENCE STATUS"
)
print("=" * 100)

status_counts = (
    result_df[
        "status"
    ]
    .value_counts()
    .rename_axis("STATUS")
    .reset_index(
        name="COUNT"
    )
)


print(
    status_counts.to_string(
        index=False
    )
)


# ==========================================================
# COMPLETE SEQUENCE EXAMPLES
# ==========================================================

print()
print("=" * 120)
print(
    "COMPLETE RETEST SEQUENCE EXAMPLES"
)
print("=" * 120)


examples = result_df[
    result_df[
        "status"
    ]
    == "COMPLETE_RETEST_SEQUENCE"
].head(20)


if examples.empty:

    print(
        "No complete sequences found."
    )

else:

    for _, row in examples.iterrows():

        print()
        print(
            f"DATE       : {row['trade_date']}"
        )

        print(
            f"SIDE       : {row['direction']}"
        )

        print(
            f"SIGNAL     : {row['signal_time']}"
        )

        print(
            f"ORB HIGH   : "
            f"{fmt_price(row['orb_high'])}"
        )

        print(
            f"ORB LOW    : "
            f"{fmt_price(row['orb_low'])}"
        )

        print(
            f"SIGNAL VWAP: "
            f"{fmt_price(row['signal_vwap'])}"
        )

        print(
            f"BROKEN ZONE: "
            f"{fmt_price(row['broken_zone_low'])}"
            f" -> "
            f"{fmt_price(row['broken_zone_high'])}"
        )

        print(
            f"MOVE AWAY  : "
            f"{fmt_time(row['move_away_time'])}"
            f" @ "
            f"{fmt_price(row['move_away_price'])}"
        )

        print(
            f"RETEST     : "
            f"{fmt_time(row['retest_time'])}"
            f" @ "
            f"{fmt_price(row['retest_price'])}"
        )

        print(
            f"REJECTION  : "
            f"{fmt_time(row['rejection_time'])}"
            f" @ "
            f"{fmt_price(row['rejection_price'])}"
        )

        print(
            f"CONTINUATION: "
            f"{fmt_time(row['continuation_time'])}"
            f" @ "
            f"{fmt_price(row['continuation_price'])}"
        )

        print(
            f"STATUS     : "
            f"{row['status']}"
        )


# ==========================================================
# INDIVIDUAL AUDIT
# ==========================================================

print()
print("=" * 150)
print(
    "INDIVIDUAL SIGNAL AUDIT"
)
print("=" * 150)

audit_columns = [
    "trade_index",
    "trade_date",
    "direction",
    "signal_time",
    "signal_close",
    "orb_low",
    "orb_high",
    "signal_vwap",
    "broken_zone_low",
    "broken_zone_high",
    "move_away",
    "move_away_time",
    "retest_reached",
    "retest_time",
    "rejection",
    "rejection_time",
    "continuation",
    "continuation_time",
    "status",
]


print(
    result_df[
        audit_columns
    ].to_string(
        index=False
    )
)


# ==========================================================
# CANDLE AUDIT FUNCTION
# ==========================================================

def print_candle_window(
    date_value,
    center_time,
    label,
):

    if center_time is None:
        return


    session = market[
        market["datetime"].dt.date
        == date_value
    ].copy()


    if session.empty:
        return

    session = add_session_vwap(session)

    matches = session[
        session["datetime"]
        == pd.Timestamp(center_time)
    ]


    if matches.empty:
        return


    center_index = (
        matches.index[0]
    )


    all_indices = list(
        session.index
    )


    center_position = (
        all_indices.index(
            center_index
        )
    )


    start_position = max(
        0,
        center_position
        - AUDIT_CONTEXT_CANDLES,
    )


    end_position = min(
        len(all_indices),
        center_position
        + AUDIT_CONTEXT_CANDLES
        + 1,
    )


    window = session.iloc[
        start_position:end_position
    ].copy()


    print()
    print(
        "-" * 120
    )

    print(
        f"{label} — {date_value}"
    )

    print(
        "-" * 120
    )

    print(
        window[
            [
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "vwap",
            ]
        ].to_string(
            index=False,
            float_format=lambda x:
                f"{x:.2f}"
        )
    )


# ==========================================================
# DETAILED CANDLE AUDIT
#
# Print first 10 complete sequences.
# ==========================================================

print()
print("=" * 120)
print(
    "DETAILED CANDLE AUDIT — FIRST 10 COMPLETE SEQUENCES"
)
print("=" * 120)


complete_examples = (
    result_df[
        result_df[
            "status"
        ]
        == "COMPLETE_RETEST_SEQUENCE"
    ]
    .head(10)
)


for _, row in complete_examples.iterrows():

    date_value = row[
        "trade_date"
    ]

    print()
    print(
        "#" * 120
    )

    print(
        f"{date_value} "
        f"{row['direction']}"
    )

    print(
        f"Signal time : "
        f"{row['signal_time']}"
    )

    print(
        f"ORB zone    : "
        f"{fmt_price(row['broken_zone_low'])}"
        f" - "
        f"{fmt_price(row['broken_zone_high'])}"
    )

    print_candle_window(
        date_value,
        row["signal_time"],
        "SIGNAL CANDLE",
    )

    print_candle_window(
        date_value,
        row["move_away_time"],
        "MOVE AWAY",
    )

    print_candle_window(
        date_value,
        row["retest_time"],
        "RETEST",
    )

    print_candle_window(
        date_value,
        row["rejection_time"],
        "REJECTION",
    )

    print_candle_window(
        date_value,
        row["continuation_time"],
        "CONTINUATION",
    )


# ==========================================================
# SAVE
# ==========================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ==========================================================
# FINAL
# ==========================================================

print()
print("=" * 110)
print(
    "VERIFICATION COMPLETE"
)
print("=" * 110)

print(
    f"Saved verification CSV:"
)

print(
    OUTPUT_FILE
)

print("=" * 110)