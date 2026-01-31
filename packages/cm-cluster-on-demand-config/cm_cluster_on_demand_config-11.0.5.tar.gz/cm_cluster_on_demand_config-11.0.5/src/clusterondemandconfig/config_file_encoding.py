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

# String values that begin or end with whitespace characters are wrapped in one these characters to
# prevent ConfigParser from removing the whitespace characters.
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .parameter.parameter import Parameter

QUOTE_SYMBOLS = ('"', "'")


def encode(parameter: Parameter, value: Any) -> str:
    if value is None:
        return "None"

    assert parameter.serializer

    if isinstance(parameter.type, list):
        return ",".join(map(parameter.serializer, value))

    result = parameter.serializer(value)
    if parameter.type == str:
        result = _wrap_in_symbols(result)
    return result


def _wrap_in_symbols(string: str) -> str:
    if len(string) == 0:
        return '""'

    if string != string.strip():
        return '"%s"' % string.replace('"', '\\"')

    return string


def remove_any_wrapping_symbols(string: str) -> str:
    for symbol in QUOTE_SYMBOLS:
        if string.startswith(symbol) and string.endswith(symbol):
            return string.strip(symbol).replace("\\" + symbol, symbol)
    return string
