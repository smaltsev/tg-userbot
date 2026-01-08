#!/usr/bin/env python3
"""
Command-line interface entry point for Telegram Group Scanner.
"""

import sys
import asyncio
from .main import main

def cli_main():
    """CLI entry point that handles async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()