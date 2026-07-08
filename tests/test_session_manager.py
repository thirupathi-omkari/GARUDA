import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.session_manager import create_authenticated_session


def main():

    print("=" * 60)
    print("GARUDA SESSION MANAGER TEST")
    print("=" * 60)

    kite = create_authenticated_session()

    if kite:

        print("\nSession Test : SUCCESS")

    else:

        print("\nSession Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()