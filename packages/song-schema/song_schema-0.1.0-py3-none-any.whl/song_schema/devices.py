"""Device models for instruments, effects, and parameters.

Maps to OSC endpoints:
- track_insert_device
- track_delete_device
- track_get_device_names / track_get_device_types / track_get_devices_class_names
- track_get_num_devices
- device_get_name / device_get_class_name / device_get_type
- device_get_is_active / device_set_is_active / device_set_enabled
- device_get_num_parameters
- device_get_parameters / device_get_parameters_names / device_get_parameters_values
- device_get_parameter_value / device_set_parameter_value / device_set_parameter
- device_get_parameter_name / device_get_parameter_min / device_get_parameter_max
- device_get_parameter_value_string
- device_set_parameters_values
- device_get_parameters_mins / device_get_parameters_maxs / device_get_parameters_is_quantized
"""

from typing import Optional, Literal, Annotated, Any
from pydantic import BaseModel, Field


# Device types (0=audio_effect, 1=instrument, 2=midi_effect)
DeviceType = Literal["instrument", "audio_effect", "midi_effect", "drums"]
DEVICE_TYPE_TO_INT = {
    "audio_effect": 0,
    "instrument": 1,
    "midi_effect": 2,
    "drums": 1,  # Drums are loaded as instruments
}


class DeviceParameter(BaseModel):
    """A single device parameter.

    Used to specify non-default parameter values when configuring a device.
    """

    name: str = Field(
        ...,
        description="Parameter name (must match device parameter name)"
    )
    value: float = Field(
        ...,
        description="Parameter value (within device's min/max range)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"name": "Attack", "value": 0.1},
                {"name": "Decay", "value": 0.5},
                {"name": "Dry/Wet", "value": 0.4},
            ]
        }


class Device(BaseModel):
    """A device (instrument, effect, or drum kit) configuration.

    Specifies which device to load and any parameter overrides.
    Device names should match what's returned by browser_list_* tools.
    """

    name: str = Field(
        ...,
        description="Device name to load (fuzzy matched via browser search)",
        min_length=1
    )
    type: Optional[DeviceType] = Field(
        default=None,
        description="Device type hint for faster/more accurate loading"
    )
    enabled: bool = Field(
        default=True,
        description="Whether device is active (not bypassed)"
    )
    parameters: list[DeviceParameter] = Field(
        default_factory=list,
        description="Parameter values to set after loading"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "808 Core Kit",
                    "type": "drums"
                },
                {
                    "name": "Wavetable",
                    "type": "instrument",
                    "parameters": [
                        {"name": "Filter Freq", "value": 800},
                        {"name": "Filter Res", "value": 0.3}
                    ]
                },
                {
                    "name": "Reverb",
                    "type": "audio_effect",
                    "parameters": [
                        {"name": "Dry/Wet", "value": 0.3},
                        {"name": "Decay Time", "value": 2.5}
                    ]
                },
                {
                    "name": "Compressor",
                    "type": "audio_effect",
                    "enabled": True
                }
            ]
        }


class DeviceChain(BaseModel):
    """A chain of devices on a track.

    Devices are applied in order (first = closest to input).
    """

    devices: list[Device] = Field(
        default_factory=list,
        description="Ordered list of devices in the chain"
    )

    @property
    def instrument(self) -> Optional[Device]:
        """Get the first instrument in the chain (if any)."""
        for device in self.devices:
            if device.type in ("instrument", "drums"):
                return device
        return None

    @property
    def effects(self) -> list[Device]:
        """Get all audio effects in the chain."""
        return [d for d in self.devices if d.type == "audio_effect"]

    @property
    def midi_effects(self) -> list[Device]:
        """Get all MIDI effects in the chain."""
        return [d for d in self.devices if d.type == "midi_effect"]


# Common device presets for quick reference
COMMON_DRUM_KITS = [
    "808 Core Kit",
    "909 Core Kit",
    "707 Core Kit",
    "Golden Era Kit",
]

COMMON_INSTRUMENTS = [
    "Wavetable",
    "Analog",
    "Operator",
    "Drift",
    "Meld",
]

COMMON_AUDIO_EFFECTS = [
    "Reverb",
    "Compressor",
    "EQ Eight",
    "Delay",
    "Echo",
    "Saturator",
    "Glue Compressor",
]

COMMON_MIDI_EFFECTS = [
    "Arpeggiator",
    "Scale",
    "Chord",
    "Random",
    "Velocity",
]
