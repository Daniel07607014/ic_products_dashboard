"""Generate a bcrypt hash to paste into ``config/auth_config.yaml``.

Usage:
    python deploy/scripts/hash_password.py
    (interactive: prompts for the password, echoes the hash to stdout)

    python deploy/scripts/hash_password.py --password 'MyP@ss'
    (non-interactive; avoid on shared terminals as it lands in shell history)
"""
from __future__ import annotations

import argparse
import getpass

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--password", help="Plaintext password. If omitted, will prompt interactively.")
    args = ap.parse_args()

    pw = args.password or getpass.getpass("Password: ")
    if not pw:
        raise SystemExit("empty password")

    print(hash_password(pw))


if __name__ == "__main__":
    main()
