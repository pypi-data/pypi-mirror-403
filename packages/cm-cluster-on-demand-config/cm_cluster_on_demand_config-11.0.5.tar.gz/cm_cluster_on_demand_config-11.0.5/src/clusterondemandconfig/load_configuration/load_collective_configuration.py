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
from collections import defaultdict
from collections.abc import Iterable
from typing import Callable, DefaultDict

from clusterondemandconfig.configuration import CollectiveConfiguration
from clusterondemandconfig.exceptions import UnknownConfigFileParameterError
from clusterondemandconfig.parameter.optional_parameter import OptionalParameter
from clusterondemandconfig.parameter.parameter import Parameter
from clusterondemandconfig.sources import ConfigFileSource
from clusterondemandconfig.sources.source import Source

from .generate_sources import SourceType, generate_sources
from .shared import assign_value, can_obtain_parameter_value_from_source, warn_about_locked_value

log = logging.getLogger("cluster-on-demand")


def load_configuration_for_parameters(parameters: Iterable[Parameter], system_config_files: list[str],
                                      enforcing_config_files: list[str]) -> CollectiveConfiguration:
    """Parse the config files to produce a valuated CollectiveConfiguration object.

    The sources are applied in a certain order. For each parameter, each source that has a value for
    that parameter overrides the value that was obtained from a previous source.
    If no config file specified a value for a parameter, the default of the parameter is used.

    The CollectiveConfiguration combines the parameters of different commands, so within the
    configuration, many parameters will appear several times; for the commands they are used in,
    but also for the parent and grandparent namespaces from which the commands inherited those
    parameters. For every namespace that a parameter appears in, a value will be obtained from the
    sources.

    The order in which the sources are applied is:
    - the enforcing config files, in the order they are obtained from the `enforcing_config_files` globs,
    - the system config files, in the order they are obtained from the `system_config_files` globs,
    - the config files declared on the command line, in the order they appear on the command line,
    - the parameter defaults, but only if no other source specified a value for that parameter.

    :param parameters: A list of Parameter instances, for which the values will be read
    :param system_config_files: A list glob patterns that specify the locations of the
                                configuration files.
    :param enforcing_config_files: A list glob patterns that specify the locations of the
                                   enforcing configuration files.
    :return CollectiveConfiguration
    """
    order_of_sources: list[Callable[[SourceType], list[Source]]] = [
        SourceType.static_default,
        SourceType.enforcing_config_files,
        SourceType.system_config_files,
        SourceType.cli_config_files,
        SourceType.dynamic_default,
    ]
    parameters = _expand_parameter_list_to_include_all_ancestors(parameters)
    sources = generate_sources(order_of_sources, parameters, system_config_files, enforcing_config_files)

    configuration = CollectiveConfiguration(parameters)
    _load_configuration_from_sources(configuration, sources, parameters)
    return configuration


def check_for_unknown_config_parameters(parameters: Iterable[Parameter], system_config_files: list[str],
                                        enforcing_config_files: list[str], ignore_unknown_namespaces: bool) -> None:
    """Check config files don't have unknown parameters.

    Make sure that you specified all possible parameters of all COD commands.

    :param parameters: A list of Parameter instances, for which the values will be read
    :param system_config_files: A list glob patterns that specify the locations of the
                                configuration files.
    :param enforcing_config_files: A list glob patterns that specify the locations of the
                                   enforcing configuration files.
    :param ignore_unknown_namespaces: Check only those config file sections which have at least
                                      one known parameter related to them.
    """

    order_of_sources: list[Callable[[SourceType], list[Source]]] = [
        SourceType.enforcing_config_files,
        SourceType.system_config_files,
        SourceType.cli_config_files,
    ]

    parameters = _expand_parameter_list_to_include_all_ancestors(parameters)

    sources: list[ConfigFileSource] = []
    for source in generate_sources(order_of_sources, parameters, system_config_files, enforcing_config_files):
        assert isinstance(source, ConfigFileSource)
        sources.append(source)

    params_by_name: DefaultDict[str, set[str]] = defaultdict(set)
    all_namespaces = set()
    for param in parameters:
        namespaces = set(param.namespaces)
        params_by_name[param.name] |= namespaces
        all_namespaces |= namespaces

    result = True
    for source in sources:
        for namespace, name in source.get_parameters():
            if (name in params_by_name and namespace in params_by_name[name] or
                    ignore_unknown_namespaces and namespace not in all_namespaces):
                continue
            # Don't break immediately to log all unknown parameters
            log.error("Config %s has unknown parameter: [%s] %s = ...", source, namespace, name)
            result = False
    if not result:
        raise UnknownConfigFileParameterError


def _load_configuration_from_sources(configuration: CollectiveConfiguration, sources: Iterable[Source],
                                     parameters: Iterable[Parameter]) -> None:
    for source in sources:
        for parameter in _parameters_sorted_by_depth(parameters):
            if source.has_value_for_parameter(parameter, configuration):
                _assign_value_for_parameter_from_source(configuration, parameter, source)


def _parameters_sorted_by_depth(parameters: Iterable[Parameter]) -> list[Parameter]:
    """Sort parameters by placing specific parameters before more generic parameters.

    Generic parameters must be assigned a value before specific parameters, because otherwise the
    values of the more generic parameter will incorrectly overwrite those of its more specific descendants.
    """
    return sorted(parameters, key=lambda parameter: len(parameter.namespaces))


def _assign_value_for_parameter_from_source(configuration: CollectiveConfiguration, parameter: Parameter,
                                            source: Source) -> None:
    if not can_obtain_parameter_value_from_source(parameter, source):
        log.warning("Ignoring value for parameter '%s' mentioned in source %s" % (parameter.name, source))
        return

    if configuration.is_value_locked_for_parameter(parameter) \
       and not _can_override_lock(configuration, parameter, source):
        assert isinstance(parameter, OptionalParameter)
        warn_about_locked_value(configuration, parameter, source)
        return

    assign_value(configuration, parameter, source)


def _expand_parameter_list_to_include_all_ancestors(parameters: Iterable[Parameter]) -> list[Parameter]:
    all_parameters = set()

    for parameter in parameters:
        current: Parameter | None = parameter
        while current:
            all_parameters.add(current)
            current = current.parent

    return list(all_parameters)


def _can_override_lock(configuration: CollectiveConfiguration, parameter: Parameter, source: Source) -> bool:
    """A configuration value can only be overridden when the source of the new value is the same as the old.

    This only applies to the CollectiveConfiguration, as those can read multiple values from the source for a
    single parameter (through the inheritance).
    """
    return configuration.get_source_of_parameter_value(parameter) == source
