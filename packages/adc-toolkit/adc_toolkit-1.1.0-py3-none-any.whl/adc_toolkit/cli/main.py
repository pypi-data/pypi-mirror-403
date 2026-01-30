"""ADC Toolkit CLI entry point."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from adc_toolkit import __version__


def init_catalog_command(args: argparse.Namespace) -> int:
    """
    Execute the init-catalog command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command line arguments.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure).
    """
    try:
        from adc_toolkit.data.catalogs.kedro.scaffold import (
            create_catalog_folder_structure,
        )
    except ImportError as e:
        print(
            "error: kedro is required for this command. Install it with: uv sync --extra kedro or pip install adc-toolkit[kedro]"
        )
        print(f"Details: {e}")
        return 1

    path = Path(args.path).resolve()

    # Check if all files are excluded
    if args.no_globals and args.no_catalog and args.no_credentials:
        print("error: All files excluded. Nothing to create.")
        print("Remove at least one of --no-globals, --no-catalog, or --no-credentials.")
        return 1

    print(f"Initializing Kedro catalog structure at: {path}")

    result = create_catalog_folder_structure(
        path,
        overwrite=args.overwrite,
        include_globals=not args.no_globals,
        include_catalog=not args.no_catalog,
        include_credentials=not args.no_credentials,
    )

    if result.created_directories:
        print("\nCreated directories:")
        for d in result.created_directories:
            print(f"  - {d}")

    if result.created_files:
        print("\nCreated files:")
        for f in result.created_files:
            print(f"  - {f}")

    if result.skipped_files:
        print("\nSkipped files (already exist):")
        for f in result.skipped_files:
            print(f"  - {f}")
        if not args.overwrite:
            print("\n  Use --overwrite to replace existing files.")

    if result.success:
        print("\nCatalog structure initialized successfully!")
        print("\nNext steps:")
        print(f"  1. Edit {path / 'base' / 'globals.yml'} to configure your bucket and dataset types")
        print(f"  2. Add dataset definitions to {path / 'base' / 'catalog.yml'}")
        print(
            f"  3. Add credentials to {path / 'local' / 'credentials.yml'} (It is in .gitignore for your convenience)"
        )
    else:
        print("\nNo files were created. Use --overwrite to replace existing files.")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="adc-toolkit",
        description="ADC Toolkit - Tools for data science and ML projects.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
    )

    # init-catalog command
    init_parser = subparsers.add_parser(
        "init-catalog",
        help="Initialize Kedro catalog folder structure",
        description=(
            "Create the Kedro catalog folder structure with template configuration files. "
            "Creates catalog_config/base/globals.yml, catalog_config/base/catalog.yml, "
            "and catalog_config/local/credentials.yml."
        ),
    )
    init_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path for the configuration directory (default: current directory)",
    )
    init_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
    )
    init_parser.add_argument(
        "--no-globals",
        action="store_true",
        help="Skip creating globals.yml",
    )
    init_parser.add_argument(
        "--no-catalog",
        action="store_true",
        help="Skip creating catalog.yml",
    )
    init_parser.add_argument(
        "--no-credentials",
        action="store_true",
        help="Skip creating credentials.yml",
    )
    init_parser.set_defaults(func=init_catalog_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Parameters
    ----------
    argv : Sequence[str] | None, optional
        Command line arguments. If None, uses sys.argv.

    Returns
    -------
    int
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
