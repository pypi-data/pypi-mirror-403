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

from collections.abc import Iterable
from typing import Callable

from clusterondemandconfig.command_context import Command
from clusterondemandconfig.configuration import CommandConfiguration
from clusterondemandconfig.parameter import Parameter
from clusterondemandconfig.sources import Source

from .generate_sources import SourceType, generate_sources


def load_boot_configuration_for_command(command: Command) -> CommandConfiguration:
    parameters = [parameter for parameter in command.parameters if getattr(parameter, "boot", False)]

    order_of_sources: list[Callable[[SourceType], list[Source]]] = [
        SourceType.static_default,
        SourceType.env,
        SourceType.loose_cli,
        SourceType.dynamic_default
    ]
    sources = generate_sources(order_of_sources, parameters, [], [])

    configuration = CommandConfiguration(parameters)
    _load_configuration_from_sources(configuration, sources, parameters)
    return configuration


def _load_configuration_from_sources(configuration: CommandConfiguration, sources: Iterable[Source],
                                     parameters: Iterable[Parameter]) -> None:
    for source in sources:
        for parameter in parameters:
            if source.has_value_for_parameter(parameter, configuration):
                value = source.get_value_for_parameter(parameter, configuration)

                configuration.set_value(parameter, value, source)
