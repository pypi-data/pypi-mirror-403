#!/usr/bin/env python3
"""Wrapper script to run the MCP server with proper path setup."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the server
from server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())