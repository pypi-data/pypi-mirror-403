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


class ConfigConstructError(Exception):
    """An error occurred while constructing the ConfigNamespace or the CommandContext object."""
    pass


class ConfigOpenError(Exception):
    """An error occured trying to access a config file."""
    pass


class ConfigLoadError(Exception):
    """An error occured while the configuration was loaded."""
    pass


class UnknownCLIArgumentError(ConfigLoadError):
    """An instance of CLISource detected an unknown flag."""

    def __init__(self, flags: list[str]) -> None:
        self.flags = flags


class UnknownConfigFileParameterError(ConfigLoadError):
    """An error occured if ConfigFileSource has unknown parameters."""
    pass


class ConfigValueIsLockedError(ConfigLoadError):
    """A value could not be loaded because the parameter was locked."""
    pass
