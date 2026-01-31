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
from typing import TYPE_CHECKING, Any

from .argparse_factory import argparse_parser_for_command_context

if TYPE_CHECKING:
    from .command_context import Command, CommandContext


def determine_invoked_command(command_context: CommandContext) -> tuple[Command | None, list[str]]:
    """Uses sys.argv to determine which command in command_context is invoked by the user.

    When determining the command, we use the name or alias of the group and the name or alias of the
    command to search through the commands declared within command_context, e.g.
    `cm-cod-os cluster create` means that the command_context needs to contain a group named
    'cluster' that contains a command named 'create'. If no matching command has been found,
    argparse prints a usage message and raises a SystemExit exception.
    N.B. The exception can be changed later.

    As an important side-effect, the user is informed of which commands he can invoke and is shown a
    usage message when he tries to invoke an unknown command.

    :param command_context A CommandContext instance that contains command groups and commands.
    :return a (Command, str) tuple containing the found Command, and the contents of sys.argv
      without the names or aliases of the found group and command. This cleaned sys.argv can be
      used to unambiguously parse the remaining CLI arguments without requiring knowledge of the
      invoked group or command.
    """
    sys_argv = list(sys.argv)
    command, user_invoked_args = _determine_invoked_command(command_context, sys_argv)

    for user_invoked_arg in user_invoked_args:
        sys_argv.remove(user_invoked_arg)

    return command, sys_argv


def _determine_invoked_command(
    command_context: CommandContext, sys_argv: list[str],
) -> tuple[Command | None, list[Any]]:

    parser = argparse_parser_for_command_context(command_context)
    config, _ = parser.parse_known_args(sys_argv[1:])

    if hasattr(config, "command"):
        command = command_context.command_for_group_and_command_name(config.group, config.command)
        user_invoked_args = [config.group, config.command]
    else:
        command = command_context.command_for_combined_alias(config.group)
        user_invoked_args = [config.group]

    return command, user_invoked_args
