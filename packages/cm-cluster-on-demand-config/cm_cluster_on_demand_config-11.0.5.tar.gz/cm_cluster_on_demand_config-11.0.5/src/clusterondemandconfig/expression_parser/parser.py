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

from typing import Any

from clusterondemandconfig.exceptions import ConfigLoadError

from .grammar import Grammar, Lexeme
from .lexeme_stream import LexemeStream


def parse(stream: list[Lexeme]) -> Any:
    """Convert a sequence of lexemes into a parse tree."""
    lex_stream = LexemeStream(stream)
    result = _parse_with_rule_name(lex_stream, Grammar.START)

    if not result:
        raise ConfigLoadError("Could not parse: %s" % "".join(lex.text for lex in lex_stream))
    if lex_stream.peek():
        raise ConfigLoadError("Extra characters at the end: %s" % "".join(lex.text for lex in lex_stream))
    return result


def _parse_with_rule_name(stream: LexemeStream, rule_name: str) -> Any:
    """Iterate over a named set of rules and return as soon as one matches the token stream."""
    for rule in Grammar.PRODUCTION_RULES[rule_name]:
        index = stream.index
        result = _parse_with_rule(stream, rule)
        if result:
            return (rule_name, result)

        stream.seek(index)
    return None


def _parse_with_rule(stream: LexemeStream, rule: list[str]) -> Any:
    """Iterate over a single sequence of expected tokens or other rules. Return a tree when it matches the stream."""
    result = []

    for expected in rule:
        if not stream.peek():
            return None

        if expected.isupper():
            lexeme = next(stream)
            if expected == lexeme.token.name:
                result.append((expected, lexeme))
            else:
                return None
        elif expected.islower():
            result_ = _parse_with_rule_name(stream, expected)
            if result_:
                result.append(result_)
            else:
                return None
        else:
            assert False, "rules consist either of uppercase terminals or lowercase rule names."

    return result
