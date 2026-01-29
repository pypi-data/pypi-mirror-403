"""Main SongConfig model that combines all song elements.

This is the top-level model that represents a complete song configuration.
It can be serialized to JSON and used to drive automated song creation in Ableton.
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from .metadata import Metadata
from .structure import Structure, Section
from .tracks import Track
from .mixing import MixConfig, ReturnTrack, MasterTrack


class SongConfig(BaseModel):
    """Complete song configuration.

    This is the root model that defines everything needed to create
    a song in Ableton Live via the OSC API.
    """

    # Song metadata (tempo, key, time signature, etc.)
    metadata: Metadata = Field(
        default_factory=Metadata,
        description="Song metadata (tempo, key, scale, time signature)"
    )

    # Song structure (sections/scenes)
    structure: Structure = Field(
        default_factory=Structure,
        description="Song structure (sections that map to scenes)"
    )

    # Tracks by name
    tracks: dict[str, Track] = Field(
        default_factory=dict,
        description="Tracks keyed by track name"
    )

    # Mixing configuration (returns + master)
    mixing: MixConfig = Field(
        default_factory=MixConfig,
        description="Return tracks and master track configuration"
    )

    @model_validator(mode="after")
    def validate_clip_sections(self) -> "SongConfig":
        """Validate that clip section names match structure sections."""
        section_names = {s.name for s in self.structure.sections}

        for track_name, track in self.tracks.items():
            for clip_section in track.clips.keys():
                if clip_section not in section_names:
                    raise ValueError(
                        f"Track '{track_name}' has clip for section '{clip_section}' "
                        f"which is not in structure. Valid sections: {section_names}"
                    )

        return self

    @model_validator(mode="after")
    def validate_send_targets(self) -> "SongConfig":
        """Validate that send targets match return track names."""
        return_names = {rt.name for rt in self.mixing.return_tracks}

        for track_name, track in self.tracks.items():
            for send_target in track.sends.levels.keys():
                if send_target not in return_names:
                    raise ValueError(
                        f"Track '{track_name}' has send to '{send_target}' "
                        f"which is not a return track. Valid returns: {return_names}"
                    )

        return self

    @property
    def track_list(self) -> list[Track]:
        """Get tracks as an ordered list."""
        return list(self.tracks.values())

    @property
    def track_names(self) -> list[str]:
        """Get track names in order."""
        return list(self.tracks.keys())

    def get_track(self, name: str) -> Optional[Track]:
        """Get a track by name."""
        return self.tracks.get(name)

    def get_section(self, name: str) -> Optional[Section]:
        """Get a section by name."""
        return self.structure.get_section(name)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)

    def save(self, path: str | Path) -> None:
        """Save to JSON file."""
        path = Path(path)
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: str | Path) -> "SongConfig":
        """Load from JSON file."""
        path = Path(path)
        data = json.loads(path.read_text())
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> "SongConfig":
        """Parse from JSON string."""
        data = json.loads(json_str)
        return cls.model_validate(data)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "metadata": {
                        "tempo": 90,
                        "key": "F#",
                        "scale": "Minor",
                        "time_signature": {"numerator": 4, "denominator": 4}
                    },
                    "structure": {
                        "sections": [
                            {"name": "intro", "bars": 4},
                            {"name": "main", "bars": 8}
                        ]
                    },
                    "tracks": {
                        "drums": {
                            "name": "drums",
                            "type": "midi",
                            "devices": [{"name": "808 Core Kit", "type": "drums"}],
                            "clips": {
                                "intro": {"length": 4, "notes": []},
                                "main": {
                                    "length": 4,
                                    "notes": [
                                        {"pitch": 36, "start": 0, "duration": 0.5, "velocity": 100}
                                    ]
                                }
                            },
                            "mix": {"volume": 0.85},
                            "sends": {"levels": {"reverb": 0.2}}
                        }
                    },
                    "mixing": {
                        "return_tracks": [
                            {
                                "name": "reverb",
                                "devices": [{"name": "Reverb", "type": "audio_effect"}]
                            }
                        ],
                        "master": {
                            "devices": [{"name": "Limiter", "type": "audio_effect"}],
                            "volume": 0.85
                        }
                    }
                }
            ]
        }


def generate_json_schema() -> dict:
    """Generate JSON Schema for SongConfig."""
    return SongConfig.model_json_schema()
