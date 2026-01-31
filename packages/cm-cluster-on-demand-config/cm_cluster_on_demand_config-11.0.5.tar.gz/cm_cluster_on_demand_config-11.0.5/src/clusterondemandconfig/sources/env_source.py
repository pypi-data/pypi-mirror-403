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
from typing import TYPE_CHECKING, Any

from clusterondemandconfig.configuration.command_configuration import CommandConfiguration
from clusterondemandconfig.exceptions import ConfigLoadError
from clusterondemandconfig.parameter import EnumerationParameter, OptionalParameter, PositionalParameter
from clusterondemandconfig.parser_utils import parse_multiple_values, parse_single_value

from .source import Source

if TYPE_CHECKING:
    from ..configuration import Configuration
    from ..parameter import Parameter


class ENVSource(Source):
    """Parameter value source for the config loader that obtains values from os.environ."""

    def __str__(self) -> str:  # pragma: no cover
        return "env"

    def is_enforcing(self) -> bool:
        return False

    def has_value_for_parameter(self, parameter: Parameter, configuration: Configuration) -> bool:
        if isinstance(parameter, PositionalParameter):
            return False

        assert isinstance(parameter, OptionalParameter)
        return any([env_var in os.environ for env_var in _env_var_names_for_parameter(parameter)])

    def get_value_for_parameter(self, parameter: Parameter, configuration: Configuration) -> Any:
        assert self.has_value_for_parameter(parameter, configuration)
        assert isinstance(parameter, OptionalParameter)

        try:
            if isinstance(parameter, EnumerationParameter):
                assert isinstance(configuration, CommandConfiguration)
                current_value = list(configuration[parameter.key] or [])
                return _value_for_enum_parameter(parameter, current_value)

            assert parameter.env
            return parse_single_value(parameter, os.environ[parameter.env])

        except Exception as e:
            raise ConfigLoadError(
                "An error occurred when parsing the value for parameter '%s' set in %s:\n\t%s\n"
                "Please note that some values need to be enclosed in quotes in order to be parsed properly" %
                (parameter.name, parameter.env, e)
            )

    def get_location_of_parameter_value(self, parameter: Parameter) -> str:
        assert isinstance(parameter, OptionalParameter)
        env_vars = [env_var for env_var in _env_var_names_for_parameter(parameter) if env_var in os.environ]

        return "env: " + ",".join(env_vars)


def _value_for_enum_parameter(parameter: OptionalParameter, current_value: list[Any] | None) -> list[Any] | None:
    prepend_var_name = env_var_name_with_prefix(parameter, "PREPEND")
    append_var_name = env_var_name_with_prefix(parameter, "APPEND")

    if parameter.env and parameter.env in os.environ:
        value = parse_multiple_values(parameter, os.environ[parameter.env])
    else:
        value = current_value

    if prepend_var_name and prepend_var_name in os.environ:
        val = parse_multiple_values(parameter, os.environ[prepend_var_name])
        value = (val or []) + (value or [])

    if append_var_name and append_var_name in os.environ:
        val = parse_multiple_values(parameter, os.environ[append_var_name])
        value = (value or []) + (val or [])

    return value


def _env_var_names_for_parameter(parameter: OptionalParameter) -> list[str]:
    if not parameter.env:
        return []
    if isinstance(parameter, EnumerationParameter):
        return [
            parameter.env,
            env_var_name_with_prefix(parameter, "PREPEND"),
            env_var_name_with_prefix(parameter, "APPEND")
        ]

    return [parameter.env]


def env_var_name_with_prefix(parameter: OptionalParameter, prefix: str) -> str:
    assert parameter.env
    if parameter.env.startswith("COD_"):
        return "_".join(["COD", prefix, parameter.env[len("COD_"):]])

    return "_".join([prefix, parameter.env])
