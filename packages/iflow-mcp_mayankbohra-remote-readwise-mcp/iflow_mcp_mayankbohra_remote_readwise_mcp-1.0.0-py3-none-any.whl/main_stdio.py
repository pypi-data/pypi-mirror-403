"""FastMCP Server for Readwise Reader + Highlights Integration - stdio mode"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import mcp

def main():
    """Entry point for running FastMCP in stdio mode"""
    mcp.run()

if __name__ == "__main__":
    main()
