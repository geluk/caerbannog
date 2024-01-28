from argparse import ArgumentParser
from typing import Optional

import argcomplete

from .. import target
from . import subcommands


def parse(dot_target: Optional[str]):
    parser = ArgumentParser(
        description="Configure a local system with Caerbannog.",
    )

    subparsers = parser.add_subparsers(metavar="action")

    apply = subparsers.add_parser(
        "apply",
        description="Apply a target to the system.",
        help="Apply a target to the system",
    )

    valid_targets = [t.name() for t in target.all()]
    if dot_target is None:
        apply.add_argument(
            "target", choices=valid_targets, help="Name of the target to apply"
        )
    else:
        apply.add_argument(
            "target",
            choices=valid_targets,
            metavar="TARGET",
            nargs="?",
            default=dot_target,
            help="Name of the target to apply",
        )

    apply.add_argument(
        "--elevate", action="store_true", help="Run as a privileged process"
    )
    apply.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify anything, only show what would happen",
    )
    apply.add_argument(
        "--role",
        type=str,
        metavar="ROLES",
        help="Comma-separated list of roles to which configuration should be limited",
    )
    apply.add_argument(
        "--skip-role",
        type=str,
        metavar="ROLES",
        help="Comma-separated list of roles that should be skipped",
    )
    apply.add_argument(
        "--show-context", action="store_true", help="Show all context variables"
    )

    apply_advanced = apply.add_argument_group("advanced options")
    apply_advanced.add_argument(
        "--context",
        type=str,
        metavar="JSON",
        help="Override the default context with a JSON-serialized context string",
    )

    apply.set_defaults(func=subcommands.configure)

    tgt = subparsers.add_parser(
        "target",
        description="List available targets.",
        help="List available targets",
    )
    tgt.add_argument("target", default=None, nargs="?")

    tgt.set_defaults(func=subcommands.show_target)

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

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if "func" not in args:
        parser.print_help()
        exit(1)

    args.func(args)
