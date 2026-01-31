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

from typing import TYPE_CHECKING, Any, Callable, Union

if TYPE_CHECKING:
    from ..config_namespace import ConfigNamespace
    from ..configuration import ConfigurationView

    ParserType = Callable[[str], Any]
    SerializerType = Callable[[Any], str]
    ParamValidationType = Callable[["Parameter", ConfigurationView], None]
    ParamValidationsType = Union[ParamValidationType, list[ParamValidationType]]


class Parameter:
    """A struct class that acts as an abstract supertype for all configuration parameters."""

    def __init__(self, name: str, default: Any, help: str, help_section: str | None, help_varname: str | None, key: str,
                 parser: ParserType | None, secret: bool, serializer: SerializerType | None, type: Any,
                 validation: ParamValidationsType | None) -> None:
        self.name = name
        self.default = default
        self.help = help
        self.help_section = help_section
        self.help_varname = help_varname
        self.key = key
        self.parser = parser
        self.secret = secret
        self.serializer = serializer
        self.type = type
        self.validation = validation
        # TODO: fix following two parameters, should they be merged or should names be different?
        self.namespace: ConfigNamespace | None = None  # noqa: F821
        self.namespaces: list[str] = []
        self.parent: Parameter | None = None

    def __hash__(self) -> int:  # pragma: no cover
        return hash(str(self))

    def __repr__(self) -> str:  # pragma: no cover
        return "<%s: %s>" % (self.__class__.__name__, self.__dict__)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other: Any) -> bool:  # pragma: no cover
        return not self == other

    def __copy__(self) -> Parameter:
        copy = type(self).__new__(self.__class__)
        copy.__dict__.update(self.__dict__)
        copy.parent = self
        return copy

    @property
    def ancestor(self) -> Parameter:
        return self if self.parent is None else self.parent.ancestor

    def complete_unspecified_attributes(self) -> None:
        pass

    def validate_attributes(self) -> None:
        pass
