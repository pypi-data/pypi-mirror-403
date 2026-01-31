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

from .parameter import Parameter

if TYPE_CHECKING:
    from .parameter import ParamValidationsType, ParserType, SerializerType


class PositionalParameter(Parameter):
    def __init__(self, name: str, default: Any, help: str, help_section: str | None, help_varname: str | None, key: Any,
                 parser: ParserType | None, require_value: bool, secret: bool,
                 serializer: SerializerType | None, type: Any, validation: ParamValidationsType | None) -> None:
        super().__init__(
            name, default, help, help_section, help_varname, key, parser, secret, serializer,
            type, validation
        )
        self.require_value = require_value
