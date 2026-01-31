#!/usr/bin/env python3
"""CLI entry point for the AnimAID tutorial application.

Usage:
    animaid-tutorial [--port PORT] [--host HOST]
"""

import argparse
import sys
import webbrowser


def main() -> int:
    """Run the AnimAID tutorial web application."""
    parser = argparse.ArgumentParser(
        description="Run the AnimAID interactive tutorial",
        prog="animaid-tutorial",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8200,
        help="Port to run the server on (default: 8200)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open the browser",
    )

    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("Error: Tutorial dependencies not installed.")
        print("Install with: pip install animaid[tutorial]")
        return 1

    url = f"http://{args.host}:{args.port}"
    print(f"Starting AnimAID Tutorial at {url}")
    print("Press Ctrl+C to stop")

    if not args.no_browser:
        # Open browser after a short delay
        import threading
        import time

        def open_browser() -> None:
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()

    try:
        uvicorn.run(
            "tutorial.app:app",
            host=args.host,
            port=args.port,
            log_level="warning",
        )
    except KeyboardInterrupt:
        print("\nTutorial stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
