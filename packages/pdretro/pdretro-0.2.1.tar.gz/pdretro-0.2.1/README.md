# pdretro

## Python Libretro Wrapper

**Headless RetroArch emulation with a clean Python API for frame-by-frame control, audio capture, memory access, and seamless game swapping**

[![Python](https://img.shields.io/pypi/pyversions/pdretro?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/pdretro/)
[![License](https://img.shields.io/github/license/yourusername/pdretro?style=flat-square)](LICENSE)

[Installation](#installation) • [Quick Start](#quick-start) • [Usage](#usage) • [Documentation](#documentation)

---

## Overview

pdretro provides a lightweight Python interface to libretro cores, enabling programmatic control of retro game emulation. Built with a pull-based architecture, it allows frame-by-frame stepping, real-time audio/video capture, direct memory access, and dynamic ROM swapping—all without GUI dependencies.

### Key Features

- **Pure Headless Operation**: No SDL, OpenGL, or GUI dependencies
- **Frame-Perfect Control**: Step through emulation frame-by-frame with Python generators
- **Zero-Copy Video Access**: Direct memory access to frame buffers via NumPy arrays
- **Audio Streaming**: Capture PCM16 stereo audio synchronized with video frames
- **Direct Memory Access**: Read/write game memory in real-time for AI training, cheats, and analysis
- **Hot-Swappable ROMs**: Load and unload games without restarting the core
- **Save State Support**: Serialize and restore emulation state at any time
- **Multiple Input Types**: Full controller and analog stick support (4 ports)
- **Fast & Lightweight**: Minimal C wrapper around libretro with NumPy-optimized operations

## Installation

### Install with pip

```bash
pip install pdretro
```

### Prerequisites

**Required:**

- Python 3.8 or higher
- NumPy 1.20.0+
- Libretro cores (`.so`/`.dll`/`.dylib` files)

**Optional:**

- Pillow (for image output in examples)
- pytest (for running tests)

### Obtaining Libretro Cores

Download precompiled cores from:

- **RetroArch Buildbot**: https://buildbot.libretro.com/nightly/
- **Platform-specific packages**: Most Linux distributions include `libretro-*` packages

**Common cores:**

- `snes9x_libretro` - SNES emulation
- `genesis_plus_gx_libretro` - Genesis/Mega Drive
- `gambatte_libretro` - Game Boy / Game Boy Color
- `mgba_libretro` - Game Boy Advance
- `nestopia_libretro` - NES

## Quick Start

```python
from pdretro import Emulator

# Initialize emulator with a core
with Emulator("cores/snes9x_libretro.so") as emu:
    # Load a ROM
    emu.load_game("roms/super_mario_world.sfc")

    # Get system information
    print(f"Core: {emu.system_info.library_name} v{emu.system_info.library_version}")
    print(f"Running at {emu.av_info.fps} FPS")

    # Run 60 frames
    for i, (video, audio) in enumerate(emu.frames):
        if i >= 60:
            break

        # Convert to RGB and process
        rgb_frame = video.to_rgb()
        print(f"Frame {i}: {rgb_frame.shape}, Audio: {audio.frames} samples")
```

### Generator-Based Workflow

```python
# Video-only generator
for video in emu.video_frames:
    frame = video.to_rgb()  # Shape: (height, width, 3)
    # Process frame...

# Audio-only generator
for audio in emu.audio_frames:
    samples = audio.data  # NumPy array (frames, 2)
    # Process audio...

# Combined generator
for video, audio in emu.frames:
    # Process both simultaneously
    pass
```

## Usage

### Basic Emulation

```python
from pdretro import Emulator

# Initialize and load
emu = Emulator("cores/snes9x_libretro.so")
emu.load_game("roms/game.sfc")

# Step through frames manually
emu.step()
video = emu.get_video_frame()
audio = emu.get_audio_frame()

# Or use generators
for video, audio in emu.frames:
    # Your processing logic
    pass

# Cleanup
emu.unload_game()
emu.shutdown()  # Or use context manager
```

### Context Manager Pattern

```python
with Emulator("cores/mgba_libretro.so") as emu:
    emu.load_game("roms/pokemon.gba")

    # Generator automatically handles cleanup
    for i, video in enumerate(emu.video_frames):
        if i >= 100:
            break
        # Process frames...
# Automatic cleanup on exit
```

### Input Control

```python
from pdretro import Emulator, RetroButton

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/game.sfc")

    # Button press using enum
    emu.set_button(0, RetroButton.A, True)

    # Step with input applied
    emu.step()

    # Release button
    emu.set_button(0, RetroButton.A, False)

    # Clear all inputs
    emu.clear_input()
```

**Available buttons:**

```python
RetroButton.B, RetroButton.Y, RetroButton.SELECT, RetroButton.START
RetroButton.UP, RetroButton.DOWN, RetroButton.LEFT, RetroButton.RIGHT
RetroButton.A, RetroButton.X, RetroButton.L, RetroButton.R
RetroButton.L2, RetroButton.R2, RetroButton.L3, RetroButton.R3
```

### Analog Input

```python
from pdretro import RetroAnalogStick, RetroAnalogAxis

# Set left analog stick on port 0
emu.set_analog(
    port=0,
    stick=RetroAnalogStick.LEFT,
    axis=RetroAnalogAxis.X,
    value=32767  # Range: -32768 to 32767
)
```

### Memory Access

```python
from pdretro import Emulator, MemoryRegion

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/super_mario_world.sfc")

    # Get system RAM
    wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)
    print(f"Memory: {wram.name}, Size: {wram.size} bytes")

    # Read single byte
    coins = wram.read_byte(0x0DBF)

    # Write single byte
    wram.write_byte(0x0DBE, 99)  # Set lives to 99

    # Read multi-byte values
    x_position = wram.read_uint16(0x94)
    score = wram.read_uint32(0x0F34)

    # Direct NumPy array access (fastest)
    wram.data[0x100] = 0xFF
    values = wram.data[0x100:0x200]

    # Search for patterns
    matches = wram.search(b'\x01\x02\x03')
    print(f"Found pattern at: {[hex(addr) for addr in matches]}")
```

**Available memory regions:**

```python
MemoryRegion.SAVE_RAM      # Battery-backed save RAM (SRAM)
MemoryRegion.SYSTEM_RAM    # Main system RAM (WRAM on SNES)
MemoryRegion.VIDEO_RAM     # Video RAM (VRAM)
MemoryRegion.RTC           # Real-time clock data
```

### Save States

```python
import _ra_wrapper

# Get required state size
state_size = _ra_wrapper.get_state_size()

if state_size > 0:
    # Save state
    state_data = _ra_wrapper.serialize_state()

    # Run some frames...
    for _ in range(100):
        emu.step()

    # Restore state
    _ra_wrapper.unserialize_state(state_data)
```

### Multiple ROMs

```python
with Emulator("cores/snes9x_libretro.so") as emu:
    # Load first game
    emu.load_game("roms/game1.sfc")
    for i, video in enumerate(emu.video_frames):
        if i >= 60:
            break

    # Switch to second game
    emu.unload_game()
    emu.load_game("roms/game2.sfc")
    for i, video in enumerate(emu.video_frames):
        if i >= 60:
            break
```

## Documentation

### Architecture

pdretro uses a two-layer architecture:

```
┌─────────────────────────────────┐
│     Python API (emulator.py)    │  ← High-level interface
│   - Emulator class              │
│   - Generator methods           │
│   - NumPy integration           │
│   - Memory access wrapper       │
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│   C Extension (_ra_wrapper)     │  ← Low-level wrapper
│   - Core loading/management     │
│   - Frame stepping              │
│   - Input handling              │
│   - Memory operations           │
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│      Libretro Core (.so)        │  ← Emulation engine
│   - Game logic                  │
│   - Video/audio generation      │
│   - Memory management           │
└─────────────────────────────────┘
```

### Data Classes

#### `SystemInfo`

Contains core metadata:

```python
@dataclass
class SystemInfo:
    library_name: str          # e.g., "Snes9x"
    library_version: str       # e.g., "1.62.3"
    valid_extensions: list[str]  # e.g., ["sfc", "smc"]
    need_fullpath: bool        # Whether core needs full ROM path
```

#### `AVInfo`

Audio/video specifications:

```python
@dataclass
class AVInfo:
    fps: float                 # Target frames per second
    sample_rate: float         # Audio sample rate (Hz)
    base_width: int           # Native video width
    base_height: int          # Native video height
    max_width: int            # Maximum width
    max_height: int           # Maximum height
    aspect_ratio: float       # Pixel aspect ratio
```

#### `VideoFrame`

Video frame data:

```python
@dataclass
class VideoFrame:
    data: np.ndarray          # Raw pixel buffer
    width: int                # Frame width
    height: int               # Frame height
    pitch: int                # Bytes per row
    format: int               # Pixel format (0/1/2)

    def to_rgb(self) -> np.ndarray:
        # Returns: (height, width, 3) uint8 array
```

**Supported pixel formats:**

- `0`: 0RGB1555 (16-bit)
- `1`: XRGB8888 (32-bit)
- `2`: RGB565 (16-bit)

#### `AudioFrame`

Audio sample data:

```python
@dataclass
class AudioFrame:
    data: np.ndarray          # Shape: (frames, 2), dtype: int16
    frames: int               # Number of stereo frames
    sample_rate: float        # Sample rate in Hz
```

#### `Memory`

Memory region wrapper:

```python
@dataclass
class Memory:
    data: np.ndarray          # Direct NumPy array access
    size: int                 # Size in bytes
    name: str                 # Region name (e.g., "WRAM")
    region_type: MemoryRegion # Region type enum

    # Methods
    read_byte(address: int) -> int
    write_byte(address: int, value: int)
    read_bytes(address: int, length: int) -> bytes
    write_bytes(address: int, data: bytes)
    read_uint16(address: int, little_endian: bool = True) -> int
    write_uint16(address: int, value: int, little_endian: bool = True)
    read_uint32(address: int, little_endian: bool = True) -> int
    write_uint32(address: int, value: int, little_endian: bool = True)
    search(pattern: bytes, start: int = 0) -> list[int]
```

### Video Frame Conversion

The `VideoFrame.to_rgb()` method efficiently converts raw pixel data to RGB:

```python
video = emu.get_video_frame()
rgb = video.to_rgb()  # NumPy array (height, width, 3)

# Use with PIL
from PIL import Image
img = Image.fromarray(rgb, 'RGB')
img.save('frame.png')

# Use with OpenCV
import cv2
bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
cv2.imwrite('frame.png', bgr)
```

### Performance Considerations

#### Frame Rate Control

pdretro operates in a pull-based model—Python controls the frame rate:

```python
import time

target_fps = emu.av_info.fps
frame_time = 1.0 / target_fps

for video, audio in emu.frames:
    start = time.time()

    # Process frame...

    # Maintain target FPS
    elapsed = time.time() - start
    if elapsed < frame_time:
        time.sleep(frame_time - elapsed)
```

#### Zero-Copy Access

Video, audio, and memory data use NumPy array views with no copying:

```python
# Efficient: view into existing buffer
video = emu.get_video_frame()
print(video.data.flags.owndata)  # False

# Efficient: direct RGB conversion
rgb = video.to_rgb()  # Uses NumPy vectorized operations

# Efficient: direct memory access
wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)
value = wram.data[0x100]  # Direct array indexing
```

#### Generator Efficiency

Generators maintain minimal memory footprint:

```python
# Memory-efficient: only one frame in memory
for video in emu.video_frames:
    process(video)

# Memory-inefficient: loads all frames
frames = list(emu.video_frames)  # Don't do this!
```

#### Memory Access Performance

```python
wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)

# FASTEST: Direct NumPy array access
value = wram.data[0x100]

# FAST: Batch operations
values = wram.data[0x100:0x200]

# SLOWER: Helper methods (bounds checking overhead)
value = wram.read_byte(0x100)
```

### Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pillow

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=pdretro
```

**Test requirements:**

- SNES9x core: `snes9x_libretro.dll` in `cores/`
- F-Zero ROM: `f-zero.sfc` in `roms/`

## Examples

### Save Screenshots

```python
from pdretro import Emulator
from PIL import Image
import time

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/game.sfc")

    time.sleep(5) # Skip black start screen

    # Save screenshot
    video = emu.get_video_frame()
    rgb = video.to_rgb()
    Image.fromarray(rgb, 'RGB').save('screenshot.png')
```

### Record Video

```python
from pdretro import Emulator
import cv2
import numpy as np
import time

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/game.sfc")

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(
        'output.mp4',
        fourcc,
        emu.av_info.fps,
        (emu.av_info.base_width, emu.av_info.base_height)
    )

    # Record 300 frames (10 seconds at 30fps)
    for i, video in enumerate(emu.video_frames):
        if i >= 300:
            break

        rgb = video.to_rgb()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        out.write(bgr)
        time.sleep(1/30)

    out.release()
```

### AI Training Loop

```python
from pdretro import Emulator, MemoryRegion, RetroButton
import numpy as np

def train_agent():
    with Emulator("cores/snes9x_libretro.so") as emu:
        emu.load_game("roms/game.sfc")

        # Get memory access
        wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)

        for episode in range(1000):
            # Reset game
            emu.reset()

            for frame_num in range(1000):
                # Get current state from memory
                state = {
                    'x_pos': wram.read_uint16(0x94),
                    'y_pos': wram.read_uint16(0x96),
                    'lives': wram.read_byte(0x0DBE),
                    'coins': wram.read_byte(0x0DBF)
                }

                # Agent decides action
                action = agent.get_action(state)

                # Apply action
                emu.clear_input()
                if action == 0:  # Jump
                    emu.set_button(0, RetroButton.A, True)
                elif action == 1:  # Right
                    emu.set_button(0, RetroButton.RIGHT, True)

                # Step emulation
                emu.step()

                # Get reward and train
                reward = compute_reward(state)
                agent.train(state, action, reward)
```

### Game State Extraction

```python
from pdretro import Emulator, MemoryRegion

def get_mario_state(emu):
    """Extract Mario's complete game state"""
    wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)

    return {
        'x_position': wram.read_uint16(0x94),
        'y_position': wram.read_uint16(0x96),
        'x_speed': wram.read_uint16(0x7B),
        'y_speed': wram.read_uint16(0x7D),
        'power_up': wram.read_byte(0x19),
        'coins': wram.read_byte(0x0DBF),
        'lives': wram.read_byte(0x0DBE),
        'score': wram.read_uint32(0x0F34) & 0xFFFFFF,
        'level': wram.read_byte(0x13BF),
    }

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/super_mario_world.sfc")

    for i, video in enumerate(emu.video_frames):
        if i >= 300:
            break

        state = get_mario_state(emu)
        print(f"Frame {i}: Mario at ({state['x_position']}, {state['y_position']})")
```

### Memory Cheats

```python
from pdretro import Emulator, MemoryRegion

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/super_mario_world.sfc")

    # Get WRAM access
    wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)

    # Wait for game to start
    for _ in range(100):
        emu.step()

    # Apply cheats
    wram.write_byte(0x0DBE, 99)   # Infinite lives
    wram.write_byte(0x0DBF, 99)   # Max coins
    wram.write_byte(0x19, 3)      # Fire flower power-up

    # Continue playing with cheats
    for video in emu.video_frames:
        pass
```

### Audio Analysis

```python
from pdretro import Emulator
import numpy as np
import matplotlib.pyplot as plt

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/game.sfc")

    # Collect audio samples
    audio_buffer = []
    for i, audio in enumerate(emu.audio_frames):
        if i >= 60:  # 2 seconds at 30fps
            break
        audio_buffer.append(audio.data)

    # Concatenate all audio
    full_audio = np.concatenate(audio_buffer, axis=0)

    # Analyze
    left_channel = full_audio[:, 0]
    right_channel = full_audio[:, 1]

    # Plot waveform
    plt.plot(left_channel[:1000])
    plt.title('Audio Waveform')
    plt.show()
```

### Memory Search and Reverse Engineering

```python
from pdretro import Emulator, MemoryRegion

with Emulator("cores/snes9x_libretro.so") as emu:
    emu.load_game("roms/game.sfc")
    wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)

    # Take snapshot of initial state
    snapshot = wram.data.copy()

    # Play for a bit (collect coins, etc)
    for _ in range(300):
        emu.step()

    # Find what changed
    changes = np.where(snapshot != wram.data)[0]

    print(f"Found {len(changes)} changed bytes:")
    for addr in changes[:10]:  # Show first 10
        print(f"  0x{addr:04X}: {snapshot[addr]} -> {wram.data[addr]}")

    # Search for specific patterns
    matches = wram.search(b'\xFF\xFF')
    print(f"Found 0xFFFF at addresses: {[hex(a) for a in matches[:5]]}")
```

## Troubleshooting

### Core Loading Issues

```bash
# Error: "Failed to load core"
# Check core path and architecture (32/64-bit)

# Linux: verify with
file cores/snes9x_libretro.so
ldd cores/snes9x_libretro.so  # Check dependencies

# Windows: use Dependency Walker
```

### ROM Loading Failures

```bash
# Error: "Failed to load game"
# Verify ROM format matches core's valid_extensions

with Emulator("cores/snes9x_libretro.so") as emu:
    print(emu.system_info.valid_extensions)
    # ['sfc', 'smc', 'swc', 'fig', 'bs', 'st']
```

### Memory Access Issues

```python
# Error: "Memory region not available"
# Not all cores support all memory regions

from pdretro import MemoryRegion

try:
    vram = emu.get_memory(MemoryRegion.VIDEO_RAM)
except RuntimeError:
    print("VRAM not available for this core")

# Check which regions are available
for region in MemoryRegion:
    try:
        mem = emu.get_memory(region)
        print(f"✓ {mem.name}: {mem.size} bytes")
    except RuntimeError:
        print(f"✗ {region.name}: Not available")
```

### Performance Issues

**Slow frame processing:**

- Use NumPy vectorized operations
- For memory access, use direct array indexing: `wram.data[addr]`
- Avoid list comprehensions on large arrays
- Profile with `cProfile` to find bottlenecks

**Memory leaks:**

- Always use context managers or call `shutdown()`
- Don't hold references to `VideoFrame` or `AudioFrame` objects
- Clear input state after use

### Platform-Specific Notes

**Windows:**

- Use `.dll` cores from RetroArch buildbot
- Ensure Visual C++ Redistributable is installed

**Linux:**

- Use `.so` cores
- May need to install `libgomp1` for some cores

**macOS:**

- Use `.dylib` cores
- May need to allow core in Security & Privacy settings

## Project Structure

```
pdretro/
├── src/
│   ├── pdretro/
│   │   ├── __init__.py
│   │   └── emulator.py          # High-level Python API
│   └── wrapper/
│       ├── ra_wrapper.c         # Core wrapper implementation
│       ├── ra_wrapper.h         # C API header
│       └── ra_wrapper_python.c  # CPython extension
├── tests/
│   └── test.py                  # Test suite
├── setup.py                     # Build configuration
├── pyproject.toml
└── README.md
```

## License

MIT License - Copyright (c) 2026

See [LICENSE](LICENSE) for full text.

## Links

- **PyPI**: https://pypi.org/project/pdretro/
- **GitHub**: https://github.com/ColinThePanda/pdretro
- **Issues**: https://github.com/ColinThePanda/pdretro/issues
- **Libretro**: https://www.libretro.com/

## Acknowledgments

Built on the [libretro API](https://www.libretro.com/) - a simple but powerful emulation framework enabling cross-platform emulator development
