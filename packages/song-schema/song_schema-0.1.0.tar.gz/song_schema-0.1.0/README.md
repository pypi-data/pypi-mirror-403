# Song Schema

Pydantic models for defining Ableton Live song configurations.

## Overview

This package provides a comprehensive schema for defining songs as JSON configurations that can be executed against Ableton Live via the OSC API.

## Installation

```bash
poetry install
```

## Usage

```python
from song_schema import SongConfig
from song_schema.validate import validate

# Load a song configuration
song = SongConfig.load("examples/lofi-beat.json")

# Validate it
result = validate(song)
print(result.summary())

# Access properties
print(f"Tempo: {song.metadata.tempo}")
print(f"Tracks: {list(song.tracks.keys())}")

# Save changes
song.save("my_song.json")
```

## Schema Structure

- **metadata**: Tempo, key, scale, time signature, groove, loop settings
- **structure**: Song sections (intro, verse, chorus, etc.) mapped to Ableton scenes
- **tracks**: MIDI/audio tracks with devices, clips, and mix settings
- **mixing**: Return tracks and master processing chain

## Examples

See the `examples/` directory:
- `minimal.json` - Simplest valid song configuration
- `lofi-beat.json` - A realistic lo-fi hip-hop beat
- `full-coverage.json` - Every field populated for reference

## Related Projects

- `ableton-mcp-server` - MCP server that exposes OSC tools to Claude
- `ableton-osc-client` - Python client for AbletonOSC
