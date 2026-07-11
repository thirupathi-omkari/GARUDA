import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from scanner.candidate_ranker import rank_candidates


def main():

    print("=" * 60)
    print("GARUDA CANDIDATE RANKER TEST")
    print("=" * 60)

    sample_candidates = {

        "STOCK_A": {
            "volume_ratio": 1.50,
            "volatility_pct": 0.10,
            "price_change_pct": 2.00,
        },

        "STOCK_B": {
            "volume_ratio": 1.20,
            "volatility_pct": 0.20,
            "price_change_pct": -4.00,
        },

        "STOCK_C": {
            "volume_ratio": 2.00,
            "volatility_pct": 0.15,
            "price_change_pct": 1.00,
        },
    }

    ranked_candidates = rank_candidates(
        sample_candidates
    )

    print("\nRanked Candidates")
    print("-" * 60)

    for rank, candidate in enumerate(
        ranked_candidates,
        start=1,
    ):

        print(
            f"{rank}. "
            f"{candidate['symbol']:<15} "
            f"Score: {candidate['score']:.4f}"
        )

    print("-" * 60)

    expected_order = [
        "STOCK_B",
        "STOCK_A",
        "STOCK_C",
    ]

    actual_order = [
        candidate["symbol"]
        for candidate in ranked_candidates
    ]

    print("Expected :", expected_order)
    print("Actual   :", actual_order)

    if actual_order == expected_order:
        print("Candidate Ranker Test : SUCCESS")
    else:
        print("Candidate Ranker Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()