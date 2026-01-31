import argparse
import os

from . import __version__, compare, rollout, sync

__all__ = [
    "main",
]


def get_version() -> str:
    pkg_dir = os.path.join(os.path.dirname(__file__))
    pkg_dir = os.path.abspath(pkg_dir)

    return f"%(prog)s {__version__} from {pkg_dir}"


def create_parser():
    """
    Main function for the Vault Toolkit CLI.

    This function sets up the main parser and subparsers for each command
    (compare, rollout, sync) and executes the corresponding script's main function.
    """
    parser = argparse.ArgumentParser(
        description="A collection of CLI tools for managing HashiCorp Vault."
    )
    parser.add_argument("-V", "--version", action="version", version=get_version())

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # --- Compare Command ---
    compare_parser = subparsers.add_parser(
        "compare", help="Compare secrets between two Vault clusters."
    )
    compare.create_parser(compare_parser)

    # --- Rollout Command ---
    rollout_parser = subparsers.add_parser(
        "rollout", help="Perform a rolling restart of a Vault cluster."
    )
    rollout.create_parser(rollout_parser)

    # --- Sync Command ---
    sync_parser = subparsers.add_parser(
        "sync", help="Take a snapshot from one Vault and restore to another."
    )
    sync.create_parser(sync_parser)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # Call the appropriate main function based on the command
    if args.command == "compare":
        compare.main(args)
    elif args.command == "rollout":
        rollout.main(args)
    elif args.command == "sync":
        sync.main(args)


if __name__ == "__main__":  # pragma: no cover
    main()
