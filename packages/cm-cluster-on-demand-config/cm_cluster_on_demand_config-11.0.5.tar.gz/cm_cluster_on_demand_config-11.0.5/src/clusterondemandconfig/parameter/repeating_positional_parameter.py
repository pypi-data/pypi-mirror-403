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

from .parameter_creation_completion import (
    complete_help_text,
    complete_help_varname_from_name,
    complete_key,
    complete_parser_from_type,
    complete_type_from_default_value
)
from .parameter_creation_validation import (
    FN_TYPE,
    ensure_default_and_type_are_compatible,
    ensure_default_method_has_correct_signature,
    ensure_key_is_valid,
    ensure_name_is_valid,
    ensure_parser_and_serializer_are_valid,
    ensure_validations_are_valid,
    one_of,
    validate_attr_types
)
from .positional_parameter import PositionalParameter

if TYPE_CHECKING:
    from .parameter import ParamValidationsType, ParserType, SerializerType


class RepeatingPositionalParameter(PositionalParameter):
    """A parameter that can only be specified on the CLI, so does not have env or flags."""

    def __init__(self, name: str, default: Any = None, help: str = "", help_section: str | None = None,
                 help_varname: str | None = None, key: str | None = None, parser: ParserType | None = None,
                 require_value: bool = False, secret: bool = False, serializer: SerializerType = str, type: Any = None,
                 validation: ParamValidationsType | None = None) -> None:
        super().__init__(
            name, default=default, help=help, help_section=help_section, help_varname=help_varname,
            key=key, parser=parser, require_value=require_value, secret=secret, serializer=serializer, type=type,
            validation=validation
        )
        self.validate_attributes()
        self.complete_unspecified_attributes()
        self.validate_attributes()

    def validate_attributes(self) -> None:
        validate_attr_types(self, {
            "name": str,
            "default": one_of(list, FN_TYPE, None),
            "help": str,
            "help_section": one_of(str, None),
            "help_varname": one_of(str, None),
            "key": one_of(str, None),
            "parser": one_of(FN_TYPE, type, None),
            "require_value": bool,
            "serializer": one_of(FN_TYPE, type, None),
            "type": one_of([type], None),
            "validation": one_of(FN_TYPE, [FN_TYPE], None),
        })

        ensure_name_is_valid(self)
        ensure_default_and_type_are_compatible(self)
        if callable(self.default):
            ensure_default_method_has_correct_signature(self)
        ensure_key_is_valid(self)
        ensure_parser_and_serializer_are_valid(self)
        ensure_validations_are_valid(self)

    def complete_unspecified_attributes(self) -> None:
        complete_help_text(self)
        complete_key(self)
        complete_help_varname_from_name(self)

        complete_type_from_default_value(self)
        if self.type is None:
            self.type = [str]

        complete_parser_from_type(self)
