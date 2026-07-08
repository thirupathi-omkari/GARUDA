import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.session_manager import create_authenticated_session


def main():

    print("=" * 60)
    print("GARUDA BROKER INTEGRATION TEST")
    print("=" * 60)

    # Create and verify authenticated Kite session
    kite = create_authenticated_session()

    if kite is None:
        print("\n❌ Broker Integration Test : FAILED")
        print("Reason: Authenticated Kite session unavailable.")
        return

    # Fetch profile to verify authenticated API communication
    profile = kite.profile()

    print("\n" + "=" * 60)
    print("BROKER CONNECTION DETAILS")
    print("=" * 60)

    print(f"Broker          : {profile.get('broker')}")
    print(f"User Type       : {profile.get('user_type')}")

    # Final status
    print("\n" + "=" * 60)
    print("GARUDA MODULE 3 STATUS")
    print("=" * 60)

    print("Kite Client          : READY")
    print("Authentication       : VERIFIED")
    print("Session Management   : WORKING")
    print("Broker Communication : SUCCESS")

    print("-" * 60)
    print("MODULE 3 BROKER INTEGRATION : PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()