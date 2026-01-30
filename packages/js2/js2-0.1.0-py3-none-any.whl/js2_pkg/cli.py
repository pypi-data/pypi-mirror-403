"""CLI entry point for js2 (Just Screen Share)."""

import argparse
import sys
import threading
import time


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="js2",
        description="Just Screen Share - Share your screen with a public URL"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command (local only)
    start_parser = subparsers.add_parser("start", help="Start screen sharing (local only)")
    start_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run server on (default: 8080)"
    )

    # Publish command (with ngrok tunnel)
    publish_parser = subparsers.add_parser("publish", help="Start and publish with public URL")
    publish_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run server on (default: 8080)"
    )

    args = parser.parse_args()

    if args.command == "start":
        start_local(args.port)
    elif args.command == "publish":
        publish(args.port)
    else:
        parser.print_help()
        sys.exit(1)


def start_local(port: int):
    """Start the screen sharing server locally."""
    print()
    print("  JS2 - Just Screen Share")
    print("  ========================")
    print()
    print(f"  Local: http://localhost:{port}")
    print()
    print("  Tip: Use 'js2 publish' to get a public URL")
    print()

    from .server import run_server
    run_server(host="0.0.0.0", port=port)


def publish(port: int):
    """Start server and ngrok tunnel for public URL."""
    print()
    print("  JS2 - Just Screen Share")
    print("  ========================")
    print()

    # Check if pyngrok is installed
    try:
        from pyngrok import ngrok
    except ImportError:
        print("  Error: pyngrok is not installed!")
        print()
        print("  Install it with: pip install pyngrok")
        print()
        sys.exit(1)

    print(f"  Starting server on port {port}...")

    # Start server in background thread
    server_thread = threading.Thread(target=run_server_thread, args=(port,), daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    print("  Starting ngrok tunnel...")
    print()

    try:
        # Create ngrok tunnel
        tunnel = ngrok.connect(port, "http")
        public_url = tunnel.public_url

        print("  " + "=" * 46)
        print(f"  PUBLIC URL: {public_url}")
        print("  " + "=" * 46)
        print()
        print("  Share this URL with your friends!")
        print("  They can view your screen in their browser.")
        print()
        print("  Press Ctrl+C to stop")
        print()

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("  Stopping...")
        ngrok.kill()
    except Exception as e:
        print(f"  Error: {e}")
        print()
        print("  If ngrok requires authentication, run:")
        print("    ngrok authtoken YOUR_TOKEN")
        print()
        print("  Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken")
        sys.exit(1)


def run_server_thread(port: int):
    """Run server in a thread."""
    from .server import run_server
    run_server(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
