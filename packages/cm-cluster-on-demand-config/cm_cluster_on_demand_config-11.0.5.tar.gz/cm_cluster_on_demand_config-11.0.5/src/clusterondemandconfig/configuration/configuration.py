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

from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config_namespace import ConfigNamespace
    from ..parameter import Parameter
    from ..sources import Source
    from .configuration_item import ConfigurationItem
    from .configuration_view import ConfigurationView


class Configuration(metaclass=ABCMeta):  # pragma: no cover
    """Shared interface for CommandConfiguration and CollectiveConfiguration."""

    @abstractmethod
    def __init__(self, parameters: list[Parameter]) -> None:
        pass

    @abstractmethod
    def view_for_namespace(self, namespace: ConfigNamespace | None) -> ConfigurationView:
        pass

    @abstractmethod
    def set_value(self, parameter: Parameter, value: Any, source: Source) -> None:
        pass

    @abstractmethod
    def set_locked_value(self, parameter: Parameter, value: Any, source: Source) -> None:
        pass

    @abstractmethod
    def is_value_locked_for_parameter(self, parameter: Parameter) -> bool:
        pass

    @abstractmethod
    def get_parameter_value(self, parameter: Parameter) -> Any:
        pass

    @abstractmethod
    def get_source_of_parameter_value(self, parameter: Parameter) -> Source | None:
        pass

    @abstractmethod
    def reduced_dict(self) -> dict[str, ConfigurationItem]:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[tuple[str, ConfigurationItem]]:
        pass
