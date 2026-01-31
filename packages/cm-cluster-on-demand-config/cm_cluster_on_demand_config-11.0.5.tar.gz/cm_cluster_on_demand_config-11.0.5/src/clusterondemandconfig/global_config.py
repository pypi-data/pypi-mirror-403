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

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from .configuration import GlobalConfiguration

if TYPE_CHECKING:
    from .configuration import CommandConfiguration

# This placeholder will receive a configuration when `global_configuration` is called.
config = GlobalConfiguration()


@contextmanager
def global_configuration(new_config: CommandConfiguration | dict[Any, Any]) -> Iterator[None]:
    """Make the `new_config` parameter globally available through `clusterondemandconfig.config`."""
    try:
        old_config, config.config = config.config, new_config
        yield
    finally:
        config.config = old_config
