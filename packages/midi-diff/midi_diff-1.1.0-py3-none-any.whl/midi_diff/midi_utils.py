"""
Author:
    Inspyre Softworks

Project:
    MIDIDiff

File:
    midi_diff/midi_utils.py

Description:
    Utilities for parsing MIDI files into NoteEvent objects and constructing MIDI files
    from NoteEvent sequences.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import mido


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """
    Immutable representation of a MIDI note event.

    Stores pitch, start tick, duration (ticks), and velocity. Values are validated on
    construction to ensure they are within MIDI/logical bounds.
    """

    pitch: int
    start: int
    duration: int
    velocity: int

    PITCH_MIN: int = 0
    PITCH_MAX: int = 127
    VELOCITY_MIN: int = 0
    VELOCITY_MAX: int = 127

    def __post_init__(self) -> None:
        """
        Validates fields after dataclass initialization.

        Raises:
            TypeError:
                If any field is not an int.

            ValueError:
                If any field is out of bounds.
        """
        self._validate_int('pitch', self.pitch, self.PITCH_MIN, self.PITCH_MAX)
        self._validate_int('start', self.start, 0, None)
        self._validate_int('duration', self.duration, 1, None)
        self._validate_int('velocity', self.velocity, self.VELOCITY_MIN, self.VELOCITY_MAX)

    @staticmethod
    def _validate_int(name: str, value: int, min_value: int | None, max_value: int | None) -> None:
        """
        Validates that a value is an integer and within optional bounds.

        Parameters:
            name (str):
                Field name (for error messages).

            value (int):
                Value to validate.

            min_value (int | None):
                Minimum allowed value, or None for no minimum.

            max_value (int | None):
                Maximum allowed value, or None for no maximum.

        Raises:
            TypeError:
                If the value is not an integer.

            ValueError:
                If the value is outside the specified bounds.
        """
        if not isinstance(value, int):
            raise TypeError(f'{name} must be int, got {type(value).__name__}')

        if min_value is not None and value < min_value:
            raise ValueError(f'{name} must be >= {min_value}, got {value}')

        if max_value is not None and value > max_value:
            raise ValueError(f'{name} must be <= {max_value}, got {value}')

    def identity_key(self) -> tuple[int, int, int]:
        """
        Returns the identity tuple used for diff-style comparisons.

        By design, velocity is excluded so notes match by musical placement rather than loudness.

        Returns:
            tuple[int, int, int]:
                (pitch, start, duration)
        """
        return self.pitch, self.start, self.duration


def extract_notes(mid: mido.MidiFile) -> list[NoteEvent]:
    """
    Parse a MIDI file into NoteEvent objects.

    Notes are collected across all tracks, then sorted by start tick for stable ordering.

    Parameters:
        mid (mido.MidiFile):
            MIDI file to parse.

    Returns:
        list[NoteEvent]:
            Note events extracted from the MIDI file.
    """
    notes: list[NoteEvent] = []

    for track in mid.tracks:
        # pitch -> stack of (start_tick, velocity). Stack supports overlapping same-pitch notes.
        ongoing: dict[int, list[tuple[int, int]]] = {}
        tick = 0

        for msg in track:
            tick += int(msg.time)

            if msg.type == 'note_on' and msg.velocity > 0:
                ongoing.setdefault(msg.note, []).append((tick, int(msg.velocity)))
                continue

            is_note_off = (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0)
            if not is_note_off:
                continue

            stack = ongoing.get(msg.note)
            if not stack:
                continue

            start, vel = stack.pop()
            if not stack:
                ongoing.pop(msg.note, None)

            duration = tick - start
            if duration <= 0:
                # Defensive: ignore pathological/invalid durations rather than create broken notes.
                continue

            notes.append(NoteEvent(pitch=int(msg.note), start=start, duration=duration, velocity=vel))

    notes.sort(key=lambda n: n.start)
    return notes


def notes_to_midi(notes: Iterable[NoteEvent], ticks_per_beat: int = 480) -> mido.MidiFile:
    """
    Construct a minimal MIDI file containing the given notes.

    Parameters:
        notes (Iterable[NoteEvent]):
            Notes to encode.

        ticks_per_beat (int):
            Resolution of the generated MIDI file.

    Returns:
        mido.MidiFile:
            A MIDI file containing the specified notes on a single track.
    """
    mid = mido.MidiFile(ticks_per_beat=int(ticks_per_beat))
    track = mido.MidiTrack()
    mid.tracks.append(track)

    events = _note_events_to_messages(notes)

    last_tick = 0
    for tick, msg in events:
        delta = tick - last_tick
        msg.time = int(delta)
        track.append(msg)
        last_tick = tick

    track.append(mido.MetaMessage('end_of_track', time=0))
    return mid


def _note_events_to_messages(notes: Iterable[NoteEvent]) -> list[tuple[int, mido.Message]]:
    """
    Convert NoteEvent objects into absolute-tick MIDI messages.

    Events are sorted by tick. For identical ticks, note_off is emitted before note_on.

    Parameters:
        notes (Iterable[NoteEvent]):
            Notes to convert.

    Returns:
        list[tuple[int, mido.Message]]:
            List of (absolute_tick, message) tuples in playback order.
    """
    events: list[tuple[int, int, mido.Message]] = []

    for note in notes:
        on_tick = int(note.start)
        off_tick = int(note.start + note.duration)

        events.extend(
            (
                (
                    on_tick,
                    1,
                    mido.Message(
                        'note_on', note=note.pitch, velocity=note.velocity
                    ),
                ),
                (
                    off_tick,
                    0,
                    mido.Message('note_off', note=note.pitch, velocity=0),
                ),
            )
        )
    events.sort(key=lambda e: (e[0], e[1]))
    return [(tick, msg) for tick, _, msg in events]


__all__ = ['NoteEvent', 'extract_notes', 'notes_to_midi']
