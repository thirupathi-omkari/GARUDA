import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.session_manager import create_authenticated_session
from data.instrument_resolver import resolve_instrument_token


def main():

    print("=" * 60)
    print("GARUDA INSTRUMENT RESOLVER TEST")
    print("=" * 60)

    kite = create_authenticated_session()

    if kite is None:
        print("\n❌ Test Failed: Authenticated session unavailable.")
        return

    instrument_token = resolve_instrument_token(
        kite=kite,
        tradingsymbol="NIFTY 50",
        exchange="NSE",
    )

    if instrument_token is None:
        print("\nInstrument Resolver Test : FAILED")
        return

    print("\n" + "=" * 60)
    print("GARUDA INSTRUMENT RESOLVER")
    print("=" * 60)

    print("Symbol Resolution : SUCCESS")
    print(f"Resolved Token    : {instrument_token}")

    print("=" * 60)


if __name__ == "__main__":
    main()