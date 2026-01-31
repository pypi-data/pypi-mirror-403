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

if TYPE_CHECKING:
    from ..configuration import Configuration
    from ..parameter import Parameter


class Source(metaclass=ABCMeta):
    """Abstract superclass that specifies all public methods that a Source must implement."""

    @abstractmethod
    def has_value_for_parameter(
        self, parameter: Parameter, configuration: Configuration
    ) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def is_enforcing(self) -> bool:
        pass

    @abstractmethod
    def get_value_for_parameter(
        self, parameter: Parameter, configuration: Configuration
    ) -> Any:  # pragma: no cover
        pass

    def get_location_of_parameter_value(self, parameter: Parameter) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:  # pragma: no cover
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other: Any) -> bool:  # pragma: no cover
        return not self == other
