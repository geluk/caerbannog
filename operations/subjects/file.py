import os
import pathlib
import platform
import shutil
import difflib
from typing import Sequence, Union

from caerbannog import template, context
from caerbannog.operations import *


MAX_DIFF_SIZE = 250


class _PathBase(Subject):
    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def _is_file(self):
        self.add_assertion(IsFile(self._path))
        if platform.system() == "Linux" and not self.has_assertion(HasOwner):
            self.has_owner(context.username(), context.groupname())
        return self

    def _is_directory(self, create_parents: bool):
        self.add_assertion(IsDirectory(self._path, create_parents))
        if platform.system() == "Linux" and not self.has_assertion(HasOwner):
            self.has_owner(context.username(), context.groupname())
        return self

    def is_absent(self):
        self.add_assertion(IsAbsent(self._path))
        return self

    def has_owner(self, user: Union[str, None] = None, group: Union[str, None] = None):
        self.remove_assertions(HasOwner)

        self.add_assertion(HasOwner(self._path, user, group))
        return self

    def has_mode(self, mode: int):
        self.add_assertion(HasMode(self._path, mode))
        return self

    def is_system_file(self):
        self.has_owner(user="root", group="root")
        return self

    def describe(self):
        return f"path {fmt.code(self._path)}"


class File(_PathBase):
    def __init__(self, path: str):
        super().__init__(path)

    def is_present(self):
        self._is_file()
        return self

    def has_template(self, *path: str):
        content = template.render(*path)
        return self.has_content(content)

    def has_content_from(self, *content_path):
        full_path = context.resolve_path(*content_path)

        try:
            with open(full_path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(full_path, "rb") as file:
                content = file.read()

        return self.has_content(content)

    def has_content(self, content: Union[str, bytes]):
        self._is_file()
        if type(content) is str:
            self.add_assertion(HasContent(self._path, content))
        elif type(content) is bytes:
            self.add_assertion(HasBinaryContent(self._path, content))
        return self

    def clone(self) -> Self:
        return File(self._path)


class Directory(_PathBase):
    def __init__(self, path: str) -> None:
        super().__init__(path)

    def is_present(self, parents=True):
        """
        Assert that this directory is present. If `parents` is `Tre`, also
        recursively create all nonexistent parent directories.
        """
        self._is_directory(create_parents=parents)
        return self

    def clone(self) -> Self:
        return Directory(self._path)


class IsDirectory(Assertion):
    def __init__(self, path: str, create_parents: bool):
        super().__init__("is directory")
        self._path = path
        self._create_parents = create_parents

    def apply(self, log: LogContext):
        if os.path.isdir(self._path):
            self._display_passed(log)
            return
        if os.path.exists(self._path):
            if context.should_modify():
                os.remove(self._path)
            self.register_change(FileRemoved())

        # TODO: Parents should be created with appropriate mode and ownership.
        parent_absent = not pathlib.Path(self._path).parent.exists()
        if context.should_modify():
            pathlib.Path(self._path).mkdir(parents=self._create_parents)
        # It probably makes more sense to emit one change per directory here.
        self.register_change(DirectoryCreated(parent_absent and self._create_parents))

        self._display(log)


class IsFile(Assertion):
    def __init__(self, path: str):
        super().__init__("is file")
        self._path = path

    def apply(self, log: LogContext):
        if os.path.isfile(self._path):
            self._display_passed(log)
            return
        if os.path.exists(self._path):
            if context.should_modify():
                shutil.rmtree(self._path)
            self.register_change(DirectoryRemoved())

        if context.should_modify():
            with open(self._path, "w"):
                pass
            self.register_change(FileCreated())

        self._display_changed(log)


class IsAbsent(Assertion):
    def __init__(self, path: str):
        super().__init__("is absent")
        self._path = path

    def apply(self, log: LogContext):
        if os.path.isdir(self._path):
            if context.should_modify():
                shutil.rmtree(self._path)
            self.register_change(DirectoryRemoved())

        elif os.path.exists(self._path):
            if context.should_modify():
                os.remove(self._path)
            self.register_change(FileRemoved())

        self._display(log)


class HasOwner(Assertion):
    def __init__(
        self, path: str, user: Union[str, None], group: Union[str, None]
    ) -> None:
        user_descr = f"user={user}" if user else ""
        group_descr = f"group={group}" if group else ""

        ownership = " ".join([user_descr, group_descr])

        super().__init__(f"has owner: {ownership}")

        self._path = path
        self._user = user
        self._group = group

    def apply(self, log: LogContext):
        path = pathlib.Path(self._path)
        try:
            old_user = path.owner()
            old_group = path.group()
        except FileNotFoundError:
            if not context.should_modify():
                self._display_failed(log)
                return
            raise

        user: Any = None
        if self._user is not None and old_user != self._user:
            user = self._user

        group: Any = None
        if self._group is not None and old_group != self._group:
            group = self._group

        if user is None and group is None:
            # Nothing to do
            self._display_passed(log)
            return

        if context.should_modify():
            shutil.chown(self._path, user=user, group=group)

        if user is not None:
            self.register_change(UserChanged(old_user, user))
        if group is not None:
            self.register_change(GroupChanged(old_group, group))

        self._display(log)


class HasMode(Assertion):
    def __init__(self, path: str, mode: int) -> None:
        super().__init__(f"has mode: {mode:03o}")
        self._path = path
        self._mode = mode

    def apply(self, log: LogContext):
        try:
            stat = os.stat(self._path, follow_symlinks=False)
        except FileNotFoundError:
            if not context.should_modify():
                self._display_failed(log)
                return
            raise

        current_mode = stat.st_mode & 0o777

        if current_mode != self._mode:
            if context.should_modify():
                os.chmod(self._path, self._mode)
            self.register_change(ModeChanged(current_mode, self._mode))

        self._display(log)


class HasContent(Assertion):
    def __init__(self, path: str, content: str) -> None:
        super().__init__("has content")
        self._path = path
        self._content = content

    def apply(self, log: LogContext):
        is_different = False
        existing_content = ""
        try:
            with open(self._path, "r", encoding="utf-8") as file:
                existing_content = file.read()
            is_different = existing_content != self._content
        except FileNotFoundError:
            is_different = True

        if is_different:
            if context.should_modify():
                with open(self._path, "w", encoding="utf-8") as file:
                    file.write(self._content)

            self.register_change(ContentChanged(existing_content, self._content))

        self._display(log)


class HasBinaryContent(Assertion):
    def __init__(self, path: str, content: bytes) -> None:
        super().__init__("has content")
        self._path = path
        self._content = content

    def apply(self, log: LogContext):
        is_different = False
        existing_content = bytes()
        try:
            with open(self._path, "rb") as file:
                existing_content = file.read()
            is_different = existing_content != self._content
        except FileNotFoundError:
            is_different = True

        if is_different:
            if context.should_modify():
                with open(self._path, "wb") as file:
                    file.write(self._content)

            self.register_change(
                ContentChangedSummary(len(self._content) - len(existing_content))
            )

        self._display(log)


class UserChanged(Change):
    def __init__(self, old: str, new: str) -> None:
        super().__init__("user changed", [DiffLine.remove(old), DiffLine.add(new)])


class GroupChanged(Change):
    def __init__(self, old: str, new: str) -> None:
        super().__init__("group changed", [DiffLine.remove(old), DiffLine.add(new)])


class ModeChanged(Change):
    def __init__(self, old: int, new: int) -> None:
        super().__init__(
            f"mode changed", [DiffLine.remove(f"{old:03o}"), DiffLine.add(f"{new:03o}")]
        )


class FileCreated(Change):
    def __init__(self):
        super().__init__("file created")


class DirectoryCreated(Change):
    def __init__(self, with_parent: bool):
        super().__init__(
            "directory created" + (" with parent(s)" if with_parent else "")
        )


class DirectoryRemoved(Change):
    def __init__(self):
        super().__init__("directory removed")


class FileRemoved(Change):
    def __init__(self):
        super().__init__("file removed")


class ContentChangedSummary(Change):
    def __init__(self, bytes: int) -> None:
        if bytes > 0:
            details = f"+{str(bytes)}"
        else:
            details = f"{str(bytes)}"

        super().__init__("content changed", [details])


class ContentChanged(Change):
    def __init__(self, frm: str, to: str) -> None:
        diff = list(
            difflib.unified_diff(
                frm.splitlines(keepends=True), to.splitlines(keepends=True)
            )
        )

        headers = ["---", "+++"]

        def format_diff(unformatted: List[str]):
            formatted = []
            for line in unformatted:
                stripped = line.strip()
                if stripped in headers:
                    continue

                trimmed = line.rstrip("\r\n")
                if line == trimmed:
                    trimmed = f"{trimmed}^m"

                if line.startswith("-"):
                    formatted.append(DiffLine.remove(trimmed[1:]))
                elif line.startswith("+"):
                    formatted.append(DiffLine.add(trimmed[1:]))
                else:
                    formatted.append(DiffLine.neutral(trimmed))
            return formatted

        def count_by_type(difftype: str):
            return sum(
                1
                for _ in filter(
                    lambda l: l.strip() not in headers and l.startswith(difftype), diff
                )
            )

        lines: Sequence[Tuple[DiffType, str]] = []
        if len(diff) > MAX_DIFF_SIZE:
            added = count_by_type("+")
            removed = count_by_type("-")

            lines = [
                DiffLine.neutral("Diff too long to be shown. Summary:"),
                DiffLine.add(f"{added} lines"),
                DiffLine.remove(f"{removed} lines"),
                DiffLine.neutral("Sample:"),
                *format_diff(diff[:10]),
                DiffLine.detail("8< -------------------------------"),
                *format_diff(diff[-10:]),
            ]
        else:
            lines = format_diff(diff)

        if len(lines) == 0:
            lines.append((DiffType.NEUTRAL, "<only whitespace changes>"))

        super().__init__("content changed", details=lines)
