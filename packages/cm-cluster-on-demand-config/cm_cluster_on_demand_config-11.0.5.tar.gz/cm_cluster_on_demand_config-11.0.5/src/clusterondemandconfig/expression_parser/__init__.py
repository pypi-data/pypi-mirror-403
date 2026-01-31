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

from typing import TYPE_CHECKING, Any

from clusterondemandconfig.config_file_encoding import remove_any_wrapping_symbols
from clusterondemandconfig.parser_utils import parse_single_value

from .evaluator import evaluate
from .grammar import Grammar, Token
from .parser import parse
from .tokenizer import tokenize

if TYPE_CHECKING:
    from ..parameter import Parameter


def parse_expression(expression: str, parameter: Parameter, current_value: Any) -> Any:
    if "None" == expression:
        return None

    if isinstance(parameter.type, list):
        if not expression:
            return []
        return _parse_enum_expression(parameter, expression, current_value)

    if not expression:
        return None

    return parse_single_value(parameter, remove_any_wrapping_symbols(expression))


def _parse_enum_expression(parameter: Parameter, expression: str, current_value: Any) -> Any:
    tokens = [Token.identifier_for_string(parameter.key)] + Grammar.TOKENS
    mapping = {parameter.key: current_value or []}

    return evaluate(parse(tokenize(expression, tokens)), parameter, mapping)
