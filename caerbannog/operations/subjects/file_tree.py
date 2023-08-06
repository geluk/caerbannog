import os
import pathlib
from typing import Iterator, List, Self, Tuple

from caerbannog.logging import *
from caerbannog import context

from . import File, Directory
from caerbannog.operations import *


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

    def _generate_subjects(self) -> Iterator[Subject]:
        expected_files: List[pathlib.Path] = []
        expected_dirs: List[pathlib.Path] = []

        if not self._children_only:
            expected_dirs.append(pathlib.Path(self._destination))

        for dst_dir, files in self._iterate_required_files():
            expected_dirs.append(pathlib.Path(dst_dir))

            yield Directory(dst_dir).is_present()

            for rel_src_file, dst_file in files:
                if rel_src_file.endswith(".j2") and self._file_tree._resolve_templates:
                    dst_file = dst_file.removesuffix(".j2")
                    yield File(dst_file).has_template(str(rel_src_file))
                else:
                    yield File(dst_file).has_content_from(str(rel_src_file))

                expected_files.append(pathlib.Path(dst_file))

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

    def _iterate_required_files(self) -> Iterator[Tuple[str, List[Tuple[str, str]]]]:
        role_dir = context.current_role_dir()
        for abs_src_dir, _, file_names in os.walk(self._file_tree._resolved_source):
            rel_src_dir = str(pathlib.Path(abs_src_dir).relative_to(role_dir))
            dst_dir = self._map_forward(rel_src_dir)

            rel_src_files = [
                str(pathlib.Path(rel_src_dir, file_name)) for file_name in file_names
            ]
            dst_files = [
                self._map_forward(rel_src_file) for rel_src_file in rel_src_files
            ]
            files = list(zip(rel_src_files, dst_files))

            yield dst_dir, files

    def _iterate_present_files(
        self,
    ) -> Iterator[Tuple[pathlib.Path, List[pathlib.Path]]]:
        iterator = os.walk(self._destination)

        for present_dir, _, present_filenames in iterator:
            present_files = [
                pathlib.Path(present_dir, filename) for filename in present_filenames
            ]
            yield pathlib.Path(present_dir), present_files

    def _map_forward(self, rel_src: str) -> str:
        if self._children_only:
            rel_src = _remove_base_dir(rel_src)
        return str(pathlib.Path(self._destination, rel_src))

    def apply(self, log: LogContext):
        with log.level():
            log.detail(self._assertion_name)
            for subject in self._subjects:
                subject.apply(log)


def _remove_base_dir(path: str):
    return str(pathlib.Path(*pathlib.Path(path).parts[1:]))