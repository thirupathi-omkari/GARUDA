import sys
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


import main


def run_test():

    print("=" * 60)
    print("GARUDA MAIN APPLICATION FAILURE TEST")
    print("=" * 60)

    with patch(
        "main.create_authenticated_session",
        return_value=None,
    ):

        main.main()

    print("\n" + "=" * 60)
    print("Failure Test Completed Safely")
    print("=" * 60)


if __name__ == "__main__":
    run_test()