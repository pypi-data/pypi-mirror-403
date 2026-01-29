import pytest
import numpy as np
from pathlib import Path
from pdretro import Emulator
from PIL import Image
import time

CORE_PATH = "cores/snes9x_libretro.dll"
ROM_PATH = "roms/f-zero.sfc"

# ----------------------------
# Fixture for emulator setup
# ----------------------------
@pytest.fixture(scope="module")
def emu():
    with Emulator(CORE_PATH) as e:
        e.load_game(ROM_PATH)
        yield e
        e.unload_game()

# ----------------------------
# Video frame shape
# ----------------------------
def test_video_frame_shape(emu):
    """Check that the video frame dimensions match SNES specs."""
    video = next(emu.video_frames)
    assert video.width == 256, f"Expected width 256, got {video.width}"
    assert video.height == 224, f"Expected height 224, got {video.height}"
    assert video.data is not None
    assert video.format in {0, 1, 2}, f"Unexpected format {video.format}"

# ----------------------------
# Video frame RGB conversion
# ----------------------------
def test_video_frame_rgb_conversion(emu):
    """Check that to_rgb produces an RGB array of shape (height, width, 3) with dtype uint8."""
    video = next(emu.video_frames)
    rgb = video.to_rgb()
    assert isinstance(rgb, np.ndarray)
    assert rgb.shape == (video.height, video.width, 3)
    assert rgb.dtype == np.uint8
    assert rgb.min() >= 0 and rgb.max() <= 255

# ----------------------------
# Audio frame shape and type
# ----------------------------
def test_audio_frame_shape(emu):
    """Ensure audio frames are stereo int16 arrays with >0 frames."""
    audio = next(emu.audio_frames)
    assert audio.data.shape[1] == 2  # stereo
    assert audio.data.dtype == np.int16
    assert audio.frames > 0

# ----------------------------
# Frame generator continuity
# ----------------------------
def test_frame_generator_continuity(emu):
    """Retrieve multiple frames and ensure frames advance correctly."""
    gen = emu.frames
    first_video, first_audio = next(gen)
    second_video, second_audio = next(gen)
    # Frames should not be identical references
    assert first_video is not second_video
    assert first_audio is not second_audio

# ----------------------------
# Performance / FPS
# ----------------------------
def test_frame_rate(emu):
    """Check that emulator can produce frames close to nominal FPS."""
    N = 10
    start = time.time()
    for i, _ in enumerate(emu.frames):
        if i >= N:
            break
    duration = time.time() - start
    measured_fps = N / duration
    print(f"Measured FPS over {N} frames: {measured_fps:.1f}")
    # Allow 20% tolerance
    assert measured_fps >= 0.8 * emu.av_info.fps

# ----------------------------
# Save a frame to disk
# ----------------------------
def test_save_frame_image(emu, tmp_path: Path):
    """Save one RGB frame to disk to check visual correctness."""
    video = next(emu.video_frames)
    rgb = video.to_rgb()
    out_file = tmp_path / "frame.png"
    Image.fromarray(rgb, 'RGB').save(out_file)
    assert out_file.exists()