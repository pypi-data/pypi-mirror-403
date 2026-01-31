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

from typing import TYPE_CHECKING

from ..parser_utils import boolean_parser
from .optional_parameter import OptionalParameter
from .parameter_creation_completion import complete_env, complete_flags, complete_help_text, complete_key
from .parameter_creation_validation import (
    FN_TYPE,
    ensure_default_method_has_correct_signature,
    ensure_env_is_valid,
    ensure_flags_are_valid,
    ensure_key_is_valid,
    ensure_name_is_valid,
    ensure_validations_are_valid,
    one_of,
    validate_attr_types
)

if TYPE_CHECKING:
    from .parameter import ParamValidationsType


class SwitchParameter(OptionalParameter):
    def __init__(self, name: str, advanced: bool = False, boot: bool = False, default: bool = False,
                 env: str | None = None, flags: list[str] | None = None, help: str = "",
                 help_section: str | None = None, key: str | None = None,
                 validation: ParamValidationsType | None = None) -> None:
        super().__init__(
            name, advanced=advanced, boot=boot, default=default, env=env, flags=flags, help=help,
            help_section=help_section, help_varname=None, key=key, parser=boolean_parser, secret=False, serializer=str,
            type=bool, validation=validation
        )
        self.validate_attributes()
        self.complete_unspecified_attributes()
        self.validate_attributes()

    def validate_attributes(self) -> None:
        validate_attr_types(self, {
            "advanced": bool,
            "boot": bool,
            "name": str,
            "default": one_of(bool, FN_TYPE),
            "env": one_of(str, None),
            "flags": one_of([str], None),
            "help": str,
            "help_section": one_of(str, None),
            "help_varname": one_of(str, None),
            "key": one_of(str, None),
            "validation": one_of(FN_TYPE, [FN_TYPE], None),
        })

        ensure_name_is_valid(self)
        if callable(self.default):
            ensure_default_method_has_correct_signature(self)
        ensure_env_is_valid(self)
        ensure_flags_are_valid(self)
        ensure_key_is_valid(self)
        ensure_validations_are_valid(self)

    def complete_unspecified_attributes(self) -> None:
        complete_env(self)
        complete_flags(self)
        complete_help_text(self)
        complete_key(self)
