import argparse
import asyncio
import json
import os
import sys
import stat
import importlib.metadata
from pathlib import Path

from brokenxapi import BrokenXAPI
from brokenxapi.exceptions import BrokenXAPIError

CONFIG_DIR = Path.home() / ".brokenx"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ---------------- CONFIG HELPERS ----------------

def save_api_key(api_key: str):
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": api_key}))
    CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600


def load_api_key():
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("api_key")
    except Exception:
        return None


def require_api_key():
    key = load_api_key()
    if not key:
        print(
            "❌ Not authenticated.\n"
            "Run: brokenx auth <YOUR_API_KEY>",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


# ---------------- CLI CORE ----------------

async def run_cli():
    parser = argparse.ArgumentParser(
        prog="brokenx",
        description="BROKENXAPI Command Line Interface",
    )

    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show BROKENXAPI version",
    )

    sub = parser.add_subparsers(dest="command")

    # ---------- AUTH ----------
    auth_cmd = sub.add_parser("auth", help="Authenticate with API key")
    auth_cmd.add_argument("api_key", help="Your BROKENXAPI key")

    # ---------- SEARCH ----------
    search_cmd = sub.add_parser("search", help="Search YouTube")
    search_cmd.add_argument("query", help="Search query")

    # ---------- DOWNLOAD ----------
    download_cmd = sub.add_parser("download", help="Download media")
    download_cmd.add_argument("video_id", help="YouTube video ID")
    download_cmd.add_argument(
        "-v", "--video",
        action="store_true",
        help="Download video instead of audio",
    )

    args = parser.parse_args()

    # ---------------- VERSION ----------------
    if args.version:
        print(importlib.metadata.version("BROKENXAPI"))
        return

    # ---------------- AUTH ----------------
    if args.command == "auth":
        try:
            # 🔍 Verify key by doing a lightweight call
            async with BrokenXAPI(api_key=args.api_key) as api:
                await api.search("test")  # harmless validation
            save_api_key(args.api_key)
            print("✅ Authentication successful. API key saved.")
        except BrokenXAPIError as e:
            print(f"❌ Authentication failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # ---------------- OTHER COMMANDS ----------------
    api_key = require_api_key()

    async with BrokenXAPI(api_key=api_key) as api:
        if args.command == "search":
            result = await api.search(args.query)
            print(json.dumps(result, indent=2))
            return

        if args.command == "download":
            media_type = "video" if args.video else "audio"
            result = await api.download(args.video_id, media_type)
            print(json.dumps(result, indent=2))
            return

    parser.print_help()


def main():
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        pass
    except BrokenXAPIError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
