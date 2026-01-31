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

from clusterondemandconfig.exceptions import ConfigLoadError

from .grammar import Lexeme, Token


def tokenize(string: str, tokens: list[Token]) -> list[Lexeme]:
    """Break the string up into lexemes using the specified tokens.

    Matching of the tokens is done in the order they appear.
    There is no backtracking if a string could not be tokenized completely, an error is raised instead.
    """
    string = string.strip()
    regex = re.compile("(" + ")|(".join(token.regex for token in tokens) + ")")

    lexemes = []
    while string:
        match = re.match(regex, string)
        if not match:
            raise ConfigLoadError("Could not parse: %s" % (string))

        text = match.group()
        token = tokens[match.groups().index(text)]
        string = string[len(text):].strip()
        if "COMMENT" != token.name:
            lexemes.append(Lexeme(text.strip(), token))

    return lexemes
