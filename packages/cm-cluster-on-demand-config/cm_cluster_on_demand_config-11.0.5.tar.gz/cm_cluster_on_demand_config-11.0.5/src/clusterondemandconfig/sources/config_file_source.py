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

import configparser
import io
import logging
import re
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from clusterondemandconfig.exceptions import ConfigLoadError
from clusterondemandconfig.expression_parser import parse_expression
from clusterondemandconfig.global_config import config

from .source import Source

if TYPE_CHECKING:
    from ..configuration import Configuration
    from ..parameter import Parameter


log = logging.getLogger("cluster-on-demand")

COMMENT_UNTIL_END_OF_LINE_REGEX = r"#.*"
URL_IN_CONFIG_FILE_REGEX = r"remote:([^#]+)"


class ConfigFileSource(Source):
    """Parameter value source for the config loader that obtains values from a single ini file."""

    def __init__(self, config_file: str) -> None:
        self.config_file = config_file
        self._parser: configparser.ConfigParser | None = None

    def is_enforcing(self) -> bool:
        return False

    def __str__(self) -> str:
        return "file: " + self.config_file  # TODO: show line

    def has_value_for_parameter(self, parameter: Parameter, configuration: Configuration) -> bool:
        for namespace in parameter.namespaces:
            if self.parser.has_option(namespace, parameter.name):
                return True
        return False

    def get_value_for_parameter(self, parameter: Parameter, configuration: Configuration) -> Any:
        assert self.has_value_for_parameter(parameter, configuration)

        try:
            current_value = configuration.get_parameter_value(parameter)
            for namespace in parameter.namespaces:
                if self.parser.has_option(namespace, parameter.name):
                    expression = self.parser.get(namespace, parameter.name)
                    current_value = parse_expression(expression, parameter, current_value)

            return current_value
        except Exception as e:
            raise ConfigLoadError(
                "An error occured when parsing the value for parameter '%s' set in %s:\n\t%s" %
                (parameter.name, self.config_file, e)
            )

    def __eq__(self, other: Any) -> bool:  # pragma: no cover
        return type(self) is type(other) and self.config_file == other.config_file

    def get_parameters(self) -> Iterator[tuple[str, str]]:
        for section in self.parser.sections():
            for option in self.parser.options(section):
                yield (section, option)

    @property
    def parser(self) -> configparser.ConfigParser:
        if self._parser is None:
            self._parser = _config_parser_for_file(self.config_file)
        return self._parser


def _config_parser_for_file(config_file: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    try:
        log.debug("Using config file: %s" % (config_file))
        if _config_file_contains_remote_link(config_file):
            if url := _url_in_config_file(config_file):
                parser.read_file(_remote_config_file_stream(url))
        else:
            parser.read(config_file)
        return parser
    except configparser.Error:
        log.error("Error when parsing config file %s" % (config_file))
        raise ConfigLoadError("Config file %s is not a valid INI file." % (config_file))


def _config_file_contains_remote_link(config_file: str) -> bool:
    with open(config_file) as f:
        contents = f.read().strip()
        contents = re.sub(COMMENT_UNTIL_END_OF_LINE_REGEX, "", contents).strip()

        return 1 == len(contents.split("\n")) and contents.startswith("remote:")


def _url_in_config_file(config_file: str) -> str | None:
    with open(config_file) as f:
        match = re.search(URL_IN_CONFIG_FILE_REGEX, f.read())
        if not match:
            log.error("Error when parsing config file %s: invalid remote link format" % (config_file))
            raise ConfigLoadError("Config file %s contains a remote link in invalid format." % (config_file))
        url = match.group(1).strip()

        # Only certain keys are allowed in "special" Python format specifiers
        match = re.search(r"{:(\w+)}", url)
        if match:
            user_key = match.group(1).strip()
            VALID_KEYS = "os_auth_host", "os_auth_url"
            if user_key not in VALID_KEYS:
                raise ConfigLoadError("Key '%s' required by %s is not allowed, allowed keys in remote link "
                                      "specifications are: %s" % (user_key, config_file, ", ".join(VALID_KEYS)))

            if not config[user_key]:
                log.warning("Key '%s' required by %s is not set, ignoring this source" % (user_key, config_file))
                log.debug("%s may only be specified as environment variable or command line argument, "
                          "not in a config file (any config file entries will be ignored in remote links)" % (user_key))
                return None

        return url.format(config)


def _remote_config_file_stream(url: str) -> io.StringIO:
    stream = io.StringIO()
    try:
        log.debug("Downloading remote config file from: %s" % (url))
        stream.write(urllib.request.build_opener().open(url, timeout=5.0).read().decode("utf-8"))
        stream.seek(0)
    except urllib.error.URLError as error:
        log.error("Could not download the configuration from %s, ignoring this source" % (url))
        log.debug("(Error was: %s)" % (error))
    return stream
