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

import clusterondemandconfig

from .command_configuration import CommandConfiguration
from .configuration_item import ConfigurationItem
from .configuration_view import MutableConfigurationView


class GlobalConfiguration(MutableConfigurationView):
    """The configuration that is globally available. Only meant to wrap an actual CommandConfiguration object."""

    config: CommandConfiguration | dict[Any, Any] = {}

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        # TODO: CM-20154, mutability is doubleplusungood.
        self.config[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.config

    def get_item_for_key(self, key: str) -> ConfigurationItem:
        assert isinstance(self.config, CommandConfiguration)
        return self.config.get_item_for_key(key)

    def is_item_set_explicitly(self, key: str) -> bool:
        return isinstance(self.get_item_for_key(key).source, clusterondemandconfig.sources.CLISource)

    def is_item_set_from_defaults(self, key: str) -> bool:
        return isinstance(
            self.get_item_for_key(key).source,
            (
                clusterondemandconfig.sources.StaticDefaultSource,
                clusterondemandconfig.sources.DynamicDefaultSource,
            ),
        )

    def __format__(self, fmt: str) -> str:
        return str(self[fmt])
