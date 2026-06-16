# -*- coding: utf-8 -*-
"""Write production .env keys without overwriting secrets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def upsert_env(key: str, value: str) -> None:
    """Insert or replace one key in .env."""
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    out: list[str] = []
    found = False
    for line in lines:
        if pattern.match(line):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        if out and out[-1].strip():
            out.append("")
        out.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Update production keys in .env")
    parser.add_argument("--public-url", required=True, help="HTTPS public API base URL")
    parser.add_argument("--tunnel-token", default="", help="Cloudflare tunnel token (optional)")
    args = parser.parse_args()
    url = args.public_url.rstrip("/")
    upsert_env("REPORT_API_URL", url)
    upsert_env("API_HOST", "127.0.0.1")
    upsert_env("API_PORT", "8080")
    if args.tunnel_token:
        upsert_env("CLOUDFLARE_TUNNEL_TOKEN", args.tunnel_token)
    print(f"Updated {ENV_PATH}")
    print(f"REPORT_API_URL={url}")


if __name__ == "__main__":
    main()
