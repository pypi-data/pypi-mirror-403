"""Song Schema - Pydantic models for Ableton Live song configurations."""

from .song import SongConfig
from .metadata import Metadata, LoopConfig
from .structure import Section, Structure
from .clips import Note, MidiClip, AudioClip, ClipConfig
from .devices import DeviceParameter, Device
from .tracks import TrackMix, TrackRouting, Track
from .mixing import ReturnTrack, MasterTrack

__all__ = [
    "SongConfig",
    "Metadata",
    "LoopConfig",
    "Section",
    "Structure",
    "Note",
    "MidiClip",
    "AudioClip",
    "ClipConfig",
    "DeviceParameter",
    "Device",
    "TrackMix",
    "TrackRouting",
    "Track",
    "ReturnTrack",
    "MasterTrack",
]

__version__ = "0.1.0"
