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

import re
from collections.abc import Collection
from typing import TYPE_CHECKING, Any

from .exceptions import ConfigLoadError

if TYPE_CHECKING:
    from .parameter import Parameter


def parser_for_type(type: Any) -> Any:
    return boolean_parser if type is bool else type


def boolean_parser(string: str) -> bool:
    """Parse string to boolean value."""
    YES = ["y", "on", "yes", "true", "1"]
    NO = ["n", "no", "off", "false", "0"]
    if string.lower() in YES:
        return True

    if string.lower() in NO:
        return False

    raise ConfigLoadError("Expected %s for yes or %s for no. Got '%s'." % (",".join(YES), ",".join(NO), string))


def parse_single_value(parameter: Parameter, value: str) -> Any:
    if value.strip() == "None":
        return None

    assert parameter.parser
    parsed_value = parameter.parser(value)

    choices = getattr(parameter, "choices", None)
    if choices:
        _raise_if_not_in_choices(parsed_value, choices)

    return parsed_value


def parse_multiple_values(parameter: Parameter, value: Any) -> list[Any] | None:
    if not value:
        return []

    if value.strip() == "None":
        return None

    assert parameter.parser
    parsed_values = [parameter.parser(v.strip()) for v in re.split(",\n?", value)]

    choices = getattr(parameter, "choices", None)
    if choices:
        for parsed_value in parsed_values:
            _raise_if_not_in_choices(parsed_value, choices)

    return parsed_values


def _raise_if_not_in_choices(value: Any, choices: Collection[Any]) -> None:
    if value not in choices:
        raise ConfigLoadError("%s is not a valid value. Valid values are {%s}" %
                              (value, ",".join(map(str, choices))))
