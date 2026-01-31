"""Command line interface to run the various apps."""

import argparse


def pymagnetos_parser() -> argparse.ArgumentParser:
    """Define the arguments of the CLI."""
    parser = argparse.ArgumentParser(
        description="pymagnetos - tools for high magnetic field experiments analysis",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )
    subparsers.add_parser("pytdo", help="Run the app for TDO experiments")
    subparsers.add_parser("pyuson", help="Run the app for ultra-sound experiments")

    return parser


def main() -> None:
    """Parse arguments and run the specified app."""
    parser = pymagnetos_parser()
    args = parser.parse_args()

    match args.command:
        case "pytdo":
            from pymagnetos.pytdo import gui

            gui.run()
        case "pyuson":
            from pymagnetos.pyuson import gui

            gui.run()
        case _:
            raise NotImplementedError(f"Unkown command : {args.command}")


if __name__ == "__main__":
    main()
