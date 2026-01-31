from __future__ import annotations

import argparse
import textwrap
import os
import platform
import webbrowser
from importlib.metadata import PackageNotFoundError, version as pkg_version

from .web import create_app


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codecam", description="Share code selections with an LLM"
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Project path (default: .)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port", type=int, default=0, help="0 chooses a random free port"
    )
    parser.add_argument(
        "--no-auto-shutdown",
        action="store_true",
        help=textwrap.dedent(
            """\
            Disable shutting down when the browser tab closes or the apii goes idle.
            Useful for remote-port forwarding / SSH tunnels where pagehide events can be unreliable.
            """
        ).strip(),
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    args = parser.parse_args()

    if args.version:
        try:
            print(pkg_version("codecam"))
        except PackageNotFoundError:
            # likely running from a checkout without an installed distribution
            # e.g. `python -m codecam.cli` without `pip install -e .`
            print("unknown")
        return

    app = create_app(args.path, auto_shutdown=not args.no_auto_shutdown)

    # pick free port if 0
    import socket

    if args.port == 0:
        with socket.socket() as s:
            s.bind((args.host, 0))
            args.port = s.getsockname()[1]

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        if platform.system() == "Linux" and "Microsoft" in platform.uname().release:
            os.system(f"powershell.exe Start-Process {url}")  # WSL case
        else:
            webbrowser.open(url)

    # threaded True to ensure shutdown handler doesn't deadlock
    app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)
