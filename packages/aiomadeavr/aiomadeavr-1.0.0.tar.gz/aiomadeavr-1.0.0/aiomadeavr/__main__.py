#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Entry point for aiomadeavr
#
# Copyright (c) 2020 François Wautier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
"""Entry point for aiomadeavr CLI/TUI."""

import argparse
import sys

from . import __version__

# Try to import Textual TUI
try:
    from .tui import run_tui

    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False


def main():
    """Main entry point."""
    # Determine program name for examples
    import os

    prog = os.path.basename(sys.argv[0])
    if prog == "__main__.py":
        prog = "python -m aiomadeavr"

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Control Marantz/Denon AVR devices.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {prog}                        # Discovery + TUI (or CLI if Textual not installed)
  {prog} --ip 192.168.1.100     # Direct connection to specific IP
  {prog} --cli                  # Force CLI mode (no Textual)
  {prog} -d                     # Debug mode with log panel
""",
    )
    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        default=None,
        help="Connect directly to receiver at IP address",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force CLI mode (no Textual TUI)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print more information",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print debug information",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Determine which UI to use
    use_tui = HAS_TEXTUAL and not args.cli

    if use_tui:
        run_tui(ip=args.ip, debug=args.debug)
    else:
        if not HAS_TEXTUAL and not args.cli:
            print(
                "Note: Textual not installed. Using CLI mode.",
                file=sys.stderr,
            )
            print(
                "Install Textual for the full TUI: pip install aiomadeavr[tui]",
                file=sys.stderr,
            )
            print(file=sys.stderr)

        from .cli import run_cli

        run_cli(ip=args.ip, debug=args.debug, verbose=args.verbose)


if __name__ == "__main__":
    main()
