"""Create a self-signed TLS certificate for running DFIP over HTTPS on localhost.

Usage (from the repository root):
    python scripts/make_dev_cert.py [--days 365] [--force]

Writes certs/dev.crt and certs/dev.key (the certs/ folder is gitignored).
Needs the `openssl` command, which ships with Git for Windows, macOS and Linux.
For local development and demos only: browsers warn about self-signed certificates.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CERT_DIR = Path(__file__).resolve().parents[1] / "certs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=365, help="validity in days (default 365)")
    parser.add_argument("--force", action="store_true", help="overwrite an existing certificate")
    args = parser.parse_args()

    crt, key = CERT_DIR / "dev.crt", CERT_DIR / "dev.key"
    if crt.exists() and key.exists() and not args.force:
        print(f"Certificate already exists: {crt}\nUse --force to replace it.")
        return 0

    openssl = shutil.which("openssl")
    if openssl is None:
        print("openssl was not found. Install Git for Windows (includes openssl) or OpenSSL, then retry.")
        return 1

    CERT_DIR.mkdir(exist_ok=True)
    cmd = [
        openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(key), "-out", str(crt), "-days", str(args.days),
        "-subj", "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
    ]
    # MSYS_NO_PATHCONV stops Git Bash from rewriting the "/CN=localhost" subject as a path.
    env = {**__import__("os").environ, "MSYS_NO_PATHCONV": "1"}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(result.stderr or result.stdout)
        return result.returncode

    print(f"Created {crt} and {key} (valid {args.days} days, CN=localhost).")
    print("Start the API with HTTPS:")
    print("  cd backend")
    print("  uvicorn app.main:app --ssl-keyfile ../certs/dev.key --ssl-certfile ../certs/dev.crt --port 8000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
