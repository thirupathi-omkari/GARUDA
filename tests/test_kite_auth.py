import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.auth import generate_login_url


def main():

    print("=" * 60)
    print("GARUDA KITE AUTH TEST")
    print("=" * 60)

    login_url = generate_login_url()

    if login_url:
        print("\nLogin URL Generation : SUCCESS")
    else:
        print("\nLogin URL Generation : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()