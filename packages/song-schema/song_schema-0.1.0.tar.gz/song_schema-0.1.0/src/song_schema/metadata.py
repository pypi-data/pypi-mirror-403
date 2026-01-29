"""Metadata models for song configuration.

Maps to OSC endpoints:
- song_get_tempo / song_set_tempo
- song_get_root_note / song_set_root_note
- song_get_scale_name / song_set_scale_name
- song_get_signature_numerator / song_set_signature_numerator
- song_get_signature_denominator / song_set_signature_denominator
- song_get_groove_amount / song_set_groove_amount
- song_get_loop / song_set_loop
- song_get_loop_start / song_set_loop_start
- song_get_loop_length / song_set_loop_length
"""

from typing import Literal, Annotated
from pydantic import BaseModel, Field


# Root note as MIDI note number (0-11, where 0=C, 1=C#, etc.)
RootNote = Literal["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Common scales supported by Ableton
ScaleName = Literal[
    "Major",
    "Minor",
    "Dorian",
    "Phrygian",
    "Lydian",
    "Mixolydian",
    "Locrian",
    "Harmonic Minor",
    "Melodic Minor",
    "Whole Tone",
    "Diminished",
    "Pentatonic Major",
    "Pentatonic Minor",
    "Blues",
    "Chromatic",
]

# Mapping from note name to MIDI number
ROOT_NOTE_TO_MIDI = {
    "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
    "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11
}


class LoopConfig(BaseModel):
    """Loop configuration for the song.

    Maps to:
    - song_get_loop / song_set_loop
    - song_get_loop_start / song_set_loop_start
    - song_get_loop_length / song_set_loop_length
    """

    enabled: bool = Field(
        default=True,
        description="Whether looping is enabled"
    )
    start: Annotated[float, Field(ge=0)] = Field(
        default=0.0,
        description="Loop start position in beats"
    )
    length: Annotated[float, Field(gt=0)] = Field(
        default=16.0,
        description="Loop length in beats"
    )


class TimeSignature(BaseModel):
    """Time signature configuration.

    Maps to:
    - song_get_signature_numerator / song_set_signature_numerator
    - song_get_signature_denominator / song_set_signature_denominator
    """

    numerator: Annotated[int, Field(ge=1, le=99)] = Field(
        default=4,
        description="Time signature numerator (beats per bar)"
    )
    denominator: Annotated[int, Field(ge=1, le=16)] = Field(
        default=4,
        description="Time signature denominator (beat unit, must be power of 2)"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Validate denominator is power of 2
        if self.denominator not in [1, 2, 4, 8, 16]:
            raise ValueError("Time signature denominator must be a power of 2 (1, 2, 4, 8, or 16)")


class Metadata(BaseModel):
    """Song metadata configuration.

    Contains all global song settings like tempo, key, time signature.
    """

    tempo: Annotated[float, Field(ge=20, le=999)] = Field(
        default=120.0,
        description="Song tempo in BPM (20-999)"
    )
    key: RootNote = Field(
        default="C",
        description="Root note of the song's key"
    )
    scale: ScaleName = Field(
        default="Minor",
        description="Scale/mode of the song"
    )
    time_signature: TimeSignature = Field(
        default_factory=TimeSignature,
        description="Time signature (numerator/denominator)"
    )
    groove_amount: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.0,
        description="Global groove amount (0.0-1.0)"
    )
    loop: LoopConfig = Field(
        default_factory=LoopConfig,
        description="Loop configuration"
    )

    @property
    def root_note_midi(self) -> int:
        """Get the root note as MIDI number (0-11)."""
        return ROOT_NOTE_TO_MIDI[self.key]

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "tempo": 90,
                    "key": "F#",
                    "scale": "Minor",
                    "time_signature": {"numerator": 4, "denominator": 4},
                    "groove_amount": 0.3,
                    "loop": {"enabled": True, "start": 0, "length": 32}
                }
            ]
        }
