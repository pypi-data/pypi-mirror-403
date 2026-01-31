"""
Author:
    Inspyre Softworks

Project:
    MIDIDiff

File:
    midi_diff/cli/completions.py


Description:
    Shell completion script generation for the MIDIDiff CLI.

"""
from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Final, Iterable, Mapping

SUPPORTED_SHELLS: Final[frozenset[str]] = frozenset({"bash", "zsh", "fish", "powershell", "cmd"})
COMPLETION_FILENAMES: Final[dict[str, str]] = {
    "bash": "midi-diff",
    "zsh": "_midi-diff",
    "fish": "midi-diff.fish",
    "powershell": "midi-diff-completion.ps1",
    "cmd": "midi-diff-completion.cmd",
}


def emit_completion_script(
    shell: str,
    commands: Iterable[str],
    flags: Iterable[str],
    subcommand_flags: Mapping[str, Iterable[str]] | None = None,
) -> str:
    """
    Generate a shell completion script for the given shell.

    Parameters
    ----------
    shell:
        Target shell name (bash, zsh, fish, powershell, cmd).
    commands:
        Iterable of supported subcommands.
    flags:
        Iterable of supported top-level flags.
    subcommand_flags:
        Mapping of subcommand name to iterable of flags/options for that subcommand.

    Returns
    -------
    str
        The completion script content.
    """
    if shell not in SUPPORTED_SHELLS:
        supported = ", ".join(sorted(SUPPORTED_SHELLS))
        raise ValueError(f"Unsupported shell '{shell}'. Supported shells: {supported}")

    sub_flags = {name: tuple(sorted(values)) for name, values in (subcommand_flags or {}).items()}

    commands_list = " ".join(sorted(commands))
    flags_list = " ".join(sorted(flags))
    commands_ps_array = "@(\"" + "\", \"".join(sorted(commands)) + "\")"
    flags_ps_array = "@(\"" + "\", \"".join(sorted(flags)) + "\")"
    shells_list = " ".join(sorted(SUPPORTED_SHELLS))
    shells_ps_array = "@(\"" + "\", \"".join(sorted(SUPPORTED_SHELLS)) + "\")"
    def _shell_flags(name: str) -> str:
        return " ".join(sub_flags.get(name, ()))
    def _ps_flags(name: str) -> str:
        return "@(\"" + "\", \"".join(sub_flags.get(name, ())) + "\")"

    if shell == "bash":
        return f"""# Bash completion for midi-diff
_midi_diff_completions() {{
    local cur prev
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=($(compgen -W "{commands_list}" -- "$cur"))
        return 0
    fi

    case "${{COMP_WORDS[1]}}" in
        diff)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "{_shell_flags("diff")}" -- "$cur"))
            elif [[ $COMP_CWORD -le 4 ]]; then
                COMPREPLY=($(compgen -f -- "$cur"))
            fi
            ;;
        upgrade)
            COMPREPLY=($(compgen -W "{_shell_flags("upgrade")}" -- "$cur"))
            ;;
        completion)
            COMPREPLY=($(compgen -W "{shells_list} {_shell_flags("completion")}" -- "$cur"))
            ;;
        install-completions)
            COMPREPLY=($(compgen -W "{_shell_flags("install-completions")}" -- "$cur"))
            ;;
        *)
            COMPREPLY=($(compgen -W "{flags_list}" -- "$cur"))
            ;;
    esac
}}
complete -F _midi_diff_completions midi-diff
"""

    if shell == "zsh":
        return f"""#compdef midi-diff

_midi_diff() {{
    local -a commands
    commands=({commands_list})

    _arguments \\
        "1: :->command" \\
        "*::arg:->args"

    case $state in
        command)
            _values 'midi-diff commands' $commands
            ;;
        args)
            case $words[2] in
                diff)
                    if [[ $words[CURRENT] == -* ]]; then
                        _values 'diff options' {_shell_flags("diff")}
                    else
                        _arguments "2:First MIDI file:_files" "3:Second MIDI file:_files" "4:Output MIDI file:_files"
                    fi
                    ;;
                upgrade)
                    _values 'upgrade options' {_shell_flags("upgrade")}
                    ;;
                completion)
                    _values 'shell' {shells_list} {_shell_flags("completion")}
                    ;;
                install-completions)
                    _values 'options' {_shell_flags("install-completions")}
                    ;;
                *)
                    _values 'flags' {flags_list}
                    ;;
            esac
            ;;
    esac
}}

_midi_diff "$@"
"""

    if shell == "fish":
        return f"""# Fish completion for midi-diff
complete -c midi-diff -n "not __fish_seen_subcommand_from {commands_list}" -s V -l version -d "Show version and environment info"
complete -c midi-diff -n "not __fish_seen_subcommand_from {commands_list}" -s h -l help -d "Show help"

complete -c midi-diff -n "__fish_use_subcommand" -a "{commands_list}" -d "midi-diff commands"

complete -c midi-diff -n "__fish_seen_subcommand_from diff" -a "(__fish_complete_path)" -d "MIDI file path"
complete -c midi-diff -n "__fish_seen_subcommand_from diff" -s h -l help -d "Show help"
complete -c midi-diff -n "__fish_seen_subcommand_from upgrade" -l pre -d "Include pre-release versions"
complete -c midi-diff -n "__fish_seen_subcommand_from upgrade" -s h -l help -d "Show help"
complete -c midi-diff -n "__fish_seen_subcommand_from completion" -a "{shells_list}" -d "Target shell"
complete -c midi-diff -n "__fish_seen_subcommand_from completion" -s h -l help -d "Show help"
complete -c midi-diff -n "__fish_seen_subcommand_from install-completions" -l shell -a "{shells_list}" -d "Override detected shell"
complete -c midi-diff -n "__fish_seen_subcommand_from install-completions" -s h -l help -d "Show help"
complete -c midi-diff -n "__fish_seen_subcommand_from debug-info" -s h -l help -d "Show help"
complete -c midi-diff -n "__fish_seen_subcommand_from check-updates" -s h -l help -d "Show help"
complete -c midi-diff -n "__fish_seen_subcommand_from docs" -s h -l help -d "Show help"
"""

    if shell == "powershell":
        return f"""# PowerShell completion for midi-diff
using namespace System.Management.Automation

Register-ArgumentCompleter -Native -CommandName midi-diff -ScriptBlock {{
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    $commands = {commands_ps_array}
    $flags = {flags_ps_array}
    $shells = {shells_ps_array}

    # if first token after command
    if ($commandAst.CommandElements.Count -le 2) {{
        foreach ($cmd in $commands) {{
            if ($cmd -like "$wordToComplete*") {{
                [CompletionResult]::new($cmd, $cmd, 'ParameterValue', 'command')
            }}
        }}
        return
    }}

    $subcommand = $commandAst.CommandElements[1].Extent.Text

    switch ($subcommand) {{
        "diff" {{
            foreach ($opt in {_ps_flags("diff")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
            [CompletionResult]::new($wordToComplete, $wordToComplete, 'ParameterValue', 'file path')
        }}
        "upgrade" {{
            foreach ($opt in {_ps_flags("upgrade")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
        }}
        "completion" {{
            foreach ($s in $shells) {{
                if ($s -like "$wordToComplete*") {{
                    [CompletionResult]::new($s, $s, 'ParameterValue', 'shell')
                }}
            }}
            foreach ($opt in {_ps_flags("completion")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
        }}
        "install-completions" {{
            foreach ($opt in {_ps_flags("install-completions")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
        }}
        "debug-info" {{
            foreach ($opt in {_ps_flags("debug-info")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
        }}
        "check-updates" {{
            foreach ($opt in {_ps_flags("check-updates")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
        }}
        "docs" {{
            foreach ($opt in {_ps_flags("docs")}) {{
                if ($opt -like "$wordToComplete*") {{
                    [CompletionResult]::new($opt, $opt, 'ParameterValue', 'option')
                }}
            }}
        }}
        default {{
            foreach ($flag in $flags) {{
                if ($flag -like "$wordToComplete*") {{
                    [CompletionResult]::new($flag, $flag, 'ParameterValue', 'flag')
                }}
            }}
        }}
    }}
}}
"""

    # cmd (simple usage hint)
    return (
        "@echo off\n"
        "rem Command prompt does not support rich completions by default.\n"
        "rem Use 'doskey' macros as a minimal helper:\n"
        "doskey midi-diff=midi-diff $*\n"
    )


def detect_shell() -> str | None:
    """Best-effort detection of the current shell."""
    shell_env = os.environ.get("SHELL")
    if shell_env:
        name = Path(shell_env).name.lower()
        if name in SUPPORTED_SHELLS:
            return name
        if "powershell" in name or "pwsh" in name:
            return "powershell"
        if name.endswith("cmd.exe"):
            return "cmd"

    if os.environ.get("POWERSHELL_DISTRIBUTION_CHANNEL") or os.environ.get("PSModulePath"):
        return "powershell"

    comspec = os.environ.get("COMSPEC", "").lower()
    if comspec.endswith("cmd.exe"):
        return "cmd"

    return None


def _default_install_path(shell: str) -> Path:
    env_override = os.environ.get("MIDI_DIFF_COMPLETIONS_DIR")
    base_dir = Path(env_override) if env_override else Path.home()

    if shell == "bash":
        return base_dir / ".local" / "share" / "bash-completion" / "completions" / COMPLETION_FILENAMES[shell]
    if shell == "zsh":
        return base_dir / ".zsh" / "completions" / COMPLETION_FILENAMES[shell]
    if shell == "fish":
        return base_dir / ".config" / "fish" / "completions" / COMPLETION_FILENAMES[shell]
    if shell == "powershell":
        if platform.system().lower() == "windows":
            return base_dir / "Documents" / "PowerShell" / "Scripts" / COMPLETION_FILENAMES[shell]
        return base_dir / ".config" / "powershell" / "Scripts" / COMPLETION_FILENAMES[shell]
    if shell == "cmd":
        return Path(os.environ.get("USERPROFILE", base_dir)) / COMPLETION_FILENAMES[shell]
    raise ValueError(f"Unsupported shell '{shell}'")


def install_completions(
    shell: str | None,
    commands: Iterable[str],
    flags: Iterable[str],
    subcommand_flags: Mapping[str, Iterable[str]] | None = None,
) -> Path:
    """
    Detect the current shell (or use the provided one), generate the completion script,
    and install it to a default location for that shell.
    """
    target_shell = shell or detect_shell()
    if target_shell is None:
        raise RuntimeError("Unable to detect current shell. Please specify --shell.")
    if target_shell not in SUPPORTED_SHELLS:
        supported = ", ".join(sorted(SUPPORTED_SHELLS))
        raise ValueError(f"Unsupported shell '{target_shell}'. Supported shells: {supported}")

    script = emit_completion_script(target_shell, commands, flags, subcommand_flags)
    path = _default_install_path(target_shell)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8")
    return path


__all__ = ["emit_completion_script", "SUPPORTED_SHELLS", "install_completions", "detect_shell"]
