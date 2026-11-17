"""Command line entry point for the vulnerability scanner.

    python -m app scan  [--target /run/current-system]
    python -m app serve [--bind 127.0.0.1:8080]
    python -m app merge [--format json|ascii] < trees.txt

Mirrors the console scripts defined in pyproject.toml:
    vuln-scanner  ->  app.app:cli_main
    vuln-web      ->  app.app:main
"""

import argparse
import os
import sys

from app.app import cli_main, main
from core.merger import TreeMergerImpl
from core.formatter import TreeFormatterImpl
from core.orchestrator import TreeOrchestrator
from core.parser import TreeParserImpl


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the `python -m app` entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Scan Nix derivations for vulnerabilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="run a scan and store the results")
    scan.add_argument(
        "--target",
        default="/run/current-system",
        help="derivation target to scan (default: /run/current-system)",
    )

    serve = subparsers.add_parser("serve", help="start the web server")
    serve.add_argument(
        "--bind",
        default=os.environ.get("BIND_ADDRESS", "localhost:8080"),
        help="HOST:PORT to listen on (default: localhost:8080)",
    )

    merge = subparsers.add_parser(
        "merge", help="merge Nix dependency trees read from stdin"
    )
    merge.add_argument(
        "--format",
        choices=("json", "ascii"),
        default="json",
        help="output format (default: json)",
    )

    return parser


def merge_trees_from_stdin(fmt: str) -> str:
    """Merge the dependency trees read from stdin into one tree.

    Args:
        fmt: "json" or "ascii".

    Returns:
        Rendered merged tree.
    """
    orchestrator = TreeOrchestrator(
        parser=TreeParserImpl(),
        merger=TreeMergerImpl(),
        formatter=TreeFormatterImpl(),
    )
    result = orchestrator.process_tree_output(sys.stdin.read())
    return result["ascii"] if fmt == "ascii" else result["json"]


def cli(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the scan, serve or merge action."""
    args = build_parser().parse_args(argv)

    if args.command == "scan":
        return cli_main(["--target", args.target])

    if args.command == "serve":
        os.environ["BIND_ADDRESS"] = args.bind
        main()
        return 0

    print(merge_trees_from_stdin(args.format))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
