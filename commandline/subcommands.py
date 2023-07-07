from argparse import Namespace
import json
import subprocess
import sys
from typing import List

from caerbannog import context, secrets, password, plugin, target


def configure(args: Namespace):
    target.select_target(args.target)
    context.init(args)

    if args.elevate:
        serialized = context.serialize()

        command = [
            "sudo",
            "env",
            "PYTHONDONTWRITEBYTECODE=1",
            *sys.argv,
            "--context",
            serialized,
        ]
        command.remove("--elevate")

        subprocess.run(command)
    else:
        if args.show_context:
            print(json.dumps(context.context(), indent=2))
            exit(0)

        role_limit = None if args.role is None else args.role.split(",")
        target.current().execute(role_limit=role_limit)


def show_target(args: Namespace):
    def _show_target(tgt: target.TargetDescriptor, padding: List[str], last: bool):
        print("".join(padding[:-1]), end="")

        if len(padding) > 0:
            if last:
                print("└───", end="")
            else:
                print("├───", end="")

        print(tgt.name())

        dep_count = len(tgt.dependencies())
        for i, dep in enumerate(tgt.dependencies(), 1):
            will_be_last = i == dep_count
            padding.append("    " if will_be_last else "│   ")
            _show_target(dep, padding, will_be_last)
            padding.pop()

    if args.target is not None:
        tgt = target.target(args.target)
        print(f"Dependencies of {tgt.name()}:")
        print()

        _show_target(tgt, [], True)
    else:
        for tgt in target.all():
            print(tgt.name())


def encrypt(args: Namespace):
    if args.file is not None:
        with open(args.file, mode="rb") as file:
            secret = secrets.encrypt(file.read(), password.get_password())

        with open(args.file, "w", encoding="utf-8") as file:
            file.write(secret)

    elif args.text is None:
        print("Reading from standard input. Ctrl-D to finish writing.", file=sys.stderr)
        raise NotImplementedError()

    else:
        secret = secrets.encrypt(
            args.text.encode("utf-8"), password.get_password(), pretty=not args.plain
        )
        print(secret)


def decrypt(args: Namespace):
    if args.file is not None:
        with open(args.file, mode="r", encoding="utf-8") as file:
            secret = secrets.decrypt(file.read(), password.get_password())

        with open(args.file, "wb") as file:
            file.write(secret)

    elif args.text is None:
        print("Reading from standard input. Ctrl-D to finish writing.", file=sys.stderr)
        raise NotImplementedError()

    else:
        secret = secrets.decrypt(args.text, password.get_password())
        print(secret.decode("utf-8"))


def view(args: Namespace):
    with open(args.file, mode="r", encoding="utf-8") as file:
        secret = secrets.decrypt(file.read(), password.get_password()).decode("utf-8")
        print(secret)
