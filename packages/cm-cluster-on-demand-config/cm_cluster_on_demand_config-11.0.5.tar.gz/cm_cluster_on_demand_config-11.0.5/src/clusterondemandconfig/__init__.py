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

from .command_context import CommandContext
from .config_dump import full_ini_config_dump, human_readable_config_dump, minimal_ini_config_dump
from .config_namespace import ConfigNamespace
from .configuration_validation import (
    ask_for_password_if_not_set,
    cannot_enable_together,
    cannot_use_together,
    files_and_urls_accessible,
    if_not_set_requires_other_parameters_to_be_set,
    if_set_file_exists_and_readable,
    ignore_if_default,
    match_http_proxy_format,
    may_not_equal_none,
    must_be_multiple_of,
    must_be_valid_timezone,
    number_greater_equal,
    number_must_be_between,
    other_parameter_must_not_equal,
    require_at_least_one_to_be_set,
    require_exactly_one_to_be_set,
    require_exactly_one_to_be_true,
    requires_at_least_one_other_parameter,
    requires_other_parameter_to_be_set,
    validate_configuration
)
from .determine_invoked_command import determine_invoked_command
from .exceptions import ConfigLoadError, UnknownCLIArgumentError, UnknownConfigFileParameterError
from .explain import explain_parameter
from .global_config import config, global_configuration
from .load_configuration import (
    check_for_unknown_config_parameters,
    load_boot_configuration_for_command,
    load_configuration_for_command,
    load_configuration_for_parameters
)
from .print_help import (
    DEFAULT_HELP_SECTION,
    print_help,
    print_help_for_positionals_missing_required_value,
    print_help_for_unknown_parameters
)
from .tab_completion import generate_tabcompletion_for_command_context

BCM_VERSION = "trunk"

__all__ = [
    "CommandContext",
    "ConfigNamespace",
    "ConfigLoadError",
    "DEFAULT_HELP_SECTION",
    "UnknownCLIArgumentError",
    "UnknownConfigFileParameterError",
    "ask_for_password_if_not_set",
    "cannot_enable_together",
    "cannot_use_together",
    "config",
    "determine_invoked_command",
    "explain_parameter",
    "full_ini_config_dump",
    "files_and_urls_accessible",
    "generate_tabcompletion_for_command_context",
    "global_configuration",
    "human_readable_config_dump",
    "if_set_file_exists_and_readable",
    "load_boot_configuration_for_command",
    "load_configuration_for_command",
    "load_configuration_for_parameters",
    "check_for_unknown_config_parameters",
    "match_http_proxy_format",
    "may_not_equal_none",
    "must_be_multiple_of",
    "must_be_valid_timezone",
    "minimal_ini_config_dump",
    "number_greater_equal",
    "number_must_be_between",
    "other_parameter_must_not_equal",
    "print_help",
    "print_help_for_positionals_missing_required_value",
    "print_help_for_unknown_parameters",
    "require_exactly_one_to_be_set",
    "require_exactly_one_to_be_true",
    "requires_at_least_one_other_parameter",
    "requires_other_parameter_to_be_set",
    "require_at_least_one_to_be_set",
    "validate_configuration",
    "ignore_if_default",
    "if_not_set_requires_other_parameters_to_be_set",
]
