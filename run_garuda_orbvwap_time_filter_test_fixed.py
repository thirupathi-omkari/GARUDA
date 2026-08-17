from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "data" / "research"

# IMPORTANT:
# This test deliberately reuses the already-completed GARUDA
# 50% ORB + 2R detailed research results.
#
# Therefore:
#   - no new entry generation
#   - no new exit simulation
#   - no new slippage calculation
#   - no new transaction-cost calculation
#   - no parallel/simplified trade simulator
#
# Only the entry-time filter changes.
DETAIL_PATH = (
    RESEARCH_DIR
    / "garuda_7stock_1year_sl_target_matrix_detail.csv"
)

# Same time hypotheses identified from the diagnostic.
FILTERS = {
    "NO_FILTER": None,
    "ENTRY_LE_12_15": "12:15",
    "ENTRY_LE_13_15": "13:15",
    "ENTRY_LE_14_15": "14:15",
}


def profit_factor(pnl):
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())

    if gross_loss == 0:
        return float("inf")

    return gross_profit / gross_loss


def max_drawdown(pnl):
    equity = pnl.cumsum()
    peak = equity.cummax()
    return float((peak - equity).max())


def summarize(name, cutoff, df):
    pnl = df["net_pnl"].astype(float)

    return {
        "FILTER": name,
        "CUTOFF": cutoff or "NONE",
        "TRADES": len(df),
        "EXCLUDED": 1880 - len(df),
        "WIN_RATE_PCT":
            (pnl > 0).mean() * 100,
        "TOTAL_PNL":
            pnl.sum(),
        "AVG_PNL":
            pnl.mean(),
        "PROFIT_FACTOR":
            profit_factor(pnl),
        "MAX_DRAWDOWN":
            max_drawdown(pnl),
        "STOP_LOSS":
            int(
                (df["exit_reason"] == "STOP_LOSS").sum()
            ),
        "TARGET":
            int(
                (df["exit_reason"] == "TARGET").sum()
            ),
        "END_OF_DAY":
            int(
                (df["exit_reason"] == "END_OF_DAY").sum()
            ),
        "AVG_MFE_R":
            df["mfe_r"].mean(),
        "AVG_MAE_R":
            df["mae_r"].mean(),
    }


def main():
    print()
    print("=" * 120)
    print("GARUDA — ORB+VWAP TIME-OF-DAY FILTER RESEARCH — FIXED")
    print("=" * 120)
    print("Source          : existing GARUDA target-matrix detail file")
    print("Locked cell     : ORB_50 + 2.00R")
    print("Frozen universe : 1,880 entries")
    print("BE              : OFF")
    print("Trailing        : OFF")
    print("Only variable   : entry-time filter")
    print("=" * 120)

    if not DETAIL_PATH.exists():
        raise FileNotFoundError(
            f"Required completed research file not found:\n{DETAIL_PATH}\n"
            "Run/repair the existing target-matrix research first."
        )

    detail = pd.read_csv(DETAIL_PATH)

    required = {
        "SYMBOL",
        "SL_MODE",
        "TARGET_R",
        "entry_candle_time",
        "exit_reason",
        "net_pnl",
        "mfe_r",
        "mae_r",
    }

    missing = required - set(detail.columns)

    if missing:
        raise RuntimeError(
            "Existing detail file is missing required columns: "
            + ", ".join(sorted(missing))
        )

    detail["entry_candle_time"] = pd.to_datetime(
        detail["entry_candle_time"],
        errors="coerce",
    )

    detail["net_pnl"] = pd.to_numeric(
        detail["net_pnl"],
        errors="coerce",
    )

    detail["mfe_r"] = pd.to_numeric(
        detail["mfe_r"],
        errors="coerce",
    )

    detail["mae_r"] = pd.to_numeric(
        detail["mae_r"],
        errors="coerce",
    )

    baseline = detail[
        (detail["SL_MODE"] == "ORB_50")
        & (detail["TARGET_R"] == 2.0)
    ].copy()

    if len(baseline) != 1879:
        raise RuntimeError(
            f"Expected the completed ORB_50 + 2R cell to contain "
            f"1,879 valid trades, got {len(baseline)}."
        )

    # One structural invalid-risk entry exists in ORB_50.
    # It is already absent from the completed detail file.
    # The frozen universe therefore remains 1,880 while the
    # valid baseline trade population is 1,879.
    print()
    print(
        "Completed ORB_50 + 2R valid trades : "
        f"{len(baseline)}"
    )
    print(
        "Frozen entries                     : 1880"
    )
    print(
        "Structural invalid-risk entries    : 1"
    )

    rows = []

    for name, cutoff in FILTERS.items():

        if cutoff is None:
            filtered = baseline.copy()
        else:
            cutoff_time = pd.Timestamp(
                cutoff
            ).time()

            filtered = baseline[
                baseline[
                    "entry_candle_time"
                ].dt.time <= cutoff_time
            ].copy()

        # Chronological ordering is essential for drawdown.
        filtered = filtered.sort_values(
            [
                "exit_time",
                "entry_candle_time",
                "SYMBOL",
            ]
        ).reset_index(drop=True)

        rows.append(
            summarize(
                name,
                cutoff,
                filtered,
            )
        )

    summary = pd.DataFrame(rows)

    # Per-symbol comparison.
    symbol_rows = []

    for name, cutoff in FILTERS.items():

        if cutoff is None:
            filtered = baseline.copy()
        else:
            cutoff_time = pd.Timestamp(
                cutoff
            ).time()

            filtered = baseline[
                baseline[
                    "entry_candle_time"
                ].dt.time <= cutoff_time
            ].copy()

        for symbol, group in filtered.groupby(
            "SYMBOL",
            sort=True,
        ):

            pnl = group[
                "net_pnl"
            ].astype(float)

            symbol_rows.append(
                {
                    "FILTER": name,
                    "SYMBOL": symbol,
                    "TRADES": len(group),
                    "TOTAL_PNL": pnl.sum(),
                    "AVG_PNL": pnl.mean(),
                    "PROFIT_FACTOR":
                        profit_factor(pnl),
                    "WIN_RATE_PCT":
                        (pnl > 0).mean() * 100,
                    "AVG_MFE_R":
                        group["mfe_r"].mean(),
                    "AVG_MAE_R":
                        group["mae_r"].mean(),
                    "STOP_LOSS":
                        int(
                            (
                                group["exit_reason"]
                                == "STOP_LOSS"
                            ).sum()
                        ),
                    "TARGET":
                        int(
                            (
                                group["exit_reason"]
                                == "TARGET"
                            ).sum()
                        ),
                    "END_OF_DAY":
                        int(
                            (
                                group["exit_reason"]
                                == "END_OF_DAY"
                            ).sum()
                        ),
                }
            )

    symbol_summary = pd.DataFrame(
        symbol_rows
    )

    summary_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_time_filter_summary_fixed.csv"
    )

    symbol_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_time_filter_by_symbol_fixed.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    symbol_summary.to_csv(
        symbol_path,
        index=False,
    )

    print()
    print("=" * 120)
    print("7-STOCK AGGREGATE")
    print("=" * 120)
    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("BY SYMBOL")
    print("=" * 120)
    print(
        symbol_summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("OUTPUT FILES")
    print("=" * 120)
    print(f"Summary : {summary_path}")
    print(f"Symbol  : {symbol_path}")

    print()
    print(
        "VALIDATION: This test reused the completed "
        "GARUDA ORB_50 + 2R results and changed only "
        "the entry-time inclusion filter."
    )


if __name__ == "__main__":
    main()
