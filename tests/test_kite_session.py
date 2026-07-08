import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.auth import generate_access_token


def main():

    print("=" * 60)
    print("GARUDA KITE SESSION TEST")
    print("=" * 60)

    request_token = input(
        "\nPaste request token here: "
    ).strip()

    kite, access_token = generate_access_token(request_token)

    profile = kite.profile()

    print("\n" + "=" * 60)
    print("GARUDA AUTHENTICATED CONNECTION")
    print("=" * 60)

    print(f"User ID       : {profile.get('user_id')}")
    print(f"User Name     : {profile.get('user_name')}")
    print(f"Broker        : {profile.get('broker')}")
    print(f"User Type     : {profile.get('user_type')}")

    print("\nProfile Fetch : SUCCESS")
    print("Module Status : AUTHENTICATED")

    print("=" * 60)


if __name__ == "__main__":
    main()