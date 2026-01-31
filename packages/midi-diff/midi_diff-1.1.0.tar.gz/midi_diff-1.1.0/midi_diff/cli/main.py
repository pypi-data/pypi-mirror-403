"""
Author: 
    Inspyre Softworks

Project:
    MIDIDiff

File: 
    midi_diff/cli/main.py
 

Description:
    Main CLI logic and argument parsing for MIDIDiff.

"""
import argparse
import sys
from typing import Final, Sequence
from midi_diff.core import main as core_main
from midi_diff.cli.version import (
    print_version_info,
    print_debug_info,
    check_for_updates_command,
    upgrade_package,
    UPDATE_CHECK_ENV_VAR,
)
from midi_diff.cli.docs import open_documentation
from midi_diff.cli.completions import emit_completion_script, SUPPORTED_SHELLS, install_completions


# Subcommand names - single source of truth for CLI commands
# These are referenced by both build_parser() and backward compatibility logic
COMMAND_DIFF: Final[str] = 'diff'
COMMAND_DEBUG_INFO: Final[str] = 'debug-info'
COMMAND_CHECK_UPDATES: Final[str] = 'check-updates'
COMMAND_UPGRADE: Final[str] = 'upgrade'
COMMAND_DOCS: Final[str] = 'docs'
COMMAND_COMPLETION: Final[str] = 'completion'
COMMAND_INSTALL_COMPLETIONS: Final[str] = 'install-completions'

# Flag definitions - single source of truth for CLI flags
# These are referenced by both build_parser() and backward compatibility logic
FLAG_VERSION_SHORT: Final[str] = '-V'
FLAG_VERSION_LONG: Final[str] = '--version'
FLAG_HELP_SHORT: Final[str] = '-h'
FLAG_HELP_LONG: Final[str] = '--help'

# Known subcommands and flags for backward compatibility.
# These sets are derived from the constants above to ensure they stay
# synchronized with the parser configuration in build_parser().
KNOWN_COMMANDS: Final[frozenset[str]] = frozenset({COMMAND_DIFF, COMMAND_DEBUG_INFO, COMMAND_CHECK_UPDATES, COMMAND_UPGRADE, COMMAND_DOCS, COMMAND_COMPLETION, COMMAND_INSTALL_COMPLETIONS})
KNOWN_FLAGS: Final[frozenset[str]] = frozenset({FLAG_VERSION_SHORT, FLAG_VERSION_LONG, FLAG_HELP_SHORT, FLAG_HELP_LONG})
SUBCOMMAND_FLAGS: Final[dict[str, tuple[str, ...]]] = {
    COMMAND_DIFF: ("--help", "-h"),
    COMMAND_UPGRADE: ("--pre", "--help", "-h"),
    COMMAND_COMPLETION: ("--help", "-h"),
    COMMAND_INSTALL_COMPLETIONS: ("--shell", "--help", "-h"),
    COMMAND_DEBUG_INFO: ("--help", "-h"),
    COMMAND_CHECK_UPDATES: ("--help", "-h"),
    COMMAND_DOCS: ("--help", "-h"),
}


class VersionAction(argparse.Action):
    """Custom argparse action to print version info and exit."""
    
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        print_version_info()
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser for MIDIDiff CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='midi-diff',
        description="MIDIDiff - Compare MIDI files and output their differences.",
    )
    parser.add_argument(
        FLAG_VERSION_SHORT,
        FLAG_VERSION_LONG,
        action=VersionAction,
        nargs=0,
        help=(
            f"Show version and environment info "
            f"(set {UPDATE_CHECK_ENV_VAR} to a truthy value like '1', 'true', or 'yes' to check for updates)."
        ),
    )
    
    # Create subparsers for subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
    )
    
    # diff subcommand (main functionality)
    diff_parser = subparsers.add_parser(
        COMMAND_DIFF,
        help='Compare two MIDI files and output their differences'
    )
    diff_parser.add_argument("file_a", help="Path to the first MIDI file.")
    diff_parser.add_argument("file_b", help="Path to the second MIDI file.")
    diff_parser.add_argument("out_file", help="Path for the diff MIDI output.")
    
    # debug-info subcommand (no additional arguments needed)
    subparsers.add_parser(
        COMMAND_DEBUG_INFO,
        help='Display diagnostic and environment information'
    )
    
    # check-updates subcommand (explicitly check for updates)
    subparsers.add_parser(
        COMMAND_CHECK_UPDATES,
        help='Check for available updates from PyPI'
    )
    
    # upgrade subcommand (upgrade the package)
    upgrade_parser = subparsers.add_parser(
        COMMAND_UPGRADE,
        help='Upgrade midi-diff to the latest version from PyPI'
    )
    upgrade_parser.add_argument(
        '--pre',
        action='store_true',
        help='Include pre-release versions in the upgrade'
    )
    
    # docs subcommand (open documentation in browser)
    subparsers.add_parser(
        COMMAND_DOCS,
        help='Open MIDIDiff documentation in your default web browser'
    )

    completion_parser = subparsers.add_parser(
        COMMAND_COMPLETION,
        help='Generate shell completion script',
    )
    completion_parser.add_argument(
        "shell",
        choices=sorted(SUPPORTED_SHELLS),
        help="Shell to generate completion for (bash, zsh, fish, powershell, cmd)",
    )

    install_completions_parser = subparsers.add_parser(
        COMMAND_INSTALL_COMPLETIONS,
        help='Install shell completions for the current shell',
    )
    install_completions_parser.add_argument(
        "--shell",
        choices=sorted(SUPPORTED_SHELLS),
        help="Override detected shell",
    )
    
    return parser


def run_cli(argv: Sequence[str] | None = None) -> None:
    """
    Main CLI entry point for MIDIDiff.

    Parameters:
        argv: Command-line arguments to parse. If None, defaults to sys.argv[1:].
              Accepts any sequence of strings (e.g., list, tuple) for testability.

    Usage:
        midi-diff fileA.mid fileB.mid output.mid  (assumes 'diff' subcommand)
        midi-diff diff fileA.mid fileB.mid output.mid
        midi-diff debug-info
        midi-diff --version

    """
    parser = build_parser()
    
    # Default to sys.argv[1:] if no argv provided
    if argv is None:
        argv = sys.argv[1:]
    
    # Combine known commands and flags for backward compatibility check
    known_subcommands_and_flags = KNOWN_COMMANDS | KNOWN_FLAGS
    
    # Backward compatibility: If first arg isn't a known subcommand/flag,
    # assume it's a file path and prepend 'diff' to make it work with the new structure.
    # Argparse will handle validation of the actual arguments.
    if len(argv) > 0 and argv[0] not in known_subcommands_and_flags:
        argv = [COMMAND_DIFF] + list(argv)
    
    args = parser.parse_args(argv)
    
    # Handle subcommands
    if args.command == COMMAND_DIFF:
        core_main(args.file_a, args.file_b, args.out_file)
    elif args.command == COMMAND_DEBUG_INFO:
        print_debug_info()
    elif args.command == COMMAND_CHECK_UPDATES:
        check_for_updates_command()
    elif args.command == COMMAND_UPGRADE:
        upgrade_package(include_pre=args.pre)
    elif args.command == COMMAND_DOCS:
        open_documentation()
    elif args.command == COMMAND_COMPLETION:
        script = emit_completion_script(
            args.shell,
            KNOWN_COMMANDS,
            KNOWN_FLAGS,
            SUBCOMMAND_FLAGS,
        )
        print(script)
    elif args.command == COMMAND_INSTALL_COMPLETIONS:
        path = install_completions(
            args.shell,
            KNOWN_COMMANDS,
            KNOWN_FLAGS,
            SUBCOMMAND_FLAGS,
        )
        print(f"Installed completions for '{path.name}' at: {path}")
    else:
        # No subcommand provided - show help
        parser.print_help()
        sys.exit(1)


__all__ = ["run_cli", "build_parser"]
