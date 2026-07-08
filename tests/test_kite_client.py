import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.kite_client import create_kite_client


def main():

    print("=" * 60)
    print("GARUDA KITE CLIENT TEST")
    print("=" * 60)

    kite = create_kite_client()

    print(f"Client Type : {type(kite).__name__}")
    print("Test Status : SUCCESS")

    print("=" * 60)


if __name__ == "__main__":
    main()