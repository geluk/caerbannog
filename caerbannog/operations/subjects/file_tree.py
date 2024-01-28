import os
from pathlib import Path
from typing import Iterator, List, Self, Tuple, cast

from caerbannog import context
from caerbannog.logging import *
from caerbannog.operations import *

from . import Directory, File
from .file import IsDirectory, IsFile


class FileTree(Subject):
    def __init__(self, source: str, resolve_templates=True) -> None:
        super().__init__()
        self._source = source
        self._resolved_source = context.resolve_path(source)
        self._resolve_templates = resolve_templates

    def replicates_self_to(self, *destinations: str, exclusive=False):
        for dst in destinations:
            self.add_assertion(
                IsReplicatedTo(self, dst, exclusive, children_only=False)
            )
        return self

    def replicates_children_to(self, *destinations: str, exclusive=False):
        for dst in destinations:
            self.add_assertion(IsReplicatedTo(self, dst, exclusive, children_only=True))
        return self

    def has_file_mode(self, mode: int) -> Self:
        assertion = self.get_last_assertion(IsReplicatedTo)
        if not assertion:
            return self

        for file_subject in assertion.get_subjects(File):
            if file_subject.get_assertion(IsFile):
                file_subject.has_mode(mode)

        return self

    def has_directory_mode(self, mode: int) -> Self:
        assertion = self.get_last_assertion(IsReplicatedTo)
        if not assertion:
            return self

        for dir_subject in assertion.get_subjects(Directory):
            if dir_subject.get_assertion(IsDirectory):
                dir_subject.has_mode(mode)

        return self

    def clone(self) -> Self:
        return FileTree(self._source, self._resolve_templates)

    def describe(self) -> str:
        return f"file tree {fmt.code(self._source)}"


class IsReplicatedTo(Assertion):
    def __init__(
        self,
        file_tree: FileTree,
        destination: str,
        exclusive: bool,
        children_only: bool,
    ) -> None:
        descr = (
            f"replicates children to {fmt.code(destination)}"
            if children_only
            else f"replicates self to {fmt.code(destination)}"
        )
        super().__init__(descr)
        self._file_tree = file_tree
        self._destination = destination
        self._exclusive = exclusive
        self._children_only = children_only
        self._subjects: List[Subject] = list(self._generate_subjects())

    T = TypeVar("T")

    def get_subjects(self, t: Type[T]) -> List[T]:
        return cast(List[t], list(filter(lambda a: type(a) == t, self._subjects)))

    def _generate_subjects(self) -> Iterator[Subject]:
        expected_files: List[Path] = []
        expected_dirs: List[Path] = []

        if not Path(self._file_tree._resolved_source).exists():
            raise Exception(
                f"Source path '{self._file_tree._resolved_source}' does not exist"
            )

        dst_path = Path(self._destination)
        if not dst_path.is_absolute():
            raise Exception(f"Destination path '{dst_path}' is not absolute")

        if not self._children_only:
            expected_dirs.append(dst_path)

        for dst_dir, files in self._iterate_required_files():
            expected_dirs.append(dst_dir)

            yield Directory(str(dst_dir)).is_present()

            for rel_src_file, dst_file in files:
                if rel_src_file.suffix == ".j2" and self._file_tree._resolve_templates:
                    dst_file = dst_file.with_suffix("")
                    yield File(str(dst_file)).has_template(str(rel_src_file))
                else:
                    yield File(str(dst_file)).has_content_from(str(rel_src_file))

                expected_files.append(Path(dst_file))

        if not self._exclusive:
            return

        for present_dir, present_files in self._iterate_present_files():
            # Could modify the lists here so we don't generate superfluous assertions
            if present_dir not in expected_dirs:
                yield Directory(str(present_dir)).is_absent()
                continue

            for present_file in present_files:
                if present_file not in expected_files:
                    yield File(str(present_file)).is_absent()

    def _iterate_required_files(self) -> Iterator[Tuple[Path, List[Tuple[Path, Path]]]]:
        role_dir = Path(context.current_role_dir())
        base_dir = Path(self._file_tree._resolved_source).parent
        for abs_src_dir, _, file_names in os.walk(self._file_tree._resolved_source):
            rel_base_src_dir = Path(abs_src_dir).relative_to(base_dir)
            rel_role_src_dir = Path(abs_src_dir).relative_to(role_dir)
            dst_dir = self._map_forward(rel_base_src_dir)

            rel_src_files = [
                Path(rel_role_src_dir, file_name) for file_name in file_names
            ]
            dst_files = [Path(dst_dir, file_name) for file_name in file_names]
            files = list(zip(rel_src_files, dst_files))

            yield dst_dir, files

    def _iterate_present_files(
        self,
    ) -> Iterator[Tuple[Path, List[Path]]]:
        iterator = os.walk(self._destination)

        for present_dir, _, present_filenames in iterator:
            present_files = [
                Path(present_dir, filename) for filename in present_filenames
            ]
            yield Path(present_dir), present_files

    def _map_forward(self, rel_src: Path) -> Path:
        if self._children_only:
            rel_src = _remove_base_dir(rel_src)
        return Path(self._destination, rel_src)

    def apply(self, log: LogContext):
        with log.level():
            log.detail(self._assertion_name)
            for subject in self._subjects:
                subject.apply(log)


def _remove_base_dir(path: Path) -> Path:
    return Path(*path.parts[1:])
