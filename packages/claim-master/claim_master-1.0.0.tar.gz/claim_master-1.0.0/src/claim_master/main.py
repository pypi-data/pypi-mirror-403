import argparse
import json
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin._auth_utils import UserNotFoundError


def initialize_firebase(cred_path: str) -> firebase_admin.App:
    cred = credentials.Certificate(cred_path)
    return firebase_admin.initialize_app(cred)


def create_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claim-master", description="CLI to manage custom claims of Firebase users"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="available commands", required=True
    )

    set_parser = subparsers.add_parser("set", help="set claims of an auth account")
    set_parser.add_argument("uid", type=str, help="the ID or email of the account")
    set_parser.add_argument("data", type=str, help="JSON-formatted claims to add")
    set_parser.add_argument(
        "-k", "--key", help="the path to the Firebase service account key", type=str
    )
    set_parser.set_defaults(func=set)

    view_parser = subparsers.add_parser("view", help="view claims of an auth account")
    view_parser.add_argument("uid", type=str, help="the ID or email of the account")
    view_parser.add_argument(
        "-k", "--key", help="the path to the Firebase service account key", type=str
    )
    view_parser.set_defaults(func=view)

    return parser


def set(args: argparse.Namespace) -> None:
    initialize_firebase(args.key)

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"provided JSON data is invalid: {e}")
        return

    try:
        uid = auth.get_user_by_email(args.uid).uid if "@" in args.uid else args.uid
    except UserNotFoundError:
        print("user not found")
    except Exception as ex:
        print(f"could not get user ID: {ex}")

    try:
        auth.set_custom_user_claims(uid, data)
        print(f"successfully set claims for user {uid} to {data}")
    except UserNotFoundError:
        print("user not found")
    except Exception as ex:
        print(f"could not set custom claims: {ex}")


def view(args: argparse.Namespace) -> None:
    initialize_firebase(args.key)
    try:
        user: auth.UserRecord = (
            auth.get_user_by_email(args.uid)
            if "@" in args.uid
            else auth.get_user(args.uid)
        )
        claims: dict = user.custom_claims

        print(f"claims for user {user.uid}\n")

        if claims is None or len(claims) == 0:
            print("no claims found")
            return

        for k, v in claims.items():
            print(f"{k}: {v}")
    except UserNotFoundError:
        print("user not found")


def main():
    args = create_argparser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
