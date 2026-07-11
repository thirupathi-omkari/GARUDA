import sys
from pathlib import Path
from datetime import date, timedelta


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.session_manager import create_authenticated_session

from scanner.market_universe import get_test_universe
from scanner.scanner_engine import fetch_universe_data
from scanner.activity_metrics import calculate_universe_metrics
from scanner.activity_filter import filter_active_instruments
from scanner.candidate_ranker import rank_candidates

from strategy.orb_vwap_strategy import ORBVWAPStrategy
from strategy.strategy_engine import evaluate_candidates


def display_ranked_candidates(ranked_candidates):
    """Display GARUDA ranked market candidates."""

    print("\n" + "=" * 100)
    print("GARUDA RANKED MARKET CANDIDATES")
    print("=" * 100)

    if not ranked_candidates:
        print("No active market candidates found.")
        print("=" * 100)
        return

    print(
        f"{'RANK':<8}"
        f"{'SYMBOL':<15}"
        f"{'SCORE':>12}"
        f"{'VOL RATIO':>15}"
        f"{'VOLATILITY':>18}"
        f"{'PRICE CHANGE':>18}"
    )

    print("-" * 100)

    for rank, candidate in enumerate(
        ranked_candidates,
        start=1,
    ):
        print(
            f"{rank:<8}"
            f"{candidate['symbol']:<15}"
            f"{candidate['score']:>12.4f}"
            f"{candidate['volume_ratio']:>15.2f}"
            f"{candidate['volatility_pct']:>17.4f}%"
            f"{candidate['price_change_pct']:>17.2f}%"
        )

    print("=" * 100)


def display_strategy_results(strategy_results):
    """Display GARUDA strategy results with diagnostics."""

    print("\n" + "=" * 110)
    print("GARUDA STRATEGY RESULTS")
    print("=" * 110)

    if not strategy_results:
        print("No strategy results available.")
        print("=" * 110)
        return

    for result in strategy_results:

        print(f"\nSymbol       : {result.symbol}")
        print(f"Strategy     : {result.strategy_name}")
        print(f"Signal       : {result.signal}")

        if result.entry_price is not None:
            print(f"Entry Price  : {result.entry_price:.2f}")
        else:
            print("Entry Price  : -")

        print(f"Reason       : {result.reason}")

        diagnostics = result.diagnostics

        if diagnostics:

            print("-" * 110)
            print("STRATEGY EVIDENCE")

            print(
                f"Opening High : "
                f"{diagnostics['opening_high']:.2f}"
            )

            print(
                f"Opening Low  : "
                f"{diagnostics['opening_low']:.2f}"
            )

            print(
                f"Latest Close : "
                f"{diagnostics['latest_close']:.2f}"
            )

            print(
                f"Latest VWAP  : "
                f"{diagnostics['latest_vwap']:.2f}"
            )

            print("-" * 110)

            print(
                f"Close > Opening High : "
                f"{diagnostics['buy_breakout']}"
            )

            print(
                f"Close > VWAP         : "
                f"{diagnostics['buy_vwap_confirmation']}"
            )

            print(
                f"Close < Opening Low  : "
                f"{diagnostics['sell_breakdown']}"
            )

            print(
                f"Close < VWAP         : "
                f"{diagnostics['sell_vwap_confirmation']}"
            )

        print("=" * 110)


def main():
    """Run the GARUDA market scanner and strategy application."""

    print("\n" + "=" * 100)
    print("GARUDA QUANT LAB")
    print("MARKET SCANNER AND STRATEGY APPLICATION")
    print("=" * 100)

    # STEP 1: CREATE AUTHENTICATED BROKER SESSION

    kite = create_authenticated_session()

    if kite is None:
        print("\nGARUDA Startup Failed.")
        print(
            "Reason: "
            "Authenticated broker session unavailable."
        )
        return

    # STEP 2: LOAD MARKET UNIVERSE

    universe = get_test_universe()

    print(
        f"\nMarket Universe Loaded : "
        f"{len(universe)} instruments"
    )

    # STEP 3: DEFINE HISTORICAL DATA PERIOD

    to_date = date.today() - timedelta(days=1)
    from_date = to_date - timedelta(days=5)

    # STEP 4: FETCH REAL MARKET DATA

    universe_data = fetch_universe_data(
        kite=kite,
        universe=universe,
        from_date=from_date,
        to_date=to_date,
        interval="5minute",
    )

    if not universe_data:
        print("\nGARUDA Scanner Failed.")
        print(
            "Reason: "
            "No valid market data available."
        )
        return

    # STEP 5: CALCULATE ACTIVITY METRICS

    universe_metrics = calculate_universe_metrics(
        universe_data
    )

    # STEP 6: FILTER ACTIVE INSTRUMENTS

    active_instruments = filter_active_instruments(
        universe_metrics=universe_metrics,
        min_volume_ratio=1.0,
        min_volatility_pct=0.05,
    )

    # STEP 7: RANK ACTIVE CANDIDATES

    ranked_candidates = rank_candidates(
        active_instruments
    )

    # STEP 8: CREATE TIME-AWARE ORB + VWAP STRATEGY

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    # STEP 9: EVALUATE RANKED CANDIDATES

    strategy_results = evaluate_candidates(
        strategy=strategy,
        ranked_candidates=ranked_candidates,
        universe_data=universe_data,
    )

    # STEP 10: DISPLAY RANKED CANDIDATES

    display_ranked_candidates(
        ranked_candidates
    )

    # STEP 11: DISPLAY STRATEGY RESULTS

    display_strategy_results(
        strategy_results
    )

    # STEP 12: DISPLAY APPLICATION STATUS

    print("\n" + "=" * 100)
    print("GARUDA APPLICATION STATUS")
    print("=" * 100)

    print(
        f"Universe Instruments : "
        f"{len(universe)}"
    )

    print(
        f"Data Ready           : "
        f"{len(universe_data)}"
    )

    print(
        f"Metrics Calculated   : "
        f"{len(universe_metrics)}"
    )

    print(
        f"Active Instruments   : "
        f"{len(active_instruments)}"
    )

    print(
        f"Ranked Candidates    : "
        f"{len(ranked_candidates)}"
    )

    print(
        f"Strategy Results     : "
        f"{len(strategy_results)}"
    )

    print("-" * 100)
    print(
        "GARUDA MARKET SCANNER AND STRATEGY : SUCCESS"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()