"""Structure models for song arrangement.

Maps to OSC endpoints:
- song_create_scene / song_delete_scene / song_duplicate_scene
- scene_get_name / scene_set_name
- scene_get_tempo / scene_set_tempo / scene_get_tempo_enabled / scene_set_tempo_enabled
- scene_get_time_signature_* / scene_set_time_signature_*
- scene_get_color / scene_set_color / scene_get_color_index / scene_set_color_index
- scene_fire / scene_fire_as_selected / scene_fire_selected

Sections define the logical structure of the song (intro, verse, chorus, etc.)
and map to Ableton scenes.
"""

from typing import Optional, Annotated
from pydantic import BaseModel, Field


class SceneOverrides(BaseModel):
    """Optional overrides for scene-specific settings.

    Allows a section to have a different tempo or time signature
    than the global song settings.
    """

    tempo: Optional[Annotated[float, Field(ge=20, le=999)]] = Field(
        default=None,
        description="Override tempo for this scene (BPM)"
    )
    tempo_enabled: bool = Field(
        default=False,
        description="Whether scene tempo override is active"
    )
    time_signature_numerator: Optional[Annotated[int, Field(ge=1, le=99)]] = Field(
        default=None,
        description="Override time signature numerator"
    )
    time_signature_denominator: Optional[Annotated[int, Field(ge=1, le=16)]] = Field(
        default=None,
        description="Override time signature denominator"
    )
    time_signature_enabled: bool = Field(
        default=False,
        description="Whether scene time signature override is active"
    )


class Section(BaseModel):
    """A section of the song (maps to an Ableton scene).

    Each section represents a logical part of the song structure
    like intro, verse, chorus, bridge, outro, etc.
    """

    name: str = Field(
        ...,
        description="Section name (e.g., 'intro', 'verse', 'chorus')",
        min_length=1
    )
    bars: Annotated[int, Field(ge=1)] = Field(
        default=8,
        description="Length of this section in bars"
    )
    color_index: Optional[Annotated[int, Field(ge=0, le=69)]] = Field(
        default=None,
        description="Ableton color index (0-69)"
    )
    scene_overrides: Optional[SceneOverrides] = Field(
        default=None,
        description="Optional tempo/time signature overrides for this scene"
    )

    @property
    def beats(self) -> int:
        """Calculate section length in beats (assumes 4/4 time)."""
        return self.bars * 4

    class Config:
        json_schema_extra = {
            "examples": [
                {"name": "intro", "bars": 4},
                {"name": "verse", "bars": 8, "color_index": 15},
                {"name": "chorus", "bars": 8, "color_index": 20},
            ]
        }


class Structure(BaseModel):
    """Song structure definition.

    Defines the order and length of sections in the song.
    Each section maps to one Ableton scene.
    """

    sections: list[Section] = Field(
        default_factory=list,
        description="Ordered list of song sections",
        min_length=1
    )

    @property
    def total_bars(self) -> int:
        """Total song length in bars."""
        return sum(section.bars for section in self.sections)

    @property
    def total_beats(self) -> int:
        """Total song length in beats (assumes 4/4 time)."""
        return self.total_bars * 4

    def get_section(self, name: str) -> Optional[Section]:
        """Get a section by name."""
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def get_section_index(self, name: str) -> Optional[int]:
        """Get the index (scene index) of a section by name."""
        for i, section in enumerate(self.sections):
            if section.name == name:
                return i
        return None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "sections": [
                        {"name": "intro", "bars": 4},
                        {"name": "verse", "bars": 8},
                        {"name": "chorus", "bars": 8},
                        {"name": "verse", "bars": 8},
                        {"name": "chorus", "bars": 8},
                        {"name": "outro", "bars": 4},
                    ]
                }
            ]
        }
