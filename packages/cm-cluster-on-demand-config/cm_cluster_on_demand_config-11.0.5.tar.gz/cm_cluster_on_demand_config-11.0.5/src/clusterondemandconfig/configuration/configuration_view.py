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
from typing import TYPE_CHECKING, Any

from ..parameter import OptionalParameter

if TYPE_CHECKING:
    from .configuration_item import ConfigurationItem


class ConfigurationView(metaclass=ABCMeta):  # pragma: no cover
    """Shared interface for CommandConfiguration, ConfigurationForNamespaceView and GlobalConfiguration."""

    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        pass

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        pass

    @abstractmethod
    def get_item_for_key(self, key: str) -> ConfigurationItem:
        pass

    @abstractmethod
    def __format__(self, format: str) -> str:
        pass

    def get(self, key: str, default: Any = None) -> Any:
        return self[key] if key in self else default

    def item_repr(self, key: str) -> str:
        parameter = self.get_item_for_key(key).parameter
        assert isinstance(parameter, OptionalParameter)
        return f"{parameter.default_flag}={self[key]}"


class MutableConfigurationView(ConfigurationView):  # pragma: no cover
    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> None:
        pass
