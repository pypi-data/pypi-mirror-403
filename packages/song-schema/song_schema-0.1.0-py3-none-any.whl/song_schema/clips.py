"""Clip models for MIDI and audio content.

Maps to OSC endpoints:
- clip_slot_create_clip / clip_slot_delete_clip / clip_slot_has_clip
- clip_get_name / clip_set_name
- clip_get_notes / clip_add_notes / clip_remove_notes
- clip_get_length / clip_get_is_midi_clip / clip_get_is_audio_clip
- clip_get_loop_start / clip_set_loop_start
- clip_get_loop_end / clip_set_loop_end
- clip_get_looping / clip_set_looping
- clip_get_color / clip_set_color / clip_get_color_index / clip_set_color_index
- clip_fire / clip_stop
- clip_get_muted / clip_set_muted
- clip_get_velocity_amount / clip_set_velocity_amount
- clip_get_legato / clip_set_legato
- clip_get_warping / clip_set_warping (audio)
- clip_get_warp_mode / clip_set_warp_mode (audio)
- clip_get_pitch_coarse / clip_set_pitch_coarse (audio)
- clip_get_pitch_fine / clip_set_pitch_fine (audio)
- clip_get_gain / clip_set_gain (audio)
"""

from typing import Optional, Literal, Union, Annotated
from pydantic import BaseModel, Field


class Note(BaseModel):
    """A single MIDI note.

    Maps to the note format used by clip_add_notes:
    - pitch: 0-127 (MIDI note number)
    - start_time: position in beats
    - duration: length in beats
    - velocity: 0-127
    """

    pitch: Annotated[int, Field(ge=0, le=127)] = Field(
        ...,
        description="MIDI note number (0-127, where 60=middle C)"
    )
    start: Annotated[float, Field(ge=0)] = Field(
        ...,
        description="Start time in beats"
    )
    duration: Annotated[float, Field(gt=0)] = Field(
        default=0.5,
        description="Duration in beats"
    )
    velocity: Annotated[int, Field(ge=0, le=127)] = Field(
        default=100,
        description="Note velocity (0-127)"
    )
    mute: bool = Field(
        default=False,
        description="Whether the note is muted"
    )

    def to_osc_dict(self) -> dict:
        """Convert to format expected by OSC clip_add_notes."""
        return {
            "pitch": self.pitch,
            "start_time": self.start,
            "duration": self.duration,
            "velocity": self.velocity,
        }

    class Config:
        json_schema_extra = {
            "examples": [
                {"pitch": 36, "start": 0, "duration": 0.5, "velocity": 100},
                {"pitch": 60, "start": 0, "duration": 1.0, "velocity": 80},
            ]
        }


class ClipLoopSettings(BaseModel):
    """Loop settings for a clip."""

    enabled: bool = Field(
        default=True,
        description="Whether looping is enabled"
    )
    start: Annotated[float, Field(ge=0)] = Field(
        default=0.0,
        description="Loop start position in beats"
    )
    end: Optional[float] = Field(
        default=None,
        description="Loop end position in beats (defaults to clip length)"
    )


class MidiClip(BaseModel):
    """A MIDI clip containing notes.

    Maps to MIDI clip operations in OSC.
    """

    name: Optional[str] = Field(
        default=None,
        description="Clip name"
    )
    length: Annotated[float, Field(gt=0)] = Field(
        default=4.0,
        description="Clip length in beats"
    )
    notes: list[Note] = Field(
        default_factory=list,
        description="MIDI notes in the clip"
    )
    loop: ClipLoopSettings = Field(
        default_factory=ClipLoopSettings,
        description="Loop settings"
    )
    color_index: Optional[Annotated[int, Field(ge=0, le=69)]] = Field(
        default=None,
        description="Ableton color index (0-69)"
    )
    muted: bool = Field(
        default=False,
        description="Whether the clip is muted"
    )
    velocity_amount: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=1.0,
        description="Velocity amount scaling (0.0-1.0)"
    )
    legato: bool = Field(
        default=False,
        description="Whether legato mode is enabled"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "length": 4,
                    "notes": [
                        {"pitch": 36, "start": 0, "duration": 0.5, "velocity": 100},
                        {"pitch": 38, "start": 1, "duration": 0.5, "velocity": 90},
                        {"pitch": 36, "start": 2, "duration": 0.5, "velocity": 95},
                        {"pitch": 38, "start": 3, "duration": 0.5, "velocity": 85},
                    ]
                }
            ]
        }


# Warp modes for audio clips
WarpMode = Literal["beats", "tones", "texture", "re-pitch", "complex", "complex_pro"]
WARP_MODE_TO_INT = {
    "beats": 0,
    "tones": 1,
    "texture": 2,
    "re-pitch": 3,
    "complex": 4,
    "complex_pro": 5,
}


class AudioClip(BaseModel):
    """An audio clip referencing an audio file.

    Maps to audio clip operations in OSC.
    Note: The audio file must already exist in the project.
    """

    name: Optional[str] = Field(
        default=None,
        description="Clip name"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Path to audio file (for reference, file must exist)"
    )
    loop: ClipLoopSettings = Field(
        default_factory=ClipLoopSettings,
        description="Loop settings"
    )
    color_index: Optional[Annotated[int, Field(ge=0, le=69)]] = Field(
        default=None,
        description="Ableton color index (0-69)"
    )
    muted: bool = Field(
        default=False,
        description="Whether the clip is muted"
    )
    warping: bool = Field(
        default=True,
        description="Whether warping is enabled"
    )
    warp_mode: WarpMode = Field(
        default="beats",
        description="Warp algorithm"
    )
    pitch_coarse: Annotated[int, Field(ge=-48, le=48)] = Field(
        default=0,
        description="Coarse pitch adjustment in semitones"
    )
    pitch_fine: Annotated[float, Field(ge=-50, le=50)] = Field(
        default=0.0,
        description="Fine pitch adjustment in cents"
    )
    gain: Annotated[float, Field(ge=0.0)] = Field(
        default=1.0,
        description="Clip gain (1.0 = unity)"
    )

    @property
    def warp_mode_int(self) -> int:
        """Get warp mode as integer for OSC."""
        return WARP_MODE_TO_INT[self.warp_mode]


# Union type for either MIDI or audio clip
ClipConfig = Union[MidiClip, AudioClip]


def is_midi_clip(clip: ClipConfig) -> bool:
    """Check if a clip config is a MIDI clip."""
    return isinstance(clip, MidiClip)


def is_audio_clip(clip: ClipConfig) -> bool:
    """Check if a clip config is an audio clip."""
    return isinstance(clip, AudioClip)
