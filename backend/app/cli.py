"""Server admin commands. Run inside the backend container: `python -m app.cli <command>`."""

import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.auth import service
from app.config import get_settings
from app.db import get_engine
from app.security import hash_password, password_problem


def _read_password(from_stdin: bool) -> str | None:
    if from_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    first = getpass.getpass("New password: ")
    second = getpass.getpass("Repeat new password: ")
    if first != second:
        print("Passwords do not match.", file=sys.stderr)
        return None
    return first


def reset_password(username: str, from_stdin: bool) -> int:
    """Set a new password for a user and sign them out everywhere."""
    with Session(get_engine()) as db:
        user = service.find_user_by_username(db, username)
        if user is None:
            print(f"No user named {username!r}.", file=sys.stderr)
            return 1
        password = _read_password(from_stdin)
        if password is None:
            return 1
        if problem := password_problem(password, get_settings().min_password_length):
            print(problem, file=sys.stderr)
            return 1
        user.password_hash = hash_password(password)
        service.delete_user_sessions(db, user.id)
        name = user.username
        db.commit()
    print(f"Password reset for {name}. All of their sessions were signed out.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", metavar="<command>")

    reset = commands.add_parser("reset-password", help="set a new password for a user")
    reset.add_argument("username")
    reset.add_argument(
        "--password-stdin",
        action="store_true",
        help="read the new password from the first line of stdin (for scripts)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "reset-password":
        return reset_password(args.username, args.password_stdin)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
