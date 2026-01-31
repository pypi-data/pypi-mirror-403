# Copyright (c) 2004-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from typing import DefaultDict, Generic, TypeVar

from ..parameter import Parameter

PT = TypeVar("PT", bound=Parameter)


@dataclass  # Should be a namedtuple, but mypy has a bug: https://github.com/python/mypy/issues/685
class ParamAndCmd(Generic[PT]):
    __slots__ = ("parameter", "command")

    parameter: PT
    command: str


def generate_namespace_tree(params_and_cmds: list[ParamAndCmd[Parameter]]) -> str:
    tree, commands = _construct_namespace_tree(params_and_cmds)

    buffer = StringIO()
    with _capture_stdout(buffer):
        _print_namespace_tree(tree, commands)
    return buffer.getvalue().strip()


def _construct_namespace_tree(
    params_and_cmds: list[ParamAndCmd[Parameter]],
) -> tuple[DefaultDict[str, set[str]], dict[str, str]]:

    tree: DefaultDict[str, set[str]] = defaultdict(set)
    commands: dict[str, str] = {}

    for param_and_cmd in params_and_cmds:
        parameter = param_and_cmd.parameter
        parent = f"{parameter.namespaces[0]}:{parameter.name}"
        tree["root"].add(parent)

        for namespace in parameter.namespaces[1:]:
            child = f"{namespace}:{parameter.name}"
            tree[parent].add(child)
            parent = child

        commands[parent] = param_and_cmd.command
    return tree, commands


def _print_namespace_tree(tree: Mapping[str, set[str]], commands: dict[str, str]) -> None:
    def __print_subtree(node: str, prefix: str, last: bool) -> None:
        if prefix and last:
            box_art = "└─"
        elif prefix:
            box_art = "├─"
        else:
            box_art = "─"

        if node in commands:
            print(f"{prefix}{box_art}[{node}]\t(command: {commands[node]})")
            return

        if node not in tree:
            print(f"{prefix}{box_art}[{node}]")
            return

        print(f"{prefix}{box_art}[{node}]")

        children = sorted(tree[node])
        for node in children[:-1]:
            __print_subtree(node, prefix=prefix + ("   " if last else "│  "), last=False)
        __print_subtree(children[-1], prefix=prefix + ("   " if last else "│  "), last=True)

    for root in sorted(tree["root"]):
        __print_subtree(root, "", True)


@contextmanager
def _capture_stdout(buffer: StringIO) -> Iterator[None]:
    sys.stdout, old_stdout = buffer, sys.stdout
    try:
        yield
    finally:
        sys.stdout = old_stdout
