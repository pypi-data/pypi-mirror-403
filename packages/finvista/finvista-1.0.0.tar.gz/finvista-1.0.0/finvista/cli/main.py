"""
FinVista Command Line Interface.

Usage:
    finvista quote <symbols>...
    finvista history <symbol> [--start=<date>] [--end=<date>] [--format=<fmt>]
    finvista search <keyword> [--market=<market>]
    finvista health
    finvista version

Examples:
    finvista quote 000001 600519
    finvista quote AAPL MSFT --market us
    finvista history 000001 --start 2024-01-01 --format csv
    finvista search 银行
    finvista health
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

import pandas as pd


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="finvista",
        description="FinVista - Global Financial Data CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Quote command
    quote_parser = subparsers.add_parser(
        "quote",
        help="Get real-time quotes",
    )
    quote_parser.add_argument(
        "symbols",
        nargs="+",
        help="Stock symbols to query",
    )
    quote_parser.add_argument(
        "--market", "-m",
        choices=["cn", "us"],
        default="cn",
        help="Market (cn=China, us=US)",
    )

    # History command
    history_parser = subparsers.add_parser(
        "history",
        help="Get historical data",
    )
    history_parser.add_argument(
        "symbol",
        help="Stock symbol",
    )
    history_parser.add_argument(
        "--start", "-s",
        help="Start date (YYYY-MM-DD)",
    )
    history_parser.add_argument(
        "--end", "-e",
        help="End date (YYYY-MM-DD)",
    )
    history_parser.add_argument(
        "--market", "-m",
        choices=["cn", "us"],
        default="cn",
        help="Market (cn=China, us=US)",
    )
    history_parser.add_argument(
        "--format", "-f",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format",
    )
    history_parser.add_argument(
        "--output", "-o",
        help="Output file path",
    )

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for stocks",
    )
    search_parser.add_argument(
        "keyword",
        help="Search keyword",
    )
    search_parser.add_argument(
        "--market", "-m",
        choices=["cn", "us"],
        default="cn",
        help="Market to search",
    )
    search_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Maximum number of results",
    )

    # Health command
    subparsers.add_parser(
        "health",
        help="Show data source health status",
    )

    # Macro command
    macro_parser = subparsers.add_parser(
        "macro",
        help="Get macroeconomic data",
    )
    macro_parser.add_argument(
        "indicator",
        choices=["gdp", "cpi", "ppi", "pmi", "m2"],
        help="Macroeconomic indicator",
    )
    macro_parser.add_argument(
        "--format", "-f",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format",
    )

    return parser


def format_dataframe(df: pd.DataFrame, fmt: str) -> str:
    """Format a DataFrame for output."""
    if fmt == "csv":
        return str(df.to_csv(index=False))
    elif fmt == "json":
        return str(df.to_json(orient="records", indent=2))
    else:
        return str(df.to_string(index=False))


def cmd_quote(args: argparse.Namespace) -> int:
    """Handle the quote command."""
    import finvista as fv

    try:
        if args.market == "cn":
            df = fv.get_cn_stock_quote(args.symbols)
        else:
            df = fv.get_us_stock_quote(args.symbols)

        # Format for display
        display_cols = ["symbol", "name", "price", "change", "change_pct", "volume"]
        display_cols = [c for c in display_cols if c in df.columns]
        print(df[display_cols].to_string(index=False))

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_history(args: argparse.Namespace) -> int:
    """Handle the history command."""
    import finvista as fv

    try:
        if args.market == "cn":
            df = fv.get_cn_stock_daily(
                args.symbol,
                start_date=args.start,
                end_date=args.end,
            )
        else:
            df = fv.get_us_stock_daily(
                args.symbol,
                start_date=args.start,
                end_date=args.end,
            )

        output = format_dataframe(df, args.format)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Data saved to {args.output}")
        else:
            print(output)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Handle the search command."""
    import finvista as fv

    try:
        if args.market == "cn":
            df = fv.search_cn_stock(args.keyword, limit=args.limit)
        else:
            df = fv.search_us_stock(args.keyword, limit=args.limit)

        if len(df) == 0:
            print("No results found.")
        else:
            print(df.to_string(index=False))

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_health(args: argparse.Namespace) -> int:
    """Handle the health command."""
    import finvista as fv

    health = fv.get_source_health()

    print("Data Source Health Report")
    print("=" * 60)

    for data_type, sources in health.items():
        print(f"\n{data_type}:")
        if isinstance(sources, dict):
            for source_name, status in sources.items():
                if isinstance(status, dict):
                    state = status.get("status", "unknown")
                    failures = status.get("consecutive_failures", 0)
                    print(f"  {source_name}: {state} (failures: {failures})")
                else:
                    print(f"  {source_name}: {status}")
        elif isinstance(sources, list):
            for source_name in sources:
                print(f"  {source_name}: registered")

    return 0


def cmd_macro(args: argparse.Namespace) -> int:
    """Handle the macro command."""
    import finvista as fv

    try:
        indicator_map: dict[str, Callable[[], pd.DataFrame]] = {
            "gdp": fv.get_cn_macro_gdp,
            "cpi": fv.get_cn_macro_cpi,
            "ppi": fv.get_cn_macro_ppi,
            "pmi": fv.get_cn_macro_pmi,
            "m2": fv.get_cn_macro_money_supply,
        }

        func = indicator_map.get(args.indicator)
        if not func:
            print(f"Unknown indicator: {args.indicator}", file=sys.stderr)
            return 1

        df: pd.DataFrame = func()

        # Show only the last 12 records
        df = df.tail(12)

        output = format_dataframe(df, args.format)
        print(output)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Handle version flag
    if args.version:
        from finvista import __version__
        print(f"finvista {__version__}")
        return 0

    # Handle commands
    if args.command == "quote":
        return cmd_quote(args)
    elif args.command == "history":
        return cmd_history(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "health":
        return cmd_health(args)
    elif args.command == "macro":
        return cmd_macro(args)
    else:
        parser.print_help()
        return 0


def cli_entry() -> None:
    """Entry point for the CLI command."""
    sys.exit(main())


if __name__ == "__main__":
    cli_entry()
