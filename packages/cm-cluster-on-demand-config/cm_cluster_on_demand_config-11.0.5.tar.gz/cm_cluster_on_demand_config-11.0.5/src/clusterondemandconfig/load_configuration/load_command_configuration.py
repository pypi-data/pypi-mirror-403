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

import logging
from collections.abc import Iterable
from typing import Callable

from clusterondemandconfig.command_context import Command
from clusterondemandconfig.configuration import CommandConfiguration
from clusterondemandconfig.parameter import Parameter
from clusterondemandconfig.sources import Source

from .generate_sources import SourceType, generate_sources
from .shared import assign_value, can_obtain_parameter_value_from_source, raise_or_warn_about_locked_value

log = logging.getLogger("cluster-on-demand")


def load_configuration_for_command(command: Command, system_config_files: list[str],
                                   enforcing_config_files: list[str]) -> CommandConfiguration:
    """Parse all sources to produce a valuated CommandConfiguration object.

    The sources are applied in a certain order. For each parameter, each source that has a value for
    that parameter overrides the value that was obtained from a previous source.

    The order in which the sources are applied is:
    - the enforcing config files, in the order they are obtained from the `enforcing_config_files` globs,
    - the system config files, in the order they are obtained from the `system_config_files` globs,
    - the config files declared on the command line, in the order they appear on the command line,
    - the environment variables,
    - the cli,
    - the parameter defaults, but only if no other source specified a value for that parameter.

    :param parameters: A list of Parameter instances, for which the values will be read
    :param system_config_files: A list glob patterns that specify the locations of the
                                configuration files.
    :param enforcing_config_files: A list glob patterns that specify the locations of the
                                   enforcing configuration files.
    :return CommandConfiguration
    """
    order_of_sources: list[Callable[[SourceType], list[Source]]] = [
        SourceType.static_default,
        SourceType.enforcing_config_files,
        SourceType.system_config_files,
        SourceType.cli_config_files,
        SourceType.env,
        SourceType.strict_cli,
        SourceType.dynamic_default,
    ]
    sources = generate_sources(order_of_sources, command.parameters, system_config_files, enforcing_config_files)

    configuration = CommandConfiguration(command.parameters)
    _load_configuration_from_sources(configuration, sources, command.parameters)
    return configuration


def _load_configuration_from_sources(configuration: CommandConfiguration, sources: Iterable[Source],
                                     parameters: Iterable[Parameter]) -> None:
    for source in sources:
        for parameter in parameters:
            if source.has_value_for_parameter(parameter, configuration):
                _assign_value_for_parameter_from_source(configuration, parameter, source)


def _assign_value_for_parameter_from_source(configuration: CommandConfiguration, parameter: Parameter,
                                            source: Source) -> None:
    if not can_obtain_parameter_value_from_source(parameter, source):
        log.warning("Ignoring value for parameter '%s' mentioned in source %s" % (parameter.name, source))
    elif configuration.is_value_locked_for_parameter(parameter):
        raise_or_warn_about_locked_value(configuration, parameter, source)
    else:
        assign_value(configuration, parameter, source)
