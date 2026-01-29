"""
Command-line interface for Agent Flight Recorder.

Provides CLI commands for managing recordings, viewing statistics,
and comparing sessions.
"""

import argparse
import sys
import logging
from typing import Optional

from .recorder import Recorder
from .analytics import Analytics
from .storage import Storage

logger = logging.getLogger(__name__)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Flight Recorder - Debug AI without burning money"
    )
    
    parser.add_argument(
        "command",
        choices=["stats", "clear", "list", "diff"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--session",
        "-s",
        help="Session ID to filter by"
    )
    
    parser.add_argument(
        "--compare",
        "-c",
        help="Second session ID for comparison (used with diff)"
    )
    
    parser.add_argument(
        "--dir",
        "-d",
        default="./afr_logs",
        help="Directory containing recordings"
    )
    
    args = parser.parse_args()
    
    storage = Storage(args.dir)
    analytics = Analytics(storage)
    
    if args.command == "stats":
        analytics.display_stats(args.session)
    
    elif args.command == "clear":
        storage.clear(args.session)
        print(f"✅ Cleared recordings" + (f" for session: {args.session}" if args.session else ""))
    
    elif args.command == "list":
        sessions = storage.get_all_sessions()
        print("\n📋 Recorded Sessions:")
        for session in sessions:
            print(f"  - {session}")
        print()
        
    elif args.command == "diff":
        if not args.session or not args.compare:
            print("❌ Error: diff requires both --session and --compare arguments")
            return
        analytics.diff_sessions(args.session, args.compare)


if __name__ == "__main__":
    main()