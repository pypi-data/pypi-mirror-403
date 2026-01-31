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

import string
from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING

from ..config_file_encoding import encode
from .utils import generate_description

if TYPE_CHECKING:
    from ..configuration import CollectiveConfiguration
    _MappingType = Mapping[str, str]
else:
    _MappingType = Mapping


def minimal_ini_config_dump(config: CollectiveConfiguration, template: str) -> str:
    """Generate a minimal configuration dump according to a template."""
    return ConfigFileTemplate(template).substitute(ConfigWrapper(config)).lstrip()


class ConfigFileTemplate(string.Template):
    """Extend string.Template just to add the . character to idpattern and make $foo.bar a valid token."""
    idpattern = r"[_a-z][_a-z0-9\.]*"


class ConfigWrapper(_MappingType):
    def __init__(self, config: CollectiveConfiguration) -> None:
        self.config = config

    def __getitem__(self, key: str) -> str:
        item = self.config.get_item_for_unique_key(key)

        return "{description}\n{name} = {value}\n".format(
            description=generate_description(item),
            name=item.parameter.name,
            value=encode(item.parameter, item.value)
        )

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self.config)

    def __len__(self) -> int:
        return len(self.config)
