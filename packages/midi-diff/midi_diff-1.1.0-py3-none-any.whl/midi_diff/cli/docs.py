"""
Author: 
    Inspyre Softworks

Project:
    MIDIDiff

File: 
    midi_diff/cli/docs.py
 

Description:
    Documentation-related functionality for the MIDIDiff CLI.

"""
import webbrowser
from typing import Final


# Documentation URL
DOCUMENTATION_URL: Final[str] = "https://mididiff.readthedocs.io/en/latest/"


def open_documentation() -> None:
    """
    Open MIDIDiff documentation in the user's default web browser.
    
    Opens https://mididiff.readthedocs.io/en/latest/ in the system's
    default web browser. If the browser cannot be opened, prints a warning
    message with the URL so the user can manually navigate to it.
    """
    print(f"Opening documentation at {DOCUMENTATION_URL}")
    try:
        opened = webbrowser.open(DOCUMENTATION_URL)
    except Exception as e:
        print(f"Warning: Unable to open browser automatically: {e}")
        print(f"Please visit the documentation manually at: {DOCUMENTATION_URL}")
    else:
        if not opened:
            print(
                "Warning: Unable to open browser automatically "
                "(webbrowser.open() returned False)."
            )
            print(f"Please visit the documentation manually at: {DOCUMENTATION_URL}")


__all__ = ["open_documentation", "DOCUMENTATION_URL"]
