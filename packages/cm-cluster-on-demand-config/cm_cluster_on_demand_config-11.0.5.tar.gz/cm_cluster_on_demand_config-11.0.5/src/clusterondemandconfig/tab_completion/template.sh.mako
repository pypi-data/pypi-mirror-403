#!/bin/sh -ex

_${tool.replace("-", "_")} ()
{
    local cur prev group command group_index command_index

    group_index=1
    command_index=2

    cur=${'${COMP_WORDS[COMP_CWORD]}'}
    prev=${'${COMP_WORDS[COMP_CWORD - 1]}'}

    # First scan, expect group and command to be separate
    if [[ ${'${COMP_WORDS[${group_index}]}'} != "-*" ]]; then
        group=${'${COMP_WORDS[${group_index}]}'}

        if [[ ${'${COMP_WORDS[${command_index}]}'} != "-*" ]]; then
            command=${'${COMP_WORDS[${command_index}]}'}
        fi
    fi

    have_to_complete_group=0; [[ -z ${'${group}'} ]] || [[ ${'${group_index}'} == ${'${COMP_CWORD}'} ]] && have_to_complete_group=1
    have_to_complete_command=0; [[ -z ${'${command}'} ]] || [[ ${'${command_index}'} == ${'${COMP_CWORD}'} ]] && have_to_complete_command=1

    COMPREPLY=()

    local top_level_flags
    # TODO: these need to be stored in, and generated from, the command context
    top_level_flags="-c --config -v -vv -vvv --show-configuration --log-file --version"

    # If we need to complete group
    if [[ 1 == $have_to_complete_group ]]; then
        COMPREPLY=( $( compgen -W "${' '.join(hierarchy.keys())} ${'${top_level_flags}'}" -- ${'${cur}'} ) );
        return 0
    fi

    # Rewrite group and command if a command alias was used
<% i = 0 %>
% for group in hierarchy:
  % for command in hierarchy[group]:
    % for alias in hierarchy[group][command]["aliases"]:
    ${"if" if 0 == i else "elif"} [[ ${'${group}'} == "${alias}" ]]; then
      group="${group}"
      command="${command}"
      have_to_complete_command=0
      <% i += 1 %>
    % endfor
  % endfor
% endfor
% if 0 < i:
    fi
% endif

    # If we need to complete command
    if [[ 1 == $have_to_complete_command ]]; then
% for i, (group, commands) in enumerate(hierarchy.items()):
        ${"if" if 0 == i else "elif"} [[ ${'${group}'} == "${group}" ]]; then
            COMPREPLY=( $( compgen -W "${' '.join(commands.keys())} ${'${top_level_flags}'}" -- ${'${cur}'} ) );
% endfor
% if hierarchy:
        fi
% endif
        return 0
    fi

    # We know the group and command, have complete the optional parameters.
    case "$group,$command,$cur,$prev" in
% for group in hierarchy:
  % for command in hierarchy[group]:
        "${group}","${command}",-*,*)
            COMPREPLY=( $( compgen -W "${' '.join(hierarchy[group][command]['flags'])}" -- ${'${cur}'} ) ); ;;
    % for flag, values in hierarchy[group][command]["parameters"].items():
        "${group}","${command}",*,"${flag}")
           COMPREPLY=( $( compgen -W "${' '.join(values)}" -- ${'${cur}'} ) ); ;;
    % endfor
  % endfor
% endfor
    esac
    return 0
}

complete -F _${tool.replace("-", "_")} ${tool}

# To enable tab-completion with this script, either execute
#   source <(${cli})  (temporarily)
# or
#   ${cli} >> ~/.bash_completion  (permanently)
# or store the output as a file inside the system bash_completion.d directory.
