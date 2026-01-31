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


class Token():
    """Matches a pattern to be found within the token."""
    @classmethod
    def identifier_for_string(cls, string: str) -> Token:
        return cls("IDENTIFIER", string)

    def __init__(self, name: str, regex: str) -> None:
        self.name = name
        self.regex = regex


class Lexeme():
    """Represents a fragment of the expression that matches a token."""
    def __init__(self, text: str, token: Token) -> None:
        self.text = text
        self.token = token

    def __eq__(self, other: Any) -> bool:
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def __str__(self) -> str:  # pragma: no cover
        return f"<Lexeme {self.token.name}: {repr(self.text)}>"


class Grammar():
    """
    A grammar specification for the config file expression language. It defines a set of production
    rules, a starting symbol and a set of tokens, which act as the terminals for the
    ruleset. Another set of terminals, the IDENTIFIER, must be specified separately by
    `parse_expression` as only that part knows what strings are identifiers and which ones are just
    strings.

    Informally specified, the language is as follows:
    - everything after the # character until the end of the line is ignored
    - an expression consists of either enumerations or identifiers separated by the + character.
    - a enumeration consists of strings, integers, etc. separated by the , character.
    - an identifier refers to a parameter.
    - a string stops at the first , or + or # character (because: see rules 1, 2 and 3),
      unless these characters appear between a pair of unescaped ' or " characters. (TODO: perhaps support ` as well)

    Examples:
    - foo=1,2,3 + foo + 4,5
    - foo="This is a string containing a , a # and a +", another string
    - postbs=postbs + echo 'Hello, World!' > /tmp/out, cat /tmp/out

    The reason why we chose to use a formal grammar is because it is not easy to correctly support
     this language by splitting on + and commas. Especially if we want to avoid splitting on them
     when they appear within two pairs of double or single quotes. This means that while iterating
     over the expression we need to keep track of whether we are within a string and thus whether
     it's okay to split when we see another + or ,.
    Also, we also want to prevent any weird behavior when the user accidentally introduces a syntax
     error, e.g. omitting a comma or plus, or adding a plus or comma at the wrong place. So
     when we do have the list of lexemes, we also need to make sure that they follow each other in the
     correct order, and if not, that we can present a clear error message to the user.
    In the end, the problem of deriving meaning from expression strings is easy if you approach the
     problem top-down: start with the grammar and then solve the underlying problems, as opposed to
     starting with the expressions and working your way up.
    """

    START = "expression"
    PRODUCTION_RULES = {
        "expression": [["item", "PLUS", "expression"], ["item"]],
        "item": [["IDENTIFIER"], ["enumeration"]],
        "enumeration": [["LITERAL", "COMMA", "enumeration"], ["LITERAL", "COMMA"], ["LITERAL"]],
    }

    # Matches the literal character '+'
    PLUS = Token("PLUS", r"\+")
    # Matches the literal character ','
    COMMA = Token("COMMA", r",")
    # Matches anything that starts with ' and continues until an unescaped ' is found.
    SINGLE_QUOTED_STRING = Token("LITERAL", r"'(?:[^\\']|\\.)*'")
    # Matches anything that starts with " and continues until an unescaped " is found.
    DOUBLE_QUOTED_STRING = Token("LITERAL", r'"(?:[^\\"]|\\.)*"')
    # Matches everything between a # and the rest of the line.
    COMMENT = Token("COMMENT", r"#[^\n]*")
    # Matches anything that starts with anything not-whitespace and continues until a comma, plus or # is found.
    #  if the comma, plus or # are found within a single or double quoted string, they are ignored.
    LITERAL = Token("LITERAL", r"\S(?:(?:\"(?:[^\"\\]"
                               r"|\\.)*\")|(?:'(?:[^'\\]"
                               r"|\\.)*')|"
                               r"(?:[^,+#]))*")

    # Order of tokens conveys a hierarchy. The tokenizer will match the token with the lower index
    # if multiple tokens match the expression.
    TOKENS = [PLUS, COMMA, COMMENT, SINGLE_QUOTED_STRING, DOUBLE_QUOTED_STRING, LITERAL]
