# PipeScope: Pipeline visualization for CPU microarchitecture traces
#
# Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
# SPDX-License-Identifier: MulanPSL-2.0
#
# Author: Chun Yang

"""Command line interface for PipeScope."""

import argparse
import sys
from pathlib import Path

import uvicorn

from .config import Settings
from .app import create_app


def main():
    """Main entry point for the PipeScope application."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="PipeScope: Pipeline visualization for "
        "CPU microarchitecture traces"
    )
    parser.add_argument(
        "--trace", required=True, help="Path to the trace file"
    )
    args = parser.parse_args()

    # Validate trace file
    trace_file = Path(args.trace)
    if not trace_file.exists():
        print(f"Error: Trace file not found: {args.trace}", file=sys.stderr)
        sys.exit(1)

    # Create application
    settings = Settings(trace_file=trace_file)
    app = create_app(settings)

    # Run uvicorn server
    try:
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nPipeScope server stopped.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
