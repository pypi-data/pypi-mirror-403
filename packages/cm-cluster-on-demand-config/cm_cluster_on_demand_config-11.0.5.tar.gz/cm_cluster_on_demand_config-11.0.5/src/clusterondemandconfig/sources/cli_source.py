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

from typing import TYPE_CHECKING, Any, Optional

from clusterondemandconfig.argparse_factory import argparse_parser_for_parameters
from clusterondemandconfig.configuration import CommandConfiguration
from clusterondemandconfig.exceptions import UnknownCLIArgumentError
from clusterondemandconfig.parameter import EnumerationParameter

from .source import Source

if TYPE_CHECKING:
    from ..configuration import Configuration
    from ..parameter import Parameter


class CLISource(Source):
    """Parameter value source for the config loader that obtains values from sys.argv."""

    def __init__(self, parameters: list[Parameter], strict: bool) -> None:
        parser = argparse_parser_for_parameters(parameters)
        self.parsed, unknown = parser.parse_known_args()
        if strict and unknown:
            raise UnknownCLIArgumentError(unknown)

    def is_enforcing(self) -> bool:
        return False

    def __str__(self) -> str:  # pragma: no cover
        return "cli"

    def has_value_for_parameter(self, parameter: Parameter, configuration: Configuration) -> bool:
        if self._has_value(parameter.name):
            return True

        if isinstance(parameter, EnumerationParameter):
            return self._has_value("prepend-" + parameter.name) or self._has_value("append-" + parameter.name)

        return False

    def get_value_for_parameter(self, parameter: Parameter, configuration: Configuration) -> Any:
        assert self.has_value_for_parameter(parameter, configuration)

        if isinstance(parameter, EnumerationParameter):
            assert isinstance(configuration, CommandConfiguration)
            current_value = configuration[parameter.key] if parameter.key in configuration else None
            return self._value_for_enum_parameter(parameter, current_value)

        return self._get_value(parameter.name)

    def _value_for_enum_parameter(self, parameter: EnumerationParameter, previous_value: Optional[Any]) -> list[str]:
        if self._has_value(parameter.name):
            center = self._get_enum_value(parameter.name)
        else:
            center = previous_value or []
        prepend = self._get_enum_value("prepend-" + parameter.name)
        append = self._get_enum_value("append-" + parameter.name)
        return prepend + center + append

    def _has_value(self, name: str) -> bool:
        return hasattr(self.parsed, name)

    def _get_enum_value(self, name: str) -> list[Any]:
        return [item for group in self._get_value(name, []) for item in group]

    def _get_value(self, name: str, *args: Any) -> Any:
        return getattr(self.parsed, name, *args)
