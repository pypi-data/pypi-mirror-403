#!/usr/bin/env python3
"""
ASVS Unified CLI - Single entry point for all ASVS compliance tools.

Usage:
    asvs <command> [options]

Commands:
    init     - Initialize a new ASVS project
    verify   - Run compliance gate validation
    scan     - Scan infrastructure (Terraform)
    test     - Run DAST verification suite
    export   - Export ASVS requirements
    drift    - Check for ASVS standard drift
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional


def cmd_init(args: argparse.Namespace) -> int:
    """Handle 'asvs init' command."""
    from tools import init_project

    cli_args = []
    if args.interactive:
        cli_args.append("--interactive")

    return init_project.main(cli_args) or 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Handle 'asvs verify' command."""
    from tools import compliance_gate

    cli_args = ["--level", str(args.level)]

    if args.docs_path:
        cli_args.extend(["--docs-path", str(args.docs_path)])

    if args.evidence:
        cli_args.extend(["--evidence-manifest", str(args.evidence)])

    if args.config:
        cli_args.extend(["--config", str(args.config)])

    if args.json:
        cli_args.extend(["--format", "json"])

    if args.strict:
        cli_args.append("--strict")

    return compliance_gate.main(cli_args)


def cmd_scan(args: argparse.Namespace) -> int:
    """Handle 'asvs scan' command."""
    from tools import iac_scanner

    cli_args = ["--plan-file", str(args.plan_file)]

    if args.json:
        cli_args.extend(["--format", "json"])

    return iac_scanner.main(cli_args)


def cmd_test(args: argparse.Namespace) -> int:
    """Handle 'asvs test' command."""
    from tools import verification_suite

    cli_args = ["--target-url", args.url]

    if args.allow_local:
        cli_args.append("--allow-local")

    if args.json:
        cli_args.extend(["--format", "json"])

    if args.timeout:
        cli_args.extend(["--timeout", str(args.timeout)])

    return verification_suite.main(cli_args)


def cmd_export(args: argparse.Namespace) -> int:
    """Handle 'asvs export' command."""
    from tools import export_requirements

    cli_args = [
        "--level", args.level,
        "--format", args.format,
    ]

    if args.output:
        cli_args.extend(["--output", str(args.output)])

    if args.source:
        cli_args.extend(["--source", str(args.source)])

    return export_requirements.main(cli_args)


def cmd_drift(args: argparse.Namespace) -> int:
    """Handle 'asvs drift' command."""
    from tools import drift_detector

    cli_args = []

    if args.local:
        cli_args.extend(["--local", str(args.local)])

    if args.offline:
        cli_args.append("--offline")

    if args.json:
        cli_args.extend(["--format", "json"])

    return drift_detector.main(cli_args)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="asvs",
        description="OWASP ASVS Compliance Engine - Unified CLI",
        epilog="Run 'asvs <command> --help' for command-specific help.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.1.0",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        metavar="<command>",
    )

    # --- asvs init ---
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new ASVS project",
        description="Bootstrap security documentation templates for your project.",
    )
    init_parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        default=True,
        help="Run in interactive mode (default: True)",
    )
    init_parser.set_defaults(func=cmd_init)

    # --- asvs verify ---
    verify_parser = subparsers.add_parser(
        "verify",
        help="Run compliance gate validation",
        description="Validate security documentation and code evidence.",
    )
    verify_parser.add_argument(
        "--docs-path", "-d",
        type=Path,
        help="Path to documentation folder (default: auto-detect ./docs or ./03-Product-Specific-Files)",
    )
    verify_parser.add_argument(
        "--level", "-l",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="ASVS assurance level (default: 2)",
    )
    verify_parser.add_argument(
        "--evidence", "-e",
        type=Path,
        help="Path to evidence.yml manifest",
    )
    verify_parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to policy configuration JSON",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    verify_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings",
    )
    verify_parser.set_defaults(func=cmd_verify)

    # --- asvs scan ---
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan infrastructure (Terraform)",
        description="Scan Terraform plan files for ASVS violations.",
    )
    scan_parser.add_argument(
        "plan_file",
        type=Path,
        help="Path to Terraform plan JSON file",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # --- asvs test ---
    test_parser = subparsers.add_parser(
        "test",
        help="Run DAST verification suite",
        description="Run security checks against a target web application.",
    )
    test_parser.add_argument(
        "url",
        help="Target URL to scan (e.g., https://example.com)",
    )
    test_parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Allow scanning localhost/private IPs (disable SSRF protection)",
    )
    test_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    test_parser.add_argument(
        "--timeout",
        type=int,
        help="Request timeout in seconds",
    )
    test_parser.set_defaults(func=cmd_test)

    # --- asvs export ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export ASVS requirements",
        description="Export ASVS requirements to CSV or Jira JSON format.",
    )
    export_parser.add_argument(
        "--level", "-l",
        choices=["1", "2", "3"],
        default="2",
        help="ASVS level to export (default: 2)",
    )
    export_parser.add_argument(
        "--format", "-f",
        choices=["csv", "jira-json"],
        default="csv",
        help="Output format (default: csv)",
    )
    export_parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file path (default: stdout)",
    )
    export_parser.add_argument(
        "--source", "-s",
        type=Path,
        help="Custom source JSON file",
    )
    export_parser.set_defaults(func=cmd_export)

    # --- asvs drift ---
    drift_parser = subparsers.add_parser(
        "drift",
        help="Check for ASVS standard drift",
        description="Compare local ASVS implementation against upstream standard.",
    )
    drift_parser.add_argument(
        "--local",
        type=Path,
        help="Path to local ASVS JSON file",
    )
    drift_parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip upstream fetch (offline mode)",
    )
    drift_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    drift_parser.set_defaults(func=cmd_drift)

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the unified CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    try:
        return parsed.func(parsed)
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
