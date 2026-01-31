${title("NAME")}
  ${parameter.name} (${command})

${title("DESCRIPTION")}
${indent(wordwrap(parameter.help, width=100), 2)}

% for comment in comments:
${indent(wordwrap(comment, width=100), 2)}

% endfor

${title("NAMESPACES AND COMMANDS")}
  It is used in the following namespaces and commands

${indent(tree, 2)}

${title("HOW TO CONFIGURE")}
  On the Command Line:
% for cli_expression in cli_expressions:
    ${cli_expression}

% endfor

% if env_expressions:
  As Environment Variable:
  % for env_expression in env_expressions:
    ${env_expression}

  % endfor
% endif

% if config_file_expressions:
  In a Config File:
  % for config_file_expression in config_file_expressions:
${indent(config_file_expression, 4)}

  % endfor
% endif

% if alternatives:

${title("SEE ALSO")}
  These other parameters also matched the identifier. They are used in different commands.

${indent(alternatives, 2)}
% endif
