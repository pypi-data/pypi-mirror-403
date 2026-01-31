# MIDIDiff

[![PyPI version](https://badge.fury.io/py/midi-diff.svg)](https://badge.fury.io/py/midi-diff)
[![Python Versions](https://img.shields.io/pypi/pyversions/midi-diff.svg)](https://pypi.org/project/midi-diff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/tayjaybabee/MIDIDiff/actions/workflows/test.yml/badge.svg)](https://github.com/tayjaybabee/MIDIDiff/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/mididiff/badge/?version=latest)](https://mididiff.readthedocs.io/en/latest/?badge=latest)

MIDIDiff compares two MIDI files and produces a third MIDI file containing the
notes that are present in only one of the inputs. Notes are matched by pitch,
start tick, and duration; velocity differences are ignored.

## Documentation

Full documentation is available at [Read the Docs](https://MIDIDiff.readthedocs.io/) (once published).

To build the documentation locally:

```shell
cd docs
poetry run sphinx-build -b html . _build/html
```

## Requirements

- Python 3.11+
- `mido` (installed automatically via the project dependencies)
- `rich` (optional, for enhanced CLI output)

## Installation

### For Development (Editable Install)

If you're contributing to MIDIDiff or testing changes, install in editable mode:

**Recommended:**
```shell
poetry install --extras cli
```

Poetry installs the package in editable mode by default, so changes to the source code are immediately reflected.

**Alternative (using pip):**
```shell
pip install -e ".[cli]"
```

The `-e` flag creates an editable install, allowing you to modify the code without reinstalling.

For more details, see the [Testing Guide](https://MIDIDiff.readthedocs.io/en/latest/testing.html).

### Build and install locally

```shell
poetry build
pip install dist/*.whl
```

For CLI functionality with rich formatting, install with CLI extras:

```shell
pip install dist/midi_diff-*.whl[cli]
```

Or install directly from the package:

```shell
pip install "midi-diff[cli]"
```

### Core library only (no CLI dependencies)

If you only need the core library without CLI dependencies (e.g., for programmatic use), install without extras:

```shell
pip install midi-diff
```

## Usage

### Command-line interface

The CLI expects two input MIDI files and an output path for the diff:

```shell
midi-diff fileA.mid fileB.mid diff.mid
```

You can also run the module directly:

```shell
python -m midi_diff.cli diff fileA.mid fileB.mid diff.mid
```

### Output behavior

- If the output file already exists, MIDIDiff will append an incrementing suffix
  (for example, `diff_1.mid`) to avoid overwriting.
- The resulting MIDI file contains only notes that are present in one input but
  not the other.

### Version and environment info

Use `-V` or `--version` to print the installed MIDIDiff version, environment
details, and the result of an update check against PyPI:

```shell
midi-diff --version
```

### Debug information

Use the `debug-info` subcommand to display comprehensive diagnostic information:

```shell
midi-diff debug-info
```

### Shell completions

Generate shell completion scripts for enhanced command-line experience:

```shell
midi-diff completion bash        # Bash
midi-diff completion zsh         # Zsh
midi-diff completion fish        # Fish
midi-diff completion powershell  # PowerShell
midi-diff completion cmd         # Command Prompt (prints doskey helper)
midi-diff install-completions    # Install for detected shell (use --shell to override)
MIDI_DIFF_COMPLETIONS_DIR=~/.my-completions midi-diff install-completions  # Custom base dir
```

**Installation:** For detailed instructions on installing and configuring shell completions for your specific shell, see the [Shell Completions Guide](https://MIDIDiff.readthedocs.io/en/latest/shell-completions.html) in the documentation.

### Programmatic usage

You can also use MIDIDiff as a library in your Python code:

```python
from midi_diff.core import main

# Compare two MIDI files and save the diff
main('fileA.mid', 'fileB.mid', 'diff.mid')
```

Or work with the lower-level API:

```python
import mido
from midi_diff.midi_utils import extract_notes, notes_to_midi

# Load MIDI files
mid_a = mido.MidiFile('fileA.mid')
mid_b = mido.MidiFile('fileB.mid')

# Extract notes
notes_a = set(extract_notes(mid_a))
notes_b = set(extract_notes(mid_b))

# Compute diff
diff_notes = notes_a.symmetric_difference(notes_b)

# Create output MIDI
diff_mid = notes_to_midi(list(diff_notes), ticks_per_beat=mid_a.ticks_per_beat)
diff_mid.save('diff.mid')
```

## Architecture

### CLI Sub-package (v1.0.0+)

Starting with version 1.0.0, the CLI has been separated into its own sub-package (`midi_diff.cli`)
to improve separation of concerns and allow the core library to be used without CLI dependencies.

- **Core library** (`midi_diff`): Contains note extraction, diff logic, and data models. Has minimal dependencies (`mido` only).
- **CLI sub-package** (`midi_diff.cli`): Contains argument parsing, version reporting, debug info, and environment checks. Requires `rich` for enhanced output.

**Migration note:** If you were importing from `midi_diff.cli` in your code, this continues to work through a backward compatibility shim that will be maintained through the 1.x release series.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- How to contribute code and documentation
- Changelog update requirements
- Development setup
- Pull request process

All contributions with user-facing changes must update the [CHANGELOG.md](CHANGELOG.md) file.

## How note matching works

Notes are considered identical when they share the same:

- Pitch
- Start tick
- Duration

Velocity is intentionally ignored so that the diff focuses on musical placement.

## API Stability (v1.0.0+)

Starting with version 1.0.0, the following API surface is considered stable and will follow semantic versioning:

- **Core functions**: `midi_diff.core.main()`
- **Data models**: `midi_diff.midi_utils.NoteEvent`
- **Utility functions**: `midi_diff.midi_utils.extract_notes()`, `midi_diff.midi_utils.notes_to_midi()`
- **CLI entry point**: `midi-diff` command and `midi_diff.cli:cli` function

Breaking changes to these APIs will result in a major version bump (2.0.0, etc.).
