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

import os
import sys
from typing import TYPE_CHECKING, Any

from mako.template import Template

from clusterondemandconfig.parameter import EnumerationParameter, OptionalParameter, SimpleParameter

if TYPE_CHECKING:
    from ..command_context import CommandContext


def generate_tabcompletion_for_command_context(tool: str, command_context: CommandContext) -> None:
    with open(os.path.join(os.path.dirname(__file__), "template.sh.mako")) as f:
        print(Template(f.read()).render(
            tool=tool,
            hierarchy=_completions_hierarchy(command_context),
            cli=_cli()
        ))


def _completions_hierarchy(command_context: CommandContext) -> dict[str, Any]:
    return {
        group.name: {
            command.name: {
                "aliases": command.combined_aliases,
                "flags": [
                    flag
                    for param in (
                        param for param in command.parameters
                        if isinstance(param, OptionalParameter)
                    )
                    for flag in param.all_flags
                ],
                "parameters": {
                    flag: [str(c) for c in param.choices]
                    for param in command.parameters
                    if isinstance(param, (SimpleParameter, EnumerationParameter)) and param.choices
                    for flag in param.all_flags
                }
            }
            for command in group
        }
        for group in command_context.groups
    }


def _cli() -> str:
    script = os.path.basename(sys.argv[0])
    args = " ".join(sys.argv[1:])
    return f"{script} {args}"
