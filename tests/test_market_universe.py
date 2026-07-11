import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from scanner.market_universe import get_test_universe


def main():

    print("=" * 60)
    print("GARUDA MARKET UNIVERSE TEST")
    print("=" * 60)

    universe = get_test_universe()

    print(f"\nTotal Instruments : {len(universe)}")

    print("\nScanner Universe")
    print("-" * 60)

    for instrument in universe:

        print(
            f"{instrument['exchange']}:"
            f"{instrument['tradingsymbol']}"
        )

    print("-" * 60)

    if len(universe) == 5:
        print("Market Universe Test : SUCCESS")
    else:
        print("Market Universe Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()