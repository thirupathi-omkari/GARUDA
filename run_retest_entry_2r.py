from pathlib import Path

import pandas as pd


# ============================================================
# GARUDA RESEARCH
# ORB + VWAP BREAK -> MOVE -> RETEST -> REJECTION -> 2R
#
# IMPORTANT:
# This is RESEARCH ONLY.
#
# Sequence:
#
#   ORB + VWAP BREAK
#          |
#          v
#   FIRST FAVORABLE MOVE
#          |
#          v
#      FIRST RETEST
#          |
#          v
#       REJECTION
#          |
#          v
#   NEXT CANDLE OPEN ENTRY
#          |
#          v
#   REJECTION-CANDLE STRUCTURAL SL
#          |
#          v
#          2R
#
# The script deliberately does NOT use the eventual maximum
# excursion to locate the retest.
# ============================================================


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent

DATA_FILE = (
    ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "retest_entry_2r_infy_corrected.csv"
)

SYMBOL = "INFY"

ORB_START = "09:15"
ORB_END = "09:30"

TARGET_R = 2.0

COST_RATE_PCT = 0.10
SLIPPAGE_PCT = 0.05

QUANTITY = 1

# Optional safety limit.
# None = search entire remaining session.
MAX_RETEST_CANDLES = None


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Data file not found:\n{DATA_FILE}"
    )


df = pd.read_csv(DATA_FILE)


required = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
}

missing = required - set(df.columns)

if missing:
    raise ValueError(
        f"Missing columns: {sorted(missing)}"
    )


df["datetime"] = pd.to_datetime(
    df["datetime"]
)

df = (
    df
    .sort_values("datetime")
    .reset_index(drop=True)
)


# ============================================================
# VWAP
# ============================================================

def calculate_session_vwap(session):

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


# ============================================================
# PREPARE SESSION
# ============================================================

def prepare_session(group):

    session = (
        group
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    session = calculate_session_vwap(
        session
    )

    times = (
        session["datetime"]
        .dt.strftime("%H:%M")
    )

    orb = session[
        (times >= ORB_START)
        &
        (times < ORB_END)
    ]

    if orb.empty:
        return None

    orb_high = float(
        orb["high"].max()
    )

    orb_low = float(
        orb["low"].min()
    )

    orb_range = (
        orb_high
        - orb_low
    )

    if orb_range <= 0:
        return None

    session["orb_high"] = orb_high
    session["orb_low"] = orb_low
    session["orb_range"] = orb_range

    return session


# ============================================================
# FIND FIRST ORB + VWAP BREAK
# ============================================================

def find_first_break(session):

    orb_high = float(
        session["orb_high"].iloc[0]
    )

    orb_low = float(
        session["orb_low"].iloc[0]
    )

    orb_range = float(
        session["orb_range"].iloc[0]
    )

    times = (
        session["datetime"]
        .dt.strftime("%H:%M")
    )

    for i in range(len(session)):

        candle = session.iloc[i]

        if (
            times.iloc[i]
            < ORB_END
        ):
            continue

        close = float(
            candle["close"]
        )

        vwap = float(
            candle["vwap"]
        )

        # ----------------------------------------------------
        # BUY BREAK
        # ----------------------------------------------------

        if (
            close > orb_high
            and
            close > vwap
        ):

            return {
                "index": i,
                "direction": "BUY",
                "break_time":
                    candle["datetime"],
                "break_open":
                    float(candle["open"]),
                "break_high":
                    float(candle["high"]),
                "break_low":
                    float(candle["low"]),
                "break_close":
                    close,
                "break_vwap":
                    vwap,
                "broken_level":
                    orb_high,
                "orb_high":
                    orb_high,
                "orb_low":
                    orb_low,
                "orb_range":
                    orb_range,
            }

        # ----------------------------------------------------
        # SELL BREAK
        # ----------------------------------------------------

        if (
            close < orb_low
            and
            close < vwap
        ):

            return {
                "index": i,
                "direction": "SELL",
                "break_time":
                    candle["datetime"],
                "break_open":
                    float(candle["open"]),
                "break_high":
                    float(candle["high"]),
                "break_low":
                    float(candle["low"]),
                "break_close":
                    close,
                "break_vwap":
                    vwap,
                "broken_level":
                    orb_low,
                "orb_high":
                    orb_high,
                "orb_low":
                    orb_low,
                "orb_range":
                    orb_range,
            }

    return None


# ============================================================
# FIRST MOVE AWAY
# ============================================================

def find_first_move_away(
    session,
    break_event,
):
    """
    CRITICAL:

    We find the FIRST favorable movement after the
    break.

    We DO NOT find the maximum favorable excursion.

    This fixes the sequencing bug in the previous script.
    """

    break_index = (
        break_event["index"]
    )

    direction = (
        break_event["direction"]
    )

    broken_level = (
        break_event["broken_level"]
    )

    # Start AFTER the break candle.
    start = break_index + 1

    for i in range(
        start,
        len(session),
    ):

        candle = session.iloc[i]

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        if direction == "BUY":

            favorable_move = (
                high
                - broken_level
            )

        else:

            favorable_move = (
                broken_level
                - low
            )

        # Any positive favorable excursion
        # qualifies as movement away.
        if favorable_move > 0:

            return {
                "index": i,
                "time":
                    candle["datetime"],
                "price":
                    (
                        high
                        if direction == "BUY"
                        else low
                    ),
                "excursion":
                    favorable_move,
                "excursion_orb_r":
                    (
                        favorable_move
                        / break_event[
                            "orb_range"
                        ]
                    ),
            }

    return None


# ============================================================
# RETEST DETECTION
# ============================================================

def detect_retest(
    session,
    break_event,
    move_event,
    mode,
):
    """
    Search ONLY AFTER the FIRST MOVE AWAY.

    ORB_LEVEL:
        candle touches broken ORB level.

    ORB_VWAP_ZONE:
        candle overlaps the zone between
        ORB boundary and breakout VWAP.
    """

    direction = (
        break_event["direction"]
    )

    broken_level = (
        break_event["broken_level"]
    )

    break_vwap = (
        break_event["break_vwap"]
    )

    start = (
        move_event["index"]
        + 1
    )

    end = len(session)

    if MAX_RETEST_CANDLES is not None:

        end = min(
            end,
            start + MAX_RETEST_CANDLES,
        )

    zone_low = min(
        broken_level,
        break_vwap,
    )

    zone_high = max(
        broken_level,
        break_vwap,
    )

    for i in range(
        start,
        end,
    ):

        candle = session.iloc[i]

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        # ----------------------------------------------------
        # ORB LEVEL RETEST
        # ----------------------------------------------------

        if mode == "ORB_LEVEL":

            retest = (
                low <= broken_level
                <= high
            )

        # ----------------------------------------------------
        # ORB + VWAP ZONE RETEST
        # ----------------------------------------------------

        elif mode == "ORB_VWAP_ZONE":

            retest = (
                high >= zone_low
                and
                low <= zone_high
            )

        else:

            raise ValueError(
                f"Unknown mode: {mode}"
            )

        if retest:

            return {
                "index": i,
                "time":
                    candle["datetime"],
                "high":
                    high,
                "low":
                    low,
                "close":
                    float(
                        candle["close"]
                    ),
                "vwap":
                    float(
                        candle["vwap"]
                    ),
            }

    return None


# ============================================================
# REJECTION DETECTION
# ============================================================

def detect_rejection(
    session,
    break_event,
    retest_event,
):
    """
    Retest candle is NOT the entry.

    We require a FOLLOWING candle to close back
    on the breakout side.

    BUY:
        rejection close > broken ORB high

    SELL:
        rejection close < broken ORB low
    """

    direction = (
        break_event["direction"]
    )

    broken_level = (
        break_event["broken_level"]
    )

    start = (
        retest_event["index"]
        + 1
    )

    for i in range(
        start,
        len(session),
    ):

        candle = session.iloc[i]

        close = float(
            candle["close"]
        )

        if direction == "BUY":

            if close > broken_level:

                return {
                    "index": i,
                    "time":
                        candle["datetime"],
                    "open":
                        float(
                            candle["open"]
                        ),
                    "high":
                        float(
                            candle["high"]
                        ),
                    "low":
                        float(
                            candle["low"]
                        ),
                    "close":
                        close,
                }

        else:

            if close < broken_level:

                return {
                    "index": i,
                    "time":
                        candle["datetime"],
                    "open":
                        float(
                            candle["open"]
                        ),
                    "high":
                        float(
                            candle["high"]
                        ),
                    "low":
                        float(
                            candle["low"]
                        ),
                    "close":
                        close,
                }

    return None


# ============================================================
# SLIPPAGE
# ============================================================

def entry_price_with_slippage(
    price,
    direction,
):

    slip = (
        price
        * SLIPPAGE_PCT
        / 100.0
    )

    if direction == "BUY":
        return price + slip

    return price - slip


def exit_price_with_slippage(
    price,
    direction,
):

    slip = (
        price
        * SLIPPAGE_PCT
        / 100.0
    )

    if direction == "BUY":
        return price - slip

    return price + slip


# ============================================================
# SIMULATE TRADE
# ============================================================

def simulate_trade(
    session,
    break_event,
    move_event,
    retest_event,
    rejection_event,
    mode,
):
    """
    Entry:
        OPEN of candle immediately after rejection.

    SL:
        BUY  -> rejection LOW
        SELL -> rejection HIGH

    Target:
        2R
    """

    direction = (
        break_event["direction"]
    )

    # --------------------------------------------------------
    # No rejection
    # --------------------------------------------------------

    if rejection_event is None:

        return {
            "status":
                "RETEST_NO_REJECTION",
            "mode":
                mode,
            "direction":
                direction,
            "break_time":
                break_event["break_time"],
            "move_time":
                move_event["time"],
            "retest_time":
                retest_event["time"],
        }

    rejection_index = (
        rejection_event["index"]
    )

    entry_index = (
        rejection_index + 1
    )

    # --------------------------------------------------------
    # No next candle
    # --------------------------------------------------------

    if entry_index >= len(session):

        return {
            "status":
                "NO_ENTRY_CANDLE",
            "mode":
                mode,
            "direction":
                direction,
            "break_time":
                break_event["break_time"],
            "move_time":
                move_event["time"],
            "retest_time":
                retest_event["time"],
            "rejection_time":
                rejection_event["time"],
        }

    entry_candle = (
        session.iloc[entry_index]
    )

    raw_entry = float(
        entry_candle["open"]
    )

    entry = (
        entry_price_with_slippage(
            raw_entry,
            direction,
        )
    )

    # --------------------------------------------------------
    # STRUCTURAL STOP
    # --------------------------------------------------------

    if direction == "BUY":

        stop_loss = (
            rejection_event["low"]
        )

        risk = (
            entry
            - stop_loss
        )

    else:

        stop_loss = (
            rejection_event["high"]
        )

        risk = (
            stop_loss
            - entry
        )

    # --------------------------------------------------------
    # INVALID RISK
    # --------------------------------------------------------

    if risk <= 0:

        return {
            "status":
                "INVALID_RISK",
            "mode":
                mode,
            "direction":
                direction,
            "break_time":
                break_event["break_time"],
            "move_time":
                move_event["time"],
            "retest_time":
                retest_event["time"],
            "rejection_time":
                rejection_event["time"],
            "entry_time":
                entry_candle["datetime"],
            "raw_entry":
                raw_entry,
            "entry":
                entry,
            "stop_loss":
                stop_loss,
            "risk":
                risk,
        }

    # --------------------------------------------------------
    # 2R TARGET
    # --------------------------------------------------------

    if direction == "BUY":

        target = (
            entry
            + TARGET_R * risk
        )

    else:

        target = (
            entry
            - TARGET_R * risk
        )

    # --------------------------------------------------------
    # EXIT SIMULATION
    # --------------------------------------------------------

    max_favorable = 0.0
    max_adverse = 0.0

    exit_price = None
    exit_time = None
    exit_reason = None
    ambiguous = False

    future = session.iloc[
        entry_index:
    ]

    for _, candle in future.iterrows():

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        # -----------------------------------------------
        # MFE / MAE
        # -----------------------------------------------

        if direction == "BUY":

            favorable = max(
                0.0,
                high - entry,
            )

            adverse = max(
                0.0,
                entry - low,
            )

            stop_hit = (
                low <= stop_loss
            )

            target_hit = (
                high >= target
            )

        else:

            favorable = max(
                0.0,
                entry - low,
            )

            adverse = max(
                0.0,
                high - entry,
            )

            stop_hit = (
                high >= stop_loss
            )

            target_hit = (
                low <= target
            )

        max_favorable = max(
            max_favorable,
            favorable,
        )

        max_adverse = max(
            max_adverse,
            adverse,
        )

        # -----------------------------------------------
        # BOTH HIT SAME CANDLE
        #
        # Preserve GARUDA conservative behavior:
        # STOP first.
        # -----------------------------------------------

        if (
            stop_hit
            and target_hit
        ):

            ambiguous = True

            exit_price = stop_loss

            exit_reason = (
                "STOP_LOSS_AMBIGUOUS"
            )

            exit_time = (
                candle["datetime"]
            )

            break

        if stop_hit:

            exit_price = stop_loss

            exit_reason = (
                "STOP_LOSS"
            )

            exit_time = (
                candle["datetime"]
            )

            break

        if target_hit:

            exit_price = target

            exit_reason = (
                "TARGET"
            )

            exit_time = (
                candle["datetime"]
            )

            break

    # --------------------------------------------------------
    # END OF DAY
    # --------------------------------------------------------

    if exit_price is None:

        final_candle = future.iloc[-1]

        exit_price = float(
            final_candle["close"]
        )

        exit_time = (
            final_candle["datetime"]
        )

        exit_reason = (
            "END_OF_DAY"
        )

    # --------------------------------------------------------
    # EXIT SLIPPAGE
    # --------------------------------------------------------

    execution_exit = (
        exit_price_with_slippage(
            exit_price,
            direction,
        )
    )

    # --------------------------------------------------------
    # PNL
    # --------------------------------------------------------

    if direction == "BUY":

        gross_pnl = (
            execution_exit
            - entry
        ) * QUANTITY

    else:

        gross_pnl = (
            entry
            - execution_exit
        ) * QUANTITY

    turnover = (
        entry * QUANTITY
        +
        execution_exit * QUANTITY
    )

    costs = (
        turnover
        * COST_RATE_PCT
        / 100.0
    )

    net_pnl = (
        gross_pnl
        - costs
    )

    # --------------------------------------------------------
    # R METRICS
    # --------------------------------------------------------

    mfe_r = (
        max_favorable
        / risk
    )

    mae_r = (
        max_adverse
        / risk
    )

    pnl_r = (
        net_pnl
        / risk
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "status":
            "TRADE",

        "mode":
            mode,

        "trade_date":
            break_event["break_time"].date(),

        "direction":
            direction,

        "orb_high":
            break_event["orb_high"],

        "orb_low":
            break_event["orb_low"],

        "break_time":
            break_event["break_time"],

        "break_close":
            break_event["break_close"],

        "break_vwap":
            break_event["break_vwap"],

        "broken_level":
            break_event["broken_level"],

        "move_time":
            move_event["time"],

        "move_price":
            move_event["price"],

        "move_excursion":
            move_event["excursion"],

        "move_excursion_orb_r":
            move_event[
                "excursion_orb_r"
            ],

        "retest_time":
            retest_event["time"],

        "retest_high":
            retest_event["high"],

        "retest_low":
            retest_event["low"],

        "retest_close":
            retest_event["close"],

        "retest_vwap":
            retest_event["vwap"],

        "rejection_time":
            rejection_event["time"],

        "rejection_open":
            rejection_event["open"],

        "rejection_high":
            rejection_event["high"],

        "rejection_low":
            rejection_event["low"],

        "rejection_close":
            rejection_event["close"],

        "entry_time":
            entry_candle["datetime"],

        "raw_entry_price":
            raw_entry,

        "entry_price":
            entry,

        "stop_loss":
            stop_loss,

        "risk":
            risk,

        "target":
            target,

        "exit_time":
            exit_time,

        "raw_exit_price":
            exit_price,

        "exit_price":
            execution_exit,

        "exit_reason":
            exit_reason,

        "ambiguous":
            ambiguous,

        "mfe":
            max_favorable,

        "mae":
            max_adverse,

        "mfe_r":
            mfe_r,

        "mae_r":
            mae_r,

        "pnl_r":
            pnl_r,

        "gross_pnl":
            gross_pnl,

        "costs":
            costs,

        "net_pnl":
            net_pnl,
    }


# ============================================================
# STRUCTURAL EVENT ANALYSIS
# ============================================================

def analyse_mode(
    mode,
):
    """
    Detect one structural sequence per session.

    This is the key validation layer.
    """

    rows = []

    for trade_date, group in df.groupby(
        df["datetime"].dt.date
    ):

        session = prepare_session(
            group
        )

        if session is None:
            continue

        break_event = find_first_break(
            session
        )

        if break_event is None:
            continue

        move_event = find_first_move_away(
            session,
            break_event,
        )

        if move_event is None:

            rows.append(
                {
                    "status":
                        "BREAK_NO_MOVE",
                    "trade_date":
                        trade_date,
                    "mode":
                        mode,
                    "direction":
                        break_event[
                            "direction"
                        ],
                    "break_time":
                        break_event[
                            "break_time"
                        ],
                }
            )

            continue

        retest_event = detect_retest(
            session,
            break_event,
            move_event,
            mode,
        )

        if retest_event is None:

            rows.append(
                {
                    "status":
                        "MOVE_NO_RETEST",
                    "trade_date":
                        trade_date,
                    "mode":
                        mode,
                    "direction":
                        break_event[
                            "direction"
                        ],
                    "break_time":
                        break_event[
                            "break_time"
                        ],
                    "move_time":
                        move_event[
                            "time"
                        ],
                }
            )

            continue

        rejection_event = detect_rejection(
            session,
            break_event,
            retest_event,
        )

        result = simulate_trade(
            session=session,
            break_event=break_event,
            move_event=move_event,
            retest_event=retest_event,
            rejection_event=rejection_event,
            mode=mode,
        )

        result["trade_date"] = (
            trade_date
        )

        rows.append(result)

    return pd.DataFrame(rows)


# ============================================================
# STRUCTURAL SUMMARY
# ============================================================

def print_structural_summary(
    results,
    mode,
):
    print()
    print("=" * 110)
    print(
        f"STRUCTURAL VALIDATION — {mode}"
    )
    print("=" * 110)

    if results.empty:

        print("No break events.")

        return

    total = len(results)

    move_count = int(
        (
            results["status"]
            != "BREAK_NO_MOVE"
        ).sum()
    )

    retest_count = int(
        results["status"].isin(
            [
                "TRADE",
                "RETEST_NO_REJECTION",
                "INVALID_RISK",
                "NO_ENTRY_CANDLE",
            ]
        ).sum()
    )

    rejection_count = int(
        results["status"].isin(
            [
                "TRADE",
                "INVALID_RISK",
                "NO_ENTRY_CANDLE",
            ]
        ).sum()
    )

    print(
        f"BREAK EVENTS             : "
        f"{total}"
    )

    print(
        f"MOVE AWAY                : "
        f"{move_count} "
        f"({move_count / total * 100:.2f}%)"
    )

    print(
        f"RETEST                   : "
        f"{retest_count} "
        f"({retest_count / total * 100:.2f}%)"
    )

    if retest_count > 0:

        print(
            f"REJECTION AFTER RETEST  : "
            f"{rejection_count} "
            f"({rejection_count / retest_count * 100:.2f}%)"
        )

    print(
        f"NO MOVE                  : "
        f"{int((results['status'] == 'BREAK_NO_MOVE').sum())}"
    )

    print(
        f"NO RETEST                : "
        f"{int((results['status'] == 'MOVE_NO_RETEST').sum())}"
    )

    print(
        f"NO REJECTION             : "
        f"{int((results['status'] == 'RETEST_NO_REJECTION').sum())}"
    )


# ============================================================
# TRADE SUMMARY
# ============================================================

def print_trade_summary(
    results,
    mode,
):
    trades = results[
        results["status"]
        == "TRADE"
    ].copy()

    print()
    print("=" * 110)
    print(
        f"RETEST ENTRY RESULTS — {mode}"
    )
    print("=" * 110)

    if trades.empty:

        print("No executable trades.")

        return

    targets = int(
        (
            trades["exit_reason"]
            == "TARGET"
        ).sum()
    )

    stops = int(
        trades[
            "exit_reason"
        ]
        .str.startswith(
            "STOP_LOSS"
        ).sum()
    )

    eod = int(
        (
            trades["exit_reason"]
            == "END_OF_DAY"
        ).sum()
    )

    winners = int(
        (
            trades["net_pnl"]
            > 0
        ).sum()
    )

    losers = int(
        (
            trades["net_pnl"]
            < 0
        ).sum()
    )

    gross_profit = float(
        trades.loc[
            trades["net_pnl"] > 0,
            "net_pnl",
        ].sum()
    )

    gross_loss = abs(
        float(
            trades.loc[
                trades["net_pnl"] < 0,
                "net_pnl",
            ].sum()
        )
    )

    pf = (
        gross_profit / gross_loss
        if gross_loss > 0
        else float("inf")
    )

    print(
        f"ENTRIES                 : "
        f"{len(trades)}"
    )

    print(
        f"TARGET                  : "
        f"{targets}"
    )

    print(
        f"STOP_LOSS               : "
        f"{stops}"
    )

    print(
        f"END_OF_DAY              : "
        f"{eod}"
    )

    print(
        f"AMBIGUOUS               : "
        f"{int(trades['ambiguous'].sum())}"
    )

    print(
        f"WINNING_TRADES          : "
        f"{winners}"
    )

    print(
        f"LOSING_TRADES           : "
        f"{losers}"
    )

    print(
        f"WIN_RATE_PCT            : "
        f"{winners / len(trades) * 100:.2f}"
    )

    print(
        f"TARGET_RATE_PCT         : "
        f"{targets / len(trades) * 100:.2f}"
    )

    print(
        f"AVG_MFE_R               : "
        f"{trades['mfe_r'].mean():.3f}"
    )

    print(
        f"MEDIAN_MFE_R            : "
        f"{trades['mfe_r'].median():.3f}"
    )

    print(
        f"AVG_MAE_R               : "
        f"{trades['mae_r'].mean():.3f}"
    )

    print(
        f"MEDIAN_MAE_R            : "
        f"{trades['mae_r'].median():.3f}"
    )

    print(
        f"AVG_PNL                 : "
        f"{trades['net_pnl'].mean():.2f}"
    )

    print(
        f"TOTAL_PNL               : "
        f"{trades['net_pnl'].sum():.2f}"
    )

    print(
        f"PROFIT_FACTOR           : "
        f"{pf:.3f}"
    )


# ============================================================
# AUDIT
# ============================================================

def print_audit(
    results,
    mode,
):
    trades = results[
        results["status"]
        == "TRADE"
    ].copy()

    print()
    print("=" * 180)
    print(
        f"TRADE AUDIT — {mode}"
    )
    print("=" * 180)

    if trades.empty:

        print("No trades.")

        return

    columns = [
        "trade_date",
        "direction",
        "break_time",
        "move_time",
        "retest_time",
        "rejection_time",
        "entry_time",
        "raw_entry_price",
        "entry_price",
        "stop_loss",
        "risk",
        "target",
        "exit_time",
        "exit_price",
        "exit_reason",
        "mfe_r",
        "mae_r",
        "pnl_r",
        "net_pnl",
        "ambiguous",
    ]

    print(
        trades[
            columns
        ].to_string(
            index=False
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 110)
    print(
        "GARUDA — CORRECTED STRUCTURAL RETEST ENTRY RESEARCH"
    )
    print("=" * 110)

    print(
        f"DATA       : {DATA_FILE}"
    )

    print(
        "SEQUENCE   : BREAK -> FIRST MOVE -> RETEST -> REJECTION -> NEXT OPEN"
    )

    print(
        "SL         : REJECTION CANDLE HIGH/LOW"
    )

    print(
        "TARGET     : 2R"
    )

    print(
        "IMPORTANT  : First move is used, NOT maximum excursion."
    )

    # --------------------------------------------------------
    # RUN ORB LEVEL
    # --------------------------------------------------------

    orb_results = analyse_mode(
        "ORB_LEVEL"
    )

    print_structural_summary(
        orb_results,
        "ORB_LEVEL",
    )

    print_trade_summary(
        orb_results,
        "ORB_LEVEL",
    )

    print_audit(
        orb_results,
        "ORB_LEVEL",
    )

    # --------------------------------------------------------
    # RUN ORB + VWAP ZONE
    # --------------------------------------------------------

    zone_results = analyse_mode(
        "ORB_VWAP_ZONE"
    )

    print_structural_summary(
        zone_results,
        "ORB_VWAP_ZONE",
    )

    print_trade_summary(
        zone_results,
        "ORB_VWAP_ZONE",
    )

    print_audit(
        zone_results,
        "ORB_VWAP_ZONE",
    )

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    def compact(results, mode):

        trades = results[
            results["status"]
            == "TRADE"
        ]

        if trades.empty:

            return {
                "MODE":
                    mode,
                "BREAKS":
                    len(results),
                "RETESTS":
                    int(
                        results["status"].isin(
                            [
                                "TRADE",
                                "RETEST_NO_REJECTION",
                                "INVALID_RISK",
                                "NO_ENTRY_CANDLE",
                            ]
                        ).sum()
                    ),
                "REJECTIONS":
                    0,
                "ENTRIES":
                    0,
                "TARGET":
                    0,
                "STOP":
                    0,
                "TOTAL_PNL":
                    0.0,
            }

        return {
            "MODE":
                mode,

            "BREAKS":
                len(results),

            "RETESTS":
                int(
                    results["status"].isin(
                        [
                            "TRADE",
                            "RETEST_NO_REJECTION",
                            "INVALID_RISK",
                            "NO_ENTRY_CANDLE",
                        ]
                    ).sum()
                ),

            "REJECTIONS":
                len(trades),

            "ENTRIES":
                len(trades),

            "TARGET":
                int(
                    (
                        trades[
                            "exit_reason"
                        ]
                        == "TARGET"
                    ).sum()
                ),

            "STOP":
                int(
                    trades[
                        "exit_reason"
                    ]
                    .str.startswith(
                        "STOP_LOSS"
                    ).sum()
                ),

            "TOTAL_PNL":
                trades[
                    "net_pnl"
                ].sum(),
        }

    comparison = pd.DataFrame(
        [
            compact(
                orb_results,
                "ORB_LEVEL",
            ),
            compact(
                zone_results,
                "ORB_VWAP_ZONE",
            ),
        ]
    )

    print()
    print("=" * 110)
    print(
        "FINAL COMPARISON"
    )
    print("=" * 110)

    print(
        comparison.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    combined = pd.concat(
        [
            orb_results,
            zone_results,
        ],
        ignore_index=True,
    )

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 110)
    print(
        "SAVED:"
    )

    print(
        OUTPUT_FILE
    )

    print("=" * 110)


if __name__ == "__main__":
    main()