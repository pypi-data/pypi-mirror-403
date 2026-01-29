"""Mixing models for return tracks and master.

Maps to OSC endpoints:
- song_create_return_track / song_delete_return_track

Return track operations use regular track tools with special indexing.
Master track is accessed via the song's master_track property.

Note: Return tracks and master track use the same device/mix APIs
as regular tracks, just with different addressing.
"""

from typing import Optional, Annotated
from pydantic import BaseModel, Field

from .devices import Device
from .tracks import TrackMix


class ReturnTrack(BaseModel):
    """A return (aux/bus) track configuration.

    Return tracks are used for shared effects (reverb, delay, etc.)
    that multiple tracks send to.
    """

    name: str = Field(
        ...,
        description="Return track name (e.g., 'reverb', 'delay')",
        min_length=1
    )
    color_index: Optional[Annotated[int, Field(ge=0, le=69)]] = Field(
        default=None,
        description="Ableton color index (0-69)"
    )

    # Devices on the return track (typically effects)
    devices: list[Device] = Field(
        default_factory=list,
        description="Effect devices on this return track"
    )

    # Mix settings for the return track itself
    mix: TrackMix = Field(
        default_factory=TrackMix,
        description="Return track mix settings"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "reverb",
                    "devices": [
                        {
                            "name": "Reverb",
                            "type": "audio_effect",
                            "parameters": [
                                {"name": "Dry/Wet", "value": 1.0},
                                {"name": "Decay Time", "value": 3.0}
                            ]
                        }
                    ],
                    "mix": {"volume": 0.85}
                },
                {
                    "name": "delay",
                    "devices": [
                        {
                            "name": "Delay",
                            "type": "audio_effect",
                            "parameters": [
                                {"name": "Dry/Wet", "value": 1.0}
                            ]
                        }
                    ],
                    "mix": {"volume": 0.7}
                }
            ]
        }


class MasterTrack(BaseModel):
    """Master track configuration.

    The master track receives the mixed output from all tracks
    and applies final processing before output.
    """

    # Devices on the master track (mastering chain)
    devices: list[Device] = Field(
        default_factory=list,
        description="Mastering devices on the master track"
    )

    # Master volume (0.0-1.0, where 0.85 is 0dB)
    volume: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.85,
        description="Master volume (0.0-1.0, where 0.85 is 0dB)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "devices": [
                        {
                            "name": "EQ Eight",
                            "type": "audio_effect"
                        },
                        {
                            "name": "Glue Compressor",
                            "type": "audio_effect",
                            "parameters": [
                                {"name": "Threshold", "value": -10},
                                {"name": "Ratio", "value": 4}
                            ]
                        },
                        {
                            "name": "Limiter",
                            "type": "audio_effect"
                        }
                    ],
                    "volume": 0.85
                }
            ]
        }


class MixConfig(BaseModel):
    """Complete mixing configuration.

    Contains all return tracks and master track settings.
    """

    return_tracks: list[ReturnTrack] = Field(
        default_factory=list,
        description="Return/aux tracks for shared effects"
    )

    master: MasterTrack = Field(
        default_factory=MasterTrack,
        description="Master track configuration"
    )

    def get_return_track(self, name: str) -> Optional[ReturnTrack]:
        """Get a return track by name."""
        for rt in self.return_tracks:
            if rt.name == name:
                return rt
        return None

    def get_return_track_index(self, name: str) -> Optional[int]:
        """Get the index of a return track by name."""
        for i, rt in enumerate(self.return_tracks):
            if rt.name == name:
                return i
        return None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "return_tracks": [
                        {
                            "name": "reverb",
                            "devices": [{"name": "Reverb", "type": "audio_effect"}]
                        },
                        {
                            "name": "delay",
                            "devices": [{"name": "Delay", "type": "audio_effect"}]
                        }
                    ],
                    "master": {
                        "devices": [
                            {"name": "Glue Compressor", "type": "audio_effect"},
                            {"name": "Limiter", "type": "audio_effect"}
                        ],
                        "volume": 0.85
                    }
                }
            ]
        }
