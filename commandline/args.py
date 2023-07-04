from argparse import ArgumentParser

from . import subcommands


def parse():
    parser = ArgumentParser(
        description="Configure a local system with Caerbannog.",
    )

    subparsers = parser.add_subparsers(metavar="action")

    configure = subparsers.add_parser(
        "configure", description="Configure the system.", help="Configure the system"
    )
    configure.add_argument("target", type=str)
    configure.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify anything, only show what would happen.",
    )
    configure.add_argument(
        "--elevate", action="store_true", help="Run as a privileged process."
    )
    configure.add_argument(
        "--context",
        type=str,
        metavar="JSON",
        help="Override the default context with a JSON-serialized context string.",
    )
    configure.add_argument(
        "--show-context", action="store_true", help="Show all context variables."
    )
    configure.add_argument("--role", type=str, nargs="*", help="Filter roles")
    configure.set_defaults(func=subcommands.configure)

    target = subparsers.add_parser(
        "target",
        description="List available targets.",
        help="List available targets",
    )
    target.add_argument("target", default=None, nargs="?")

    target.set_defaults(func=subcommands.show_target)

    encrypt = subparsers.add_parser(
        "encrypt", description="Encrypt a secret.", help="Encrypt a secret"
    )
    encrypt.add_argument("text", type=str, default=None, nargs="?")
    encrypt.add_argument("--file", type=str, help="Decrypt a file")
    encrypt.add_argument(
        "--plain", action="store_true", help="Do not pretty-print the secret"
    )
    encrypt.set_defaults(func=subcommands.encrypt)

    decrypt = subparsers.add_parser(
        "decrypt", description="Decrypt a secret.", help="Decrypt a secret"
    )
    decrypt.add_argument("text", type=str, default=None, nargs="?")
    decrypt.add_argument("--file", type=str)
    decrypt.set_defaults(func=subcommands.decrypt)

    view = subparsers.add_parser(
        "view", description="View a secrets file.", help="View a secret"
    )
    view.add_argument("file", type=str)
    view.set_defaults(func=subcommands.view)

    args = parser.parse_args()

    if "func" not in args:
        parser.print_help()
        exit(1)

    args.func(args)
