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

if TYPE_CHECKING:
    from ..parameter import Parameter
    from ..sources import Source


class ConfigurationItem:
    """Represents a value as it was found in one of the configuration sources.

    :attr parameter: The parameter to which the value and source are assigned.
    :attr value: The value that was found in a configuration source.
    :attr source: A human-readable string that specifies how the value was specified,
        e.g. in which config file it was specified.
    """

    def __init__(self, parameter: Parameter, value: Any | None = None, source: Source | None = None) -> None:
        self.parameter = parameter
        self.value = value
        self.source = source
        self.locked = False

    @property
    def key(self) -> str:
        return self.parameter.key

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other: Any) -> bool:  # pragma: no cover
        return not self == other
