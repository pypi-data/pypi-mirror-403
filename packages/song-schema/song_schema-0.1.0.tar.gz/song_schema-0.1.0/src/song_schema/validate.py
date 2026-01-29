"""Validation utilities for song configurations.

Provides completeness checking and recommendations for song configs.
"""

from dataclasses import dataclass, field
from .song import SongConfig
from .clips import MidiClip


@dataclass
class ValidationResult:
    """Result of validation with issues and recommendations."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.is_valid

    def summary(self) -> str:
        """Generate a summary string."""
        lines = []

        if self.is_valid:
            lines.append("✓ Song configuration is valid")
        else:
            lines.append("✗ Song configuration has errors")

        if self.errors:
            lines.append("\nErrors:")
            for e in self.errors:
                lines.append(f"  - {e}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        if self.recommendations:
            lines.append("\nRecommendations:")
            for r in self.recommendations:
                lines.append(f"  - {r}")

        return "\n".join(lines)


def validate_completeness(song: SongConfig) -> ValidationResult:
    """Check if a song configuration is complete and ready for production.

    Validates:
    - At least one track exists
    - Each track has at least one clip
    - Rhythm tracks have clips in all sections
    - Mix levels are explicitly set (not all defaults)
    - Return tracks exist for any sends

    Returns a ValidationResult with errors, warnings, and recommendations.
    """
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    # Check for tracks
    if not song.tracks:
        errors.append("No tracks defined")
    else:
        # Check each track
        for name, track in song.tracks.items():
            # Track must have at least one clip
            if not track.clips:
                errors.append(f"Track '{name}' has no clips")

            # MIDI tracks should have an instrument
            if track.type == "midi" and not track.instrument:
                warnings.append(f"MIDI track '{name}' has no instrument device")

            # Check for clips in all sections (for rhythm tracks)
            section_names = {s.name for s in song.structure.sections}
            clip_sections = set(track.clips.keys())
            missing_sections = section_names - clip_sections

            if missing_sections and name in ("drums", "bass", "percussion"):
                warnings.append(
                    f"Rhythm track '{name}' missing clips for sections: {missing_sections}"
                )

            # Check if mix is all defaults
            if (track.mix.volume == 0.85 and
                track.mix.pan == 0.0 and
                not track.mix.mute and
                not track.mix.solo):
                recommendations.append(
                    f"Track '{name}' has default mix settings - consider adjusting"
                )

    # Check structure
    if not song.structure.sections:
        errors.append("No sections defined in structure")

    # Check for return tracks if there are sends
    has_sends = any(
        track.sends.levels for track in song.tracks.values()
    )
    if has_sends and not song.mixing.return_tracks:
        errors.append("Tracks have sends but no return tracks defined")

    # Check return tracks have devices
    for rt in song.mixing.return_tracks:
        if not rt.devices:
            warnings.append(f"Return track '{rt.name}' has no devices")

    # Recommendations for common issues
    if not song.mixing.master.devices:
        recommendations.append(
            "Consider adding mastering devices to master track (EQ, compressor, limiter)"
        )

    # Check for reasonable tempo
    if song.metadata.tempo < 60:
        warnings.append(f"Tempo {song.metadata.tempo} BPM is very slow")
    elif song.metadata.tempo > 200:
        warnings.append(f"Tempo {song.metadata.tempo} BPM is very fast")

    # Check clips have notes
    for name, track in song.tracks.items():
        for section_name, clip in track.clips.items():
            if isinstance(clip, MidiClip) and not clip.notes:
                warnings.append(
                    f"Track '{name}' clip '{section_name}' has no notes"
                )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        recommendations=recommendations,
    )


def validate_osc_compatibility(song: SongConfig) -> ValidationResult:
    """Check if a song config is compatible with the OSC API.

    Validates that all device names, routing types, etc. are likely
    to work with the Ableton OSC API.
    """
    errors: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    # Known working device names
    known_drum_kits = {"808 Core Kit", "909 Core Kit", "707 Core Kit", "Golden Era Kit"}
    known_instruments = {"Wavetable", "Analog", "Operator", "Drift", "Meld"}
    known_effects = {"Reverb", "Compressor", "EQ Eight", "Delay", "Echo", "Saturator"}

    for name, track in song.tracks.items():
        for device in track.devices:
            if device.type == "drums":
                # Check if drum kit is known
                if device.name not in known_drum_kits:
                    warnings.append(
                        f"Drum kit '{device.name}' on track '{name}' may not be found. "
                        f"Known working: {known_drum_kits}"
                    )
            elif device.type == "instrument":
                if device.name not in known_instruments:
                    warnings.append(
                        f"Instrument '{device.name}' on track '{name}' may not be found. "
                        f"Known working: {known_instruments}"
                    )
            elif device.type == "audio_effect":
                if device.name not in known_effects:
                    warnings.append(
                        f"Effect '{device.name}' on track '{name}' may not be found. "
                        f"Known working: {known_effects}"
                    )

    # Check return track effects
    for rt in song.mixing.return_tracks:
        for device in rt.devices:
            if device.type == "audio_effect" and device.name not in known_effects:
                warnings.append(
                    f"Return track '{rt.name}' effect '{device.name}' may not be found"
                )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        recommendations=recommendations,
    )


def validate(song: SongConfig, check_osc: bool = True) -> ValidationResult:
    """Run all validations on a song config.

    Args:
        song: The song configuration to validate
        check_osc: Whether to check OSC API compatibility

    Returns:
        Combined ValidationResult
    """
    result = validate_completeness(song)

    if check_osc:
        osc_result = validate_osc_compatibility(song)
        result.errors.extend(osc_result.errors)
        result.warnings.extend(osc_result.warnings)
        result.recommendations.extend(osc_result.recommendations)
        result.is_valid = result.is_valid and osc_result.is_valid

    return result
