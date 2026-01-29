"""Track models for MIDI and audio tracks.

Maps to OSC endpoints:
- song_create_midi_track / song_create_audio_track / song_delete_track / song_duplicate_track
- track_get_name / track_set_name
- track_get_volume / track_set_volume
- track_get_panning / track_set_panning
- track_get_mute / track_set_mute
- track_get_solo / track_set_solo
- track_get_arm / track_set_arm
- track_get_color / track_set_color / track_get_color_index / track_set_color_index
- track_get_send / track_set_send
- track_get_input_routing_type / track_set_input_routing_type
- track_get_input_routing_channel / track_set_input_routing_channel
- track_get_output_routing_type / track_set_output_routing_type
- track_get_output_routing_channel / track_set_output_routing_channel
- track_get_available_input_routing_types / track_get_available_output_routing_types
- track_get_available_input_routing_channels / track_get_available_output_routing_channels
- track_get_current_monitoring_state / track_set_current_monitoring_state
- track_get_is_foldable / track_get_is_grouped / track_get_is_visible
- track_get_can_be_armed / track_get_has_midi_input / track_get_has_midi_output
- track_get_has_audio_input / track_get_has_audio_output
- track_get_fold_state / track_set_fold_state
- track_stop_all_clips
"""

from typing import Optional, Literal, Annotated
from pydantic import BaseModel, Field

from .devices import Device
from .clips import MidiClip, AudioClip


# Track types
TrackType = Literal["midi", "audio"]

# Monitoring states (0=In, 1=Auto, 2=Off)
MonitoringState = Literal["in", "auto", "off"]
MONITORING_STATE_TO_INT = {"in": 0, "auto": 1, "off": 2}


class TrackMix(BaseModel):
    """Mix settings for a track.

    Contains volume, pan, mute, solo settings.
    """

    volume: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.85,
        description="Track volume (0.0-1.0, where 0.85 is 0dB)"
    )
    pan: Annotated[float, Field(ge=-1.0, le=1.0)] = Field(
        default=0.0,
        description="Pan position (-1.0=left, 0.0=center, 1.0=right)"
    )
    mute: bool = Field(
        default=False,
        description="Whether track is muted"
    )
    solo: bool = Field(
        default=False,
        description="Whether track is soloed"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"volume": 0.85, "pan": 0.0},
                {"volume": 0.7, "pan": -0.3, "mute": False},
            ]
        }


class TrackRouting(BaseModel):
    """Routing configuration for a track.

    Specifies input and output routing.
    """

    input_type: Optional[str] = Field(
        default=None,
        description="Input routing type (e.g., 'Ext. In', 'No Input')"
    )
    input_channel: Optional[str] = Field(
        default=None,
        description="Input routing channel"
    )
    output_type: Optional[str] = Field(
        default=None,
        description="Output routing type (e.g., 'Master', 'Sends Only')"
    )
    output_channel: Optional[str] = Field(
        default=None,
        description="Output routing channel"
    )
    monitoring: MonitoringState = Field(
        default="auto",
        description="Monitoring state (in, auto, off)"
    )

    @property
    def monitoring_int(self) -> int:
        """Get monitoring state as integer for OSC."""
        return MONITORING_STATE_TO_INT[self.monitoring]


class TrackSends(BaseModel):
    """Send levels for a track.

    Maps send names to levels (0.0-1.0).
    Send names should match return track names.
    """

    levels: dict[str, Annotated[float, Field(ge=0.0, le=1.0)]] = Field(
        default_factory=dict,
        description="Send levels by return track name"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"levels": {"reverb": 0.3, "delay": 0.2}}
            ]
        }


class Track(BaseModel):
    """A track configuration (MIDI or audio).

    Contains all settings for a track including devices, clips, and mix.
    """

    name: str = Field(
        ...,
        description="Track name",
        min_length=1
    )
    type: TrackType = Field(
        default="midi",
        description="Track type (midi or audio)"
    )
    color_index: Optional[Annotated[int, Field(ge=0, le=69)]] = Field(
        default=None,
        description="Ableton color index (0-69)"
    )
    armed: bool = Field(
        default=False,
        description="Whether track is armed for recording"
    )

    # Devices on the track
    devices: list[Device] = Field(
        default_factory=list,
        description="Devices on this track (instrument + effects)"
    )

    # Clips by section name
    clips: dict[str, MidiClip | AudioClip] = Field(
        default_factory=dict,
        description="Clips keyed by section name"
    )

    # Mix settings
    mix: TrackMix = Field(
        default_factory=TrackMix,
        description="Volume, pan, mute, solo settings"
    )

    # Routing
    routing: TrackRouting = Field(
        default_factory=TrackRouting,
        description="Input/output routing configuration"
    )

    # Sends
    sends: TrackSends = Field(
        default_factory=TrackSends,
        description="Send levels to return tracks"
    )

    @property
    def instrument(self) -> Optional[Device]:
        """Get the first instrument device on this track."""
        for device in self.devices:
            if device.type in ("instrument", "drums"):
                return device
        return None

    @property
    def effects(self) -> list[Device]:
        """Get all audio effect devices on this track."""
        return [d for d in self.devices if d.type == "audio_effect"]

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "drums",
                    "type": "midi",
                    "devices": [{"name": "808 Core Kit", "type": "drums"}],
                    "clips": {
                        "intro": {
                            "length": 4,
                            "notes": [
                                {"pitch": 36, "start": 0, "duration": 0.5, "velocity": 100}
                            ]
                        }
                    },
                    "mix": {"volume": 0.85, "pan": 0.0}
                }
            ]
        }
