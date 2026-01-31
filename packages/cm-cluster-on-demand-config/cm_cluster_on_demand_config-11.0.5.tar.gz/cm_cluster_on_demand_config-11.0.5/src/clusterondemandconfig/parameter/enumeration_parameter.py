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

from ..exceptions import ConfigConstructError
from .optional_parameter import OptionalParameter
from .parameter_creation_completion import (
    complete_env,
    complete_flags,
    complete_help_text,
    complete_help_varname_from_choices,
    complete_help_varname_from_name,
    complete_key,
    complete_list_value_type_from_choices,
    complete_parser_from_type,
    complete_type_from_default_value
)
from .parameter_creation_validation import (
    FN_TYPE,
    ensure_choices_are_compatible_with_help_choices,
    ensure_choices_are_compatible_with_type,
    ensure_choices_are_valid,
    ensure_default_and_type_are_compatible,
    ensure_default_is_a_subset_of_choices,
    ensure_default_method_has_correct_signature,
    ensure_env_is_valid,
    ensure_flags_are_valid,
    ensure_key_is_valid,
    ensure_name_is_valid,
    ensure_parser_and_serializer_are_valid,
    ensure_validations_are_valid,
    one_of,
    validate_attr_types
)

if TYPE_CHECKING:
    from .parameter import ParamValidationsType, ParserType, SerializerType


class EnumerationParameter(OptionalParameter):
    def __init__(self, name: str, advanced: bool = False, boot: bool = False, choices: list[Any] | None = None,
                 default: Any = None, env: str | None = None, flags: list[str] | None = None, help: str = "",
                 help_choices: dict[str, str] | None = None, help_section: str | None = None,
                 help_varname: str | None = None, key: str | None = None, parser: ParserType | None = None,
                 secret: bool = False, serializer: SerializerType = str, type: Any = None,
                 validation: ParamValidationsType | None = None) -> None:
        super().__init__(
            name, advanced=advanced, boot=boot, default=default, env=env, flags=flags, help=help,
            help_section=help_section, help_varname=help_varname, key=key, parser=parser,
            secret=secret, serializer=serializer, type=type, validation=validation
        )
        self.choices = choices
        self.help_choices = help_choices or {}

        self.validate_attributes()
        self.complete_unspecified_attributes()
        self.validate_attributes()

    def validate_attributes(self) -> None:
        validate_attr_types(self, {
            "name": str,
            "advanced": bool,
            "boot": bool,
            "choices": one_of(list, None),
            "default": one_of(list, FN_TYPE, None),
            "env": one_of(str, None),
            "flags": one_of([str], None),
            "help": str,
            "help_choices": one_of(dict, None),
            "help_section": one_of(str, None),
            "help_varname": one_of(str, None),
            "key": one_of(str, None),
            "parser": one_of(FN_TYPE, type, None),
            "serializer": one_of(FN_TYPE, type, None),
            "type": one_of([type], [[type]], None),
            "validation": one_of(FN_TYPE, [FN_TYPE], None)
        })

        ensure_name_is_valid(self)
        ensure_env_is_valid(self)
        ensure_flags_are_valid(self)
        ensure_key_is_valid(self)
        ensure_parser_and_serializer_are_valid(self)
        ensure_validations_are_valid(self)
        ensure_choices_are_valid(self)
        ensure_default_and_type_are_compatible(self)
        if callable(self.default):
            ensure_default_method_has_correct_signature(self)
        else:
            ensure_default_is_a_subset_of_choices(self)
        ensure_choices_are_compatible_with_type(self)
        ensure_choices_are_compatible_with_help_choices(self)

        if isinstance(self.type, list) and isinstance(self.type[0], list) and not self.parser:
            raise ConfigConstructError("parser must be specified if parameter type is complex")

    def complete_unspecified_attributes(self) -> None:
        complete_env(self)
        complete_flags(self)
        complete_help_text(self)
        complete_key(self)

        complete_help_varname_from_choices(self)
        if self.help_varname is None:
            complete_help_varname_from_name(self)

        if self.type is None:
            complete_list_value_type_from_choices(self)
        if self.type is None:
            complete_type_from_default_value(self)
        if self.type is None:
            self.type = [str]

        complete_parser_from_type(self)
