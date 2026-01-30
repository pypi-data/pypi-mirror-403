"""
SmartPortfolio CLI Entry Point

This module provides the command-line interface for launching the SmartPortfolio TUI.
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for the smartportfolio command."""
    parser = argparse.ArgumentParser(
        prog="smartportfolio",
        description="SmartPortfolio - GNN + Prophet + DRL Portfolio Optimization TUI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        help="Path to CSV/XLSX file containing ticker symbols",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run integration test with sample tickers",
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Run in headless mode without TUI",
    )
    
    args = parser.parse_args()
    
    if args.test:
        from smartportfolio.pipeline import run_test_pipeline
        run_test_pipeline()
        return 0
    
    if args.no_tui:
        if not args.tickers:
            print("Error: --tickers required in headless mode")
            return 1
        from smartportfolio.pipeline import run_headless_pipeline
        run_headless_pipeline(args.tickers)
        return 0
    
    # Launch the TUI application
    from smartportfolio.app import SmartPortfolioApp
    app = SmartPortfolioApp(ticker_file=args.tickers)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
