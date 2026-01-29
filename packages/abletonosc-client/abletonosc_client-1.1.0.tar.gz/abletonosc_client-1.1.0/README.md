# abletonosc-client

Python OSC client wrapper for AbletonOSC - control Ableton Live via OSC.

## Installation

```bash
pip install abletonosc-client
```

## Requirements

- Python 3.11+
- Ableton Live with [AbletonOSC](https://github.com/ideoforms/AbletonOSC) installed

## Quick Start

```python
from abletonosc_client import connect, Song, Track

# Connect to Ableton Live
client = connect()

# Control the song
song = Song(client)
song.set_tempo(120.0)
song.start_playing()

# Work with tracks
track = Track(client)
track.set_name(0, "My Track")
track.set_volume(0, 0.8)
```

## Features

- **Application**: Version info, reload script, log level, status bar messages
- **Song**: Tempo, transport, time signature, tracks, scenes, loops, recording, quantization, cue points, key/scale
- **Track**: Volume, pan, mute, solo, arm, color, routing, monitoring, meters, device management, sends
- **Clip**: Notes (add/get/remove), properties (loop, warp, gain, pitch), launch/stop
- **ClipSlot**: Create/delete/duplicate clips, launch, stop
- **Device**: Parameters (get/set by index or name), enable/disable, device info
- **Scene**: Name, color, tempo, time signature, launch
- **View**: Track/scene/clip/device selection, view focus
- **Listeners**: Real-time callbacks for tempo, transport, loop, record, beat, song time, track properties

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed documentation.

## License

MIT
