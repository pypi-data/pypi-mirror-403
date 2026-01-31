"""
Author: 
    Inspyre Softworks

Project:
    MIDIDiff

File: 
    midi_diff/cli/__init__.py
 

Description:
    CLI sub-package for MIDIDiff, providing command-line interface functionality.
    
    This package contains the CLI entry point and related utilities, separated from
    the core library to allow the core to be used independently without CLI dependencies.

"""
from midi_diff.cli.main import run_cli


def cli() -> None:
    """
    Main entry point for the midi-diff command-line tool.
    
    This function is called when the `midi-diff` command is executed.
    """
    run_cli()


__all__ = ["cli"]
