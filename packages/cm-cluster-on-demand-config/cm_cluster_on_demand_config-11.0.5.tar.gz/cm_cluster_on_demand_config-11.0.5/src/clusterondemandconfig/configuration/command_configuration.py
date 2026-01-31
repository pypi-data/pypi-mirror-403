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

import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from clusterondemandconfig.config_namespace import ConfigNamespace
from clusterondemandconfig.configuration.configuration_item import ConfigurationItem
from clusterondemandconfig.parameter import PositionalParameter

from .configuration import Configuration
from .configuration_view import MutableConfigurationView

if TYPE_CHECKING:
    from ..parameter import Parameter
    from ..sources import Source

log = logging.getLogger("cluster-on-demand")


class CommandConfiguration(Configuration, MutableConfigurationView):
    """Represents the configuration for a single Command. Only stores a single value per parameter."""

    def __init__(self, parameters: list[Parameter]) -> None:
        self._mutable = True
        self._keys_to_items = {parameter.key: ConfigurationItem(parameter) for parameter in parameters}

    def lock(self) -> None:
        self._mutable = False

    def view_for_namespace(self, namespace: ConfigNamespace | None) -> CommandConfiguration:
        return self

    def set_value(self, parameter: Parameter, value: Any, source: Source) -> None:
        assert not self.is_value_locked_for_parameter(parameter)

        item = self.get_item_for_key(parameter.key)
        item.value, item.source = value, source

    def set_locked_value(self, parameter: Parameter, value: Any, source: Source) -> None:
        assert not self.is_value_locked_for_parameter(parameter)

        item = self.get_item_for_key(parameter.key)
        item.value, item.source, item.locked = value, source, True

    def is_value_locked_for_parameter(self, parameter: Parameter) -> bool:
        return self.get_item_for_key(parameter.key).locked

    def get_item_for_key(self, key: str) -> ConfigurationItem:
        """Return the ConfigurationItem object that is mapped to the key."""
        if key in self._keys_to_items:
            return self._keys_to_items[key]

        raise KeyError("Programmer error: The parameter '%s' is not defined within this configuration." % key)

    def get_parameter_value(self, parameter: Parameter) -> Any:
        return self.get_item_for_key(parameter.key).value

    def get_source_of_parameter_value(self, parameter: Parameter) -> Source | None:
        return self.get_item_for_key(parameter.key).source

    def reduced_dict(self) -> dict[str, ConfigurationItem]:
        return self._keys_to_items

    def required_positionals_with_missing_values(self) -> list[PositionalParameter]:
        return [config_item.parameter
                for config_item in self._keys_to_items.values()
                if isinstance(config_item.parameter, PositionalParameter)
                and config_item.parameter.require_value
                and config_item.value is None]

    def __getitem__(self, parameter_key: str) -> Any:
        """Handle the [] operation. Return the value that was assigned to this parameter."""
        return self.get_item_for_key(parameter_key).value

    def __setitem__(self, parameter_key: str, value: Any) -> None:
        """Handle the []= operation. This is no bueno and could disappear with CM-20154."""
        if not self._mutable:
            log.debug("Dynamic modification of the config object: %s" % (parameter_key))
        self.get_item_for_key(parameter_key).value = value

    def __contains__(self, key: str) -> bool:
        return key in self._keys_to_items

    def __iter__(self) -> Iterator[tuple[str, ConfigurationItem]]:
        return iter(self._keys_to_items.items())

    def __format__(self, format: str) -> str:
        return str(self[format])
