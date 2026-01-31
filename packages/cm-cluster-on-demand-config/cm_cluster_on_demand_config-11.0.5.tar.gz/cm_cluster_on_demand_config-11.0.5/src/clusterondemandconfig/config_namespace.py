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

import copy
from typing import TYPE_CHECKING, Any, Callable

from .exceptions import ConfigConstructError
from .parameter import (
    EnumerationParameter,
    OptionalParameter,
    Parameter,
    RepeatingPositionalParameter,
    SimpleParameter,
    SimplePositionalParameter,
    SwitchParameter
)

if TYPE_CHECKING:
    from .configuration import CommandConfiguration
    from .parameter.parameter import ParamValidationsType, ParserType, SerializerType

    ConfigValidationType = Callable[["ConfigNamespace", CommandConfiguration], None]


class ConfigNamespace:
    """A utility class for creating and maintaining a group of configuration parameters.

    The values for these parameters can be read from configuration files, environment variables and
    the command line, depending on the type of the parameter. A positional parameter may only be set
    through the CLI, all other parameters can be set through either a config file, ENV variable or
    command line argument.

    There are several kinds of configuration parameters:
      - parameter: a simple key value mapping.

        Create with:
          instance.add_parameter('param')

        To set the value:
          CLI:         --param bar
          config file: param=bar
          ENV:         COD_PARAM=bar

      - enumeration: a key that maps to a list of items. These items are separated by a space on the
        cli and by a comma when stored in an environment variable or config file. Three modes of
        passing the values are supported: overwriting, prepending or appending to the existing
        value. The latter two can be specified by using the prefix prepend or append.

        Create with:
          instance.add_enumeration_parameter('enum')

        To set the value:
          CLI:         --enum foo bar baz   or   --enum foo --enum bar --enum baz
          config file: enum=foo,bar,baz
          ENV:         COD_ENUM=foo,bar,baz

        To prepend to a possibly existing list of values:
          CLI:         --prepend-enum bar
          config file: prepend-enum=bar
          ENV:         COD_PREPEND_ENUM=bar

        To append to a possibly existing list of values:
          CLI:         --append-enum bar
          config file: append-enum=bar
          ENV:         COD_APPEND_ENUM=bar


      - switch: a key that maps to a boolean value. No value needs to be given on the command line,
        because the presence or absence of the switch is enough to determine the boolean value.

        Create with:
          instance.add_switch_parameter('switch')

        To set the value to True:
          CLI:         --switch
          config-file: switch=True
          ENV:         COD_SWITCH=True

        To set the value to False in order to override another source that sets it to True:
          CLI:         --no-switch
          config-file: switch=False
          ENV:         COD_SWITCH=False


      - positional: a CLI-only parameter that is not preceded by a flag. It cannot be set through an
        environment variable or config file. Optional positional parameters are possible, they
        appear after any mandatory positional parameters and only one is possible per namespace. A
        namespace cannot have both an optional positional as well as a mandatory or optional
        repeating positional parameter.

        Create with:
          instance.add_positional_parameter('name')

        To create a cluster named 'foo' when a positional parameter named 'name' is expected:
          CLI:         `cm-cod-os cluster create foo`
          config-file: not supported, a warning is generated if set and the value is not used
          ENV:         not supported, a warning is generated if set and the value is not used


      - repeating positional: a CLI-only parameter that takes space separated values. It can only
        appear once in a namespace and is placed after any mandatory non-repeating positional
        parameters. If required, then at least a single value is required.

        Create with:
          instance.add_repeating_positional_parameter('names')

        To delete multiple clusters by specifying values for repeating positional named 'names':
          CLI:         `cm-cod-os cluster delete foo bar baz`
          config-file: not supported, a warning is generated if set and the value is not used
          ENV:         not supported, a warning is generated if set and the value is not used

    Note that for every CLI item of the form --foo bar, --foo=bar is also acceptable.

    This class helps with collecting configuration parameters into logical units. A namespace can
    import the parameters of another. For example, an 'azure.cluster.create' namespace can import
    the parameters of a generic 'cluster.create' action. When a namespace is imported, copies of the
    parameters of the imported namespace also become available in the importing namespace.

    A namespace can also be coupled to a CLI action such as 'cm-cod-azure cluster create'. For an
    action, only the parameters that belong to the coupled namespace can be set on the command line
    and the (advanced) help output will only mention those parameters.

    The factory methods take several keywords for specifying the attributes of the configuration
    parameters. Note that most keywords are not applicable to all parameters. Check the signatures
    of the factory method to see which parameters are accepted.
    In alphabetical order:
      - advanced: advanced configuration parameters are not shown in the normal help output. They
        are only visible in the advanced help output.
        Default: False
      - boot: boot parameters are loaded before any other parameters. As such, they can act as
        configuration parameters for cod-config and control how the configuration is loaded.
        Default: False.
      - choices: simple parameters and enumeration parameters can take a list of choices. When the
        user sets a value for such a parameter and that value is not part of the choice, an error is
        raised.
      - default: the default value for an optional item or item enumeration. The default value of a
        switch is False. This can also be a function, this function takes a parameter and the
        configuration and is called after the configuration has been filled with values from the
        config files and other sources.
        Default: None
        If choices is given, default MUST be in this set. If type is specified, default MUST be of
        this type.
      - env: the upper case name of the environment variable that sets this value.
        Default: 'name' in upper case with prefix COD_.
        MUST be a valid environment variable name. MUST not conflict with another (imported)
        parameter in the same namespace.
      - flags: a list of strings prefixed with a single or double hyphen. These become available as
        CLI parameters in addition to the 'name' prefixed with '--'.
        Default: an empty list.
        Each entry in the list MUST be a valid CLI parameter (e.g. may not contain spaces). MUST not
        conflict with another (imported) flag in the same namespace.
      - help: a human readable text that explains the intended consequences of the parameter. The
        text should not mention the default value, logical namespace, or how to pass the value,
        because this information is automatically added by the ConfigHelpPrinter. A dot is
        automatically added at the end if there was none.
        Default: an empty string.
      - help_choices: A dictionary that maps choices to human readable text. Shown in the help
        output. The dictionary does not need to contain an entry for every choice.
        Default: an empty dictionary.
      - help_section: The human readable name of the help page section in which the full explanation
        of this configuration parameter will appear. This is used to group related configuration
        parameters on the help page.
        Default: None
      - help_varname: Similar to 'metavar' in argparse. For example, for the help output of a
        configuration item named 'ssh-pub-key', with help_varname='SOMEPATH', the help output
        will contain --ssh-pub-key SOMEPATH.
        Default: 'name' in upper case.
      - key: the attribute of the valuated configuration object that stores the configuration value.
        Default: 'name' in camel case.
      - parser: a function that takes an input string as given on the cli, env or config file, and
        returns a single value of type 'type'. If 'type' is a list, then the parser must return a
        value of type 'type[0]'.
        Default: type or type[0], applied as a function.
      - require_value: whether a value must be specified. Can only be set for positional parameters.
        Other parameters can use the `may_not_equal_none` validation to enforce this rule.
        Default: False.
      - secret: a boolean that indicates whether the value of the parameter should be removed or
        otherwise masked when the configuration is converted into a string, e.g. through
        `config dump`, or the value is otherwise logged.
      - serializer: a function that takes a single value of type 'type' and returns a human readable
        string. Used for dumping the valuated parameter to a human readable form.
        Default: str
      - type: an instance of Python type or a list containing a single python type. The result will
        be casted to this type. If type is bool, then certain english language variations or
        numerical variations of True and False will be accepted. For enumerations and repeating
        positional parameters, it must be a list. For other types of parameters it may not be a
        list.
        Default: depends on the type of default or choices, otherwise str or [str].
      - validation: a function, or list of such functions, that takes two arguments: an instance of
        the Parameter and the CommandConfiguration. If there is an issue with the configuration, the
        function may raise an exception, it may also modify the configuration to fix the issue.
    """

    def __init__(self, name: str, help_section: str | None = None) -> None:
        """
        Create a new instance. A new instance does not come with default parameters.

        :param name A name that consists of lowercase words separated by dots. Identifies the
                    namespace. Is used to group parameters in a config file.
        :param help_section If the parameters of this namespace can be naturally grouped into a
                            single section of the help output, then set this value to be the
                            name of the section.
        """
        self.name = name
        self.help_section = help_section
        self._parameters: list[Parameter] = []
        self.validation: list[ConfigValidationType] = []

    @property
    def parameters(self) -> list[Parameter]:
        return list(self._parameters)

    # The methods add_*_parameter below have the same signature as the constructors of the corresponding parameter
    # classes. Unfortunately, at this moment there's no way to copy their signature using python typing capabilities.
    # Of course it's possible to bypass all parameters using args/kwargs or dynamic code generation as was before,
    # but all these ways doesn't let us to use static typing.

    def add_parameter(
        self,
        name: str,
        advanced: bool = False,
        boot: bool = False,
        choices: list[Any] | None = None,
        default: Any = None,
        env: str | None = None,
        flags: list[str] | None = None,
        help: str = "",
        help_choices: dict[str, str] | None = None,
        help_section: str | None = None,
        help_varname: str | None = None,
        key: str | None = None,
        parser: ParserType | None = None,
        secret: bool = False,
        serializer: SerializerType = str,
        type: Any = None,
        validation: ParamValidationsType | None = None,
    ) -> None:
        self._append_parameter(
            SimpleParameter(name, advanced=advanced, boot=boot, choices=choices, default=default, env=env, flags=flags,
                            help=help, help_choices=help_choices, help_section=help_section, help_varname=help_varname,
                            key=key, parser=parser, secret=secret, serializer=serializer, type=type,
                            validation=validation)
        )

    def add_switch_parameter(
        self,
        name: str,
        advanced: bool = False,
        boot: bool = False,
        default: bool = False,
        env: str | None = None,
        flags: list[str] | None = None,
        help: str = "",
        help_section: str | None = None,
        key: str | None = None,
        validation: ParamValidationsType | None = None,
    ) -> None:
        self._append_parameter(
            SwitchParameter(name, advanced=advanced, boot=boot, default=default, env=env, flags=flags, help=help,
                            help_section=help_section, key=key, validation=validation)
        )

    def add_enumeration_parameter(
        self,
        name: str,
        advanced: bool = False,
        boot: bool = False,
        choices: list[Any] | None = None,
        default: Any = None,
        env: str | None = None,
        flags: list[str] | None = None,
        help: str = "",
        help_choices: dict[str, str] | None = None,
        help_section: str | None = None,
        help_varname: str | None = None,
        key: str | None = None,
        parser: ParserType | None = None,
        secret: bool = False,
        serializer: SerializerType = str,
        type: Any = None,
        validation: ParamValidationsType | None = None,
    ) -> None:
        self._append_parameter(
            EnumerationParameter(name, advanced=advanced, boot=boot, choices=choices,
                                 default=default, env=env, flags=flags, help=help, help_choices=help_choices,
                                 help_section=help_section, help_varname=help_varname, key=key, parser=parser,
                                 secret=secret, serializer=serializer, type=type, validation=validation)
        )

    def add_positional_parameter(
        self,
        name: str,
        default: Any = None,
        help: str = "",
        help_section: str | None = None,
        help_varname: str | None = None,
        key: str | None = None,
        parser: ParserType | None = None,
        require_value: bool = False,
        secret: bool = False,
        serializer: SerializerType = str,
        type: Any = None,
        validation: ParamValidationsType | None = None,
    ) -> None:
        self._append_parameter(
            SimplePositionalParameter(name, default=default, help=help, help_section=help_section,
                                      help_varname=help_varname, key=key, parser=parser, require_value=require_value,
                                      secret=secret, serializer=serializer, type=type, validation=validation)
        )

    def add_repeating_positional_parameter(
        self,
        name: str,
        default: Any = None,
        help: str = "",
        help_section: str | None = None,
        help_varname: str | None = None,
        key: str | None = None,
        parser: ParserType | None = None,
        require_value: bool = False,
        secret: bool = False,
        serializer: SerializerType = str,
        type: Any = None,
        validation: ParamValidationsType | None = None,
    ) -> None:
        self._append_parameter(
            RepeatingPositionalParameter(name, default=default, help=help, help_section=help_section,
                                         help_varname=help_varname, key=key, parser=parser, require_value=require_value,
                                         secret=secret, serializer=serializer, type=type, validation=validation)
        )

    def import_namespace(self, other_ns: ConfigNamespace) -> None:
        """
        Add copies of the parameters of another namespace to this namespace. Also imports the validations.

        :param other_ns ConfigNamespace
        """
        for parameter in other_ns.parameters:
            self._append_parameter(copy.copy(parameter))
        for validation in other_ns.validation:
            self.add_validation(validation)

    def override_imported_parameter(self, name: str, **kwargs: Any) -> None:
        """Set attributes of a parameter that was previously imported from another namespace.

        :param name str The name of the parameter. Raises if that parameter could be found.
        :param kwargs a mapping of parameter attributes to their new values

        This method is useful when this parameter has a different default value or help text within
        the context of this namespace.
        """
        parameter = next((p for p in self._parameters if p.name == name), None)
        if parameter is None:
            raise ConfigConstructError("parameter %s does not exist in this namespace" % name)
        for (attr, value) in kwargs.items():
            if hasattr(parameter, attr):
                setattr(parameter, attr, value)
            else:
                raise ConfigConstructError("parameter %s does not have attribute %s" % (name, attr))
        parameter.validate_attributes()
        parameter.complete_unspecified_attributes()
        parameter.validate_attributes()

    def remove_imported_parameter(self, name: str) -> None:
        """Removes a parameter that was previously imported from another namespace.

        :param name str The name of the parameter. Raises if that parameter could be found.

        This method can be used when you want a certain parameter to be globally parameter in all namespaces
        but not in a certain inheriting namespace.
        """
        parameter = next((p for p in self._parameters if p.name == name), None)
        if parameter is None:
            raise ConfigConstructError("parameter %s does not exist in this namespace" % name)
        self._parameters.remove(parameter)

    def add_validation(self, validation: Callable[..., Any]) -> None:
        self.validation.append(validation)

    def _append_parameter(self, parameter: Parameter) -> None:
        self._check_for_collisions_with_other_parameters(parameter)
        self._check_for_collisions_with_other_namespaces(parameter)

        parameter.namespace = self
        parameter.namespaces = parameter.namespaces + [self.name]
        if self.help_section is not None and parameter.help_section is None:
            parameter.help_section = self.help_section
        self._parameters.append(parameter)

    def _check_for_collisions_with_other_parameters(self, parameter: Parameter) -> None:
        """Raise if there is a conflict between 'parameter' and any one of 'other_parameters'."""
        for p in self._parameters:
            if p.name == parameter.name:
                raise ConfigConstructError("Parameter named %s already exists in namespace %s" % (p.name, self.name))
            if p.key and p.key == parameter.key:
                raise ConfigConstructError("%s.key conflicts with %s.key" % (parameter.name, p.name))

            if isinstance(parameter, OptionalParameter) and isinstance(p, OptionalParameter):
                if p.env and p.env == parameter.env:
                    raise ConfigConstructError("%s.env conflicts with %s.env" % (parameter.name, p.name))

                shared_flags = set(p.all_flags).intersection(set(parameter.all_flags))
                if shared_flags:
                    raise ConfigConstructError("%s.flags conflicts with %s.flags on: %s" %
                                               (parameter.name, p.name, ", ".join(shared_flags)))

            if isinstance(parameter, RepeatingPositionalParameter) and \
               isinstance(p, RepeatingPositionalParameter):
                raise ConfigConstructError("%s conflicts with %s: a namespace can only contain one "
                                           "repeating positional parameter" % (parameter.name, p.name))

    def _check_for_collisions_with_other_namespaces(self, parameter: Parameter) -> None:
        """Raise if there is a conflict between this namespace and any of the other namespaces of 'parameter'."""
        if self.name in parameter.namespaces:
            raise ConfigConstructError(
                "Parameter '%s' is already member of a namespace named '%s'" % (parameter.name, self.name)
            )
