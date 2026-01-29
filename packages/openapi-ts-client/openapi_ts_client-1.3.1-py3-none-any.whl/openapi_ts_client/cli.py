"""Command-line interface for openapi-ts-client."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Configure library logging BEFORE importing generator
# This must happen at module load time, before __init__.py imports generator
if "-q" in sys.argv or "--quiet" in sys.argv:
    os.environ["OPENAPI_TS_CLIENT_LOG_LEVEL"] = "CRITICAL"
elif "-v" not in sys.argv and "--verbose" not in sys.argv:
    os.environ["OPENAPI_TS_CLIENT_LOG_LEVEL"] = "WARNING"

from . import ClientFormat, generate_typescript_client  # noqa: E402
from .exceptions import OutputDirectoryNotEmptyError  # noqa: E402

# Read version from pyproject.toml - this is the canonical version
__version__ = "1.1.2"


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="openapi-ts-client",
        description="Generate TypeScript clients from OpenAPI specifications.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"openapi-ts-client {__version__}",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="OpenAPI spec file path, URL, or '-' for stdin",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["fetch", "axios", "angular"],
        default="fetch",
        help="Output format (default: fetch)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./generated",
        help="Output directory (default: ./generated)",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Config file path (default: openapi-ts-client.json)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip OpenAPI spec validation",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear output directory before generating",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Continue even if output directory is not empty (may overwrite files)",
    )
    return parser


def load_spec_from_file(file_path: str) -> dict:
    """Load OpenAPI spec from a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return json.loads(path.read_text())


def is_url(input_str: str) -> bool:
    """Check if input is a URL."""
    return input_str.startswith("http://") or input_str.startswith("https://")


def load_spec_from_url(url: str) -> dict:
    """Load OpenAPI spec from a URL."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ConnectionError(f"Failed to fetch URL: {url}\n  HTTP {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to fetch URL: {url}\n  {e.reason}") from e


def load_spec_from_stdin() -> dict:
    """Load OpenAPI spec from stdin."""
    content = sys.stdin.read()
    if not content.strip():
        raise ValueError("No input received from stdin")
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from stdin: {e}") from e


def get_client_format(format_str: str) -> ClientFormat:
    """Convert format string to ClientFormat enum."""
    return {
        "fetch": ClientFormat.FETCH,
        "axios": ClientFormat.AXIOS,
        "angular": ClientFormat.ANGULAR,
    }[format_str]


DEFAULT_CONFIG_NAME = "openapi-ts-client.json"


class Output:
    """Handle CLI output based on verbosity settings."""

    def __init__(self, quiet: bool = False, verbose: bool = False):
        self.quiet = quiet
        self.verbose = verbose

    def info(self, message: str) -> None:
        """Print info message (unless quiet)."""
        if not self.quiet:
            print(message)

    def detail(self, message: str) -> None:
        """Print detail message (only in verbose mode)."""
        if self.verbose and not self.quiet:
            print(f"  {message}")

    def success(self, message: str) -> None:
        """Print success message (unless quiet)."""
        if not self.quiet:
            print(message)

    def error(self, message: str) -> None:
        """Print error message (always shown)."""
        print(f"Error: {message}", file=sys.stderr)


def prompt_directory_action(path: Path, file_count: int) -> str:
    """Prompt user for action on non-empty directory.

    Args:
        path: The output directory path.
        file_count: Number of non-hidden files in the directory.

    Returns:
        'clean' to clear directory, 'force' to continue, or 'cancel' to abort.
    """
    print(f"\nOutput directory '{path}' is not empty (contains {file_count} files).")
    print("\nHow would you like to proceed?")
    print("  [1] Clear directory and continue")
    print("  [2] Continue without clearing (may overwrite files)")
    print("  [3] Cancel")

    while True:
        choice = input("\nChoice [1/2/3]: ").strip()
        if choice == "1":
            return "clean"
        elif choice == "2":
            return "force"
        elif choice == "3":
            return "cancel"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def load_config(config_path: str | None) -> dict | None:
    """Load config file if it exists."""
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
    else:
        path = Path(DEFAULT_CONFIG_NAME)
        if not path.exists():
            return None

    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid config file: {path}\n  {e}") from e


def normalize_config(config: dict) -> list[dict]:
    """Normalize config to list of client configs."""
    if "clients" in config:
        return config["clients"]
    # Single client shorthand
    return [config]


def validate_client_config(client: dict, index: int) -> None:
    """Validate a single client config."""
    if "input" not in client:
        raise ValueError(f"Config client #{index + 1} missing required 'input' field")


def generate_from_config(config: dict, args, out: Output) -> int:
    """Generate clients from config file."""
    clients = normalize_config(config)

    if len(clients) > 1:
        out.info(f"Generating {len(clients)} clients...")

    for i, client in enumerate(clients):
        validate_client_config(client, i)

        input_path = client["input"]
        format_str = client.get("format", "fetch")
        output_path = client.get("output", "./generated")

        if len(clients) > 1:
            out.info(f"\n[{i + 1}/{len(clients)}] {format_str} -> {output_path}")
        else:
            out.info(f"Generating {format_str} client...")

        # Load spec
        if is_url(input_path):
            out.detail(f"Fetching spec from {input_path}")
            spec = load_spec_from_url(input_path)
        else:
            out.detail(f"Reading spec from {input_path}")
            spec = load_spec_from_file(input_path)

        # Generate
        client_format = get_client_format(format_str)
        try:
            generate_typescript_client(
                spec,
                client_format,
                output_path,
                skip_validation=args.no_validate,
                clean=getattr(args, "clean", False),
                force=getattr(args, "force", False),
            )
        except OutputDirectoryNotEmptyError as e:
            if sys.stdin.isatty() and not args.quiet:
                action = prompt_directory_action(e.path, e.file_count)
                if action == "cancel":
                    out.info("Cancelled.")
                    return 1
                elif action == "clean":
                    generate_typescript_client(
                        spec,
                        client_format,
                        output_path,
                        skip_validation=args.no_validate,
                        clean=True,
                    )
                else:  # force
                    generate_typescript_client(
                        spec,
                        client_format,
                        output_path,
                        skip_validation=args.no_validate,
                        force=True,
                    )
            else:
                out.error(str(e))
                out.error(
                    "  Use --clean to clear the directory first, or --force to continue anyway."
                )
                return 1

        out.success(f"Generated to {output_path}")

    if len(clients) > 1:
        out.info("\nDone.")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)
    out = Output(quiet=args.quiet, verbose=args.verbose)

    try:
        # If explicit input given, use it (ignore config)
        if args.input:
            out.info(f"Generating {args.format} client...")

            # Load spec based on input type
            if args.input == "-":
                out.detail("Reading spec from stdin")
                spec = load_spec_from_stdin()
            elif is_url(args.input):
                out.detail(f"Fetching spec from {args.input}")
                spec = load_spec_from_url(args.input)
            else:
                out.detail(f"Reading spec from {args.input}")
                spec = load_spec_from_file(args.input)

            # Log spec details in verbose mode
            if args.verbose:
                info = spec.get("info", {})
                out.detail(f"API: {info.get('title', 'Unknown')} v{info.get('version', '?')}")
                schemas = spec.get("components", {}).get("schemas", {})
                out.detail(f"Models: {len(schemas)}")

            # Generate client
            client_format = get_client_format(args.format)
            try:
                generate_typescript_client(
                    spec,
                    client_format,
                    args.output,
                    skip_validation=args.no_validate,
                    clean=args.clean,
                    force=args.force,
                )
            except OutputDirectoryNotEmptyError as e:
                if sys.stdin.isatty() and not args.quiet:
                    action = prompt_directory_action(e.path, e.file_count)
                    if action == "cancel":
                        out.info("Cancelled.")
                        return 1
                    elif action == "clean":
                        generate_typescript_client(
                            spec,
                            client_format,
                            args.output,
                            skip_validation=args.no_validate,
                            clean=True,
                        )
                    else:  # force
                        generate_typescript_client(
                            spec,
                            client_format,
                            args.output,
                            skip_validation=args.no_validate,
                            force=True,
                        )
                else:
                    out.error(str(e))
                    out.error(
                        "  Use --clean to clear the directory first, or --force to continue anyway."
                    )
                    return 1

            out.success(f"Generated to {args.output}")

            return 0

        # No input - try config file
        config = load_config(args.config)
        if config is None:
            out.error("No input provided and no config file found")
            print("  Usage: openapi-ts-client <input> [options]", file=sys.stderr)
            return 2

        return generate_from_config(config, args, out)

    except (FileNotFoundError, ConnectionError) as e:
        out.error(str(e))
        return 1
    except ValueError as e:
        out.error(str(e))
        return 2
    except Exception as e:
        out.error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
