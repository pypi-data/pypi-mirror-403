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

import glob
import logging
import os
from typing import Callable

from clusterondemandconfig import config
from clusterondemandconfig.exceptions import ConfigOpenError
from clusterondemandconfig.parameter import Parameter
from clusterondemandconfig.sources import (
    CLISource,
    ConfigFileSource,
    DynamicDefaultSource,
    EnforcingConfigFileSource,
    ENVSource,
    Source,
    StaticDefaultSource
)

log = logging.getLogger("cluster-on-demand")


class SourceType:
    """Factory class for Source instances."""
    def __init__(self, parameters: list[Parameter], system_config_files: list[str],
                 enforcing_config_files: list[str]) -> None:
        self._parameters = parameters
        self._enforcing_config_files = enforcing_config_files
        self._system_config_files = system_config_files

    def static_default(self) -> list[Source]:
        return [StaticDefaultSource()]

    def enforcing_config_files(self) -> list[Source]:
        return list(map(
            EnforcingConfigFileSource, _readable_config_files_for_glob_patterns(self._enforcing_config_files)
        ))

    def system_config_files(self) -> list[Source]:
        if "system_config" in config and config["system_config"]:
            return list(map(ConfigFileSource, _readable_config_files_for_glob_patterns(self._system_config_files)))

        return []

    def cli_config_files(self) -> list[Source]:
        if "config" not in config:
            return []

        cli_config_files = []

        for config_file in config["config"] or []:
            if not os.path.isfile(config_file) or not os.access(config_file, os.R_OK):
                raise ConfigOpenError("Config file %s does not exist or is not readable" % (config_file))
            cli_config_files.append(config_file)

        return list(map(ConfigFileSource, cli_config_files))

    def env(self) -> list[Source]:
        return [ENVSource()]

    def loose_cli(self) -> list[Source]:
        # TODO: improve name, a loose cli source simply doesn't complain about unknown flags.
        return [CLISource(self._parameters, strict=False)]

    def strict_cli(self) -> list[Source]:
        return [CLISource(self._parameters, strict=True)]

    def dynamic_default(self) -> list[Source]:
        return [DynamicDefaultSource()]


def generate_sources(
    source_order: list[Callable[[SourceType], list[Source]]],
    parameters: list[Parameter],
    system_config_files: list[str],
    enforcing_config_files: list[str],
) -> list[Source]:
    """Convert `source_order` into an ordered list of Source instances.

    `source_order` is expected to be a list of unbound methods of SourceType. These methods take an
    instance of SourceType and return a list of Source instances.
    """
    sources: list[Source] = []
    factory = SourceType(parameters, system_config_files, enforcing_config_files)

    for source in source_order:
        sources.extend(source(factory))

    return sources


def _readable_config_files_for_glob_patterns(config_file_globs: list[str]) -> list[str]:
    config_file_paths = []

    for config_file_glob in config_file_globs:
        log.debug("Searching for config files at: %s" % (config_file_glob))
        for config_file_path in sorted(glob.glob(config_file_glob)):
            if not os.access(config_file_path, os.R_OK):
                raise ConfigOpenError("Config file %s is not readable" % (config_file_path))
            config_file_paths.append(config_file_path)

    return config_file_paths
