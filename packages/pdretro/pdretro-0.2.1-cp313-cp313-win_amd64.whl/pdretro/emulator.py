import _ra_wrapper
import numpy as np
import os
from dataclasses import dataclass
from enum import IntEnum

class RetroButton(IntEnum):
    """RetroArch button IDs matching libretro RETRO_DEVICE_ID_JOYPAD_*"""
    B = 0
    Y = 1
    SELECT = 2
    START = 3
    UP = 4
    DOWN = 5
    LEFT = 6
    RIGHT = 7
    A = 8
    X = 9
    L = 10
    R = 11
    L2 = 12
    R2 = 13
    L3 = 14
    R3 = 15

class RetroAnalogStick(IntEnum):
    """Analog stick selection"""
    LEFT = 0
    RIGHT = 1

class RetroAnalogAxis(IntEnum):
    """Analog axis selection"""
    X = 0
    Y = 1

class MemoryRegion(IntEnum):
    """Memory region types"""
    SAVE_RAM = 0      # Battery-backed save RAM (SRAM)
    RTC = 1           # Real-time clock data
    SYSTEM_RAM = 2    # Main system RAM (WRAM on SNES)
    VIDEO_RAM = 3     # Video RAM (VRAM)

@dataclass
class SystemInfo:
    library_name: str
    library_version: str
    valid_extensions: list[str]
    need_fullpath: bool

    @classmethod
    def from_dict(cls, info: dict) -> 'SystemInfo':
        return cls(
            library_name=info['library_name'],
            library_version=info['library_version'],
            valid_extensions=info['valid_extensions'].split('|'),
            need_fullpath=info['need_fullpath']
        )

@dataclass
class AVInfo:
    fps: float
    sample_rate: float
    base_width: int
    base_height: int
    max_width: int
    max_height: int
    aspect_ratio: float

    @classmethod
    def from_dict(cls, info: dict) -> 'AVInfo':
        return cls(**info)

@dataclass
class VideoFrame:
    data: np.ndarray  # Raw pixel data (pointer / bytes)
    width: int
    height: int
    pitch: int
    format: int

    @classmethod
    def from_dict(cls, frame: dict) -> 'VideoFrame':
        return cls(**frame)

    def to_rgb(self) -> np.ndarray:
        # Allocate output array once
        out = np.empty((self.height, self.width, 3), dtype=np.uint8)

        if self.format == 1:  # XRGB8888
            raw = np.frombuffer(self.data, dtype=np.uint32).reshape(self.height, self.pitch // 4)
            raw = raw[:, :self.width]  # just view, no copy
            out[..., 0] = (raw >> 16) & 0xFF  # R
            out[..., 1] = (raw >> 8) & 0xFF   # G
            out[..., 2] = raw & 0xFF          # B

        elif self.format == 0:  # 0RGB1555
            raw = np.frombuffer(self.data, dtype=np.uint16).reshape(self.height, self.pitch // 2)
            raw = raw[:, :self.width]
            out[..., 0] = ((raw >> 10) & 0x1F) << 3
            out[..., 1] = ((raw >> 5) & 0x1F) << 3
            out[..., 2] = (raw & 0x1F) << 3

        elif self.format == 2:  # RGB565
            raw = np.frombuffer(self.data, dtype=np.uint16).reshape(self.height, self.pitch // 2)
            raw = raw[:, :self.width]
            out[..., 0] = ((raw >> 11) & 0x1F) << 3
            out[..., 1] = ((raw >> 5) & 0x3F) << 2
            out[..., 2] = (raw & 0x1F) << 3

        else:
            raise ValueError(f"Unsupported video format: {self.format}")

        return out


@dataclass
class AudioFrame:
    data: np.ndarray  # Stereo int16 samples
    frames: int
    sample_rate: float

    @classmethod
    def from_dict(cls, audio: dict) -> 'AudioFrame':
        return cls(**audio)

@dataclass
class Memory:
    """Memory region wrapper with NumPy array access"""
    data: np.ndarray  # Direct memory access via NumPy array
    size: int
    name: str
    region_type: MemoryRegion

    def read_byte(self, address: int) -> int:
        """Read a single byte from memory
        
        Args:
            address: Address within this memory region
            
        Returns:
            Byte value (0-255)
        """
        if address >= self.size:
            raise IndexError(f"Address {address} out of range for {self.name} (size: {self.size})")
        return int(self.data[address])
    
    def write_byte(self, address: int, value: int):
        """Write a single byte to memory
        
        Args:
            address: Address within this memory region
            value: Byte value to write (0-255)
        """
        if address >= self.size:
            raise IndexError(f"Address {address} out of range for {self.name} (size: {self.size})")
        if not 0 <= value <= 255:
            raise ValueError(f"Value must be 0-255, got {value}")
        self.data[address] = value
    
    def read_bytes(self, address: int, length: int) -> bytes:
        """Read multiple bytes from memory
        
        Args:
            address: Starting address
            length: Number of bytes to read
            
        Returns:
            Bytes object
        """
        if address + length > self.size:
            raise IndexError(f"Read range {address}:{address+length} out of bounds for {self.name} (size: {self.size})")
        return bytes(self.data[address:address+length])
    
    def write_bytes(self, address: int, data: bytes):
        """Write multiple bytes to memory
        
        Args:
            address: Starting address
            data: Bytes to write
        """
        length = len(data)
        if address + length > self.size:
            raise IndexError(f"Write range {address}:{address+length} out of bounds for {self.name} (size: {self.size})")
        self.data[address:address+length] = np.frombuffer(data, dtype=np.uint8)
    
    def read_uint16(self, address: int, little_endian: bool = True) -> int:
        """Read a 16-bit unsigned integer
        
        Args:
            address: Address to read from
            little_endian: True for little-endian, False for big-endian
            
        Returns:
            16-bit unsigned integer value
        """
        if address + 2 > self.size:
            raise IndexError(f"Address {address} out of range for 16-bit read")
        
        if little_endian:
            return int(self.data[address]) | (int(self.data[address + 1]) << 8)
        else:
            return (int(self.data[address]) << 8) | int(self.data[address + 1])
    
    def write_uint16(self, address: int, value: int, little_endian: bool = True):
        """Write a 16-bit unsigned integer
        
        Args:
            address: Address to write to
            value: 16-bit value to write
            little_endian: True for little-endian, False for big-endian
        """
        if address + 2 > self.size:
            raise IndexError(f"Address {address} out of range for 16-bit write")
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"Value must be 0-65535, got {value}")
        
        if little_endian:
            self.data[address] = value & 0xFF
            self.data[address + 1] = (value >> 8) & 0xFF
        else:
            self.data[address] = (value >> 8) & 0xFF
            self.data[address + 1] = value & 0xFF
    
    def read_uint32(self, address: int, little_endian: bool = True) -> int:
        """Read a 32-bit unsigned integer
        
        Args:
            address: Address to read from
            little_endian: True for little-endian, False for big-endian
            
        Returns:
            32-bit unsigned integer value
        """
        if address + 4 > self.size:
            raise IndexError(f"Address {address} out of range for 32-bit read")
        
        if little_endian:
            return (int(self.data[address]) |
                    (int(self.data[address + 1]) << 8) |
                    (int(self.data[address + 2]) << 16) |
                    (int(self.data[address + 3]) << 24))
        else:
            return ((int(self.data[address]) << 24) |
                    (int(self.data[address + 1]) << 16) |
                    (int(self.data[address + 2]) << 8) |
                    int(self.data[address + 3]))
    
    def write_uint32(self, address: int, value: int, little_endian: bool = True):
        """Write a 32-bit unsigned integer
        
        Args:
            address: Address to write to
            value: 32-bit value to write
            little_endian: True for little-endian, False for big-endian
        """
        if address + 4 > self.size:
            raise IndexError(f"Address {address} out of range for 32-bit write")
        if not 0 <= value <= 0xFFFFFFFF:
            raise ValueError(f"Value must be 0-4294967295, got {value}")
        
        if little_endian:
            self.data[address] = value & 0xFF
            self.data[address + 1] = (value >> 8) & 0xFF
            self.data[address + 2] = (value >> 16) & 0xFF
            self.data[address + 3] = (value >> 24) & 0xFF
        else:
            self.data[address] = (value >> 24) & 0xFF
            self.data[address + 1] = (value >> 16) & 0xFF
            self.data[address + 2] = (value >> 8) & 0xFF
            self.data[address + 3] = value & 0xFF
    
    def search(self, pattern: bytes, start: int = 0) -> list[int]:
        """Search for a byte pattern in memory
        
        Args:
            pattern: Bytes to search for
            start: Starting address for search
            
        Returns:
            List of addresses where pattern was found
        """
        matches = []
        pattern_len = len(pattern)
        
        for i in range(start, self.size - pattern_len + 1):
            if bytes(self.data[i:i+pattern_len]) == pattern:
                matches.append(i)
        
        return matches

class Emulator:
    def __init__(self, core_path: str):
        self.core_path = os.path.abspath(core_path)
        
        if not os.path.isfile(core_path):
            raise FileNotFoundError(f"Core not found: {core_path}")
        
        _ra_wrapper.init_core(self.core_path)
        self._system_info = SystemInfo.from_dict(_ra_wrapper.get_system_info())
        self._av_info = None
        self._game_loaded = False
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try: 
            _ra_wrapper.shutdown()
        except:
            pass
    
    @property
    def system_info(self) -> SystemInfo:
        return self._system_info
    
    @property
    def av_info(self) -> AVInfo:
        if not self._game_loaded or self._av_info is None:
            raise RuntimeError("No game loaded")
        return self._av_info

    
    @property
    def is_game_loaded(self) -> bool:
        return self._game_loaded

    def load_game(self, rom_path: str):
        rom_path = os.path.abspath(rom_path)
        
        if not os.path.isfile(rom_path):
            raise FileNotFoundError(f"ROM not found: {rom_path}")
        
        try:
            _ra_wrapper.load_game(rom_path)
        except RuntimeError as e:
            error_msg = str(e)
            if "hardware rendering" in error_msg.lower():
                raise RuntimeError(
                    f"This core requires hardware rendering (OpenGL/Vulkan) which is not currently supported.\n"
                    f"Hardware rendering cores include: parallel_n64, mupen64plus_next, flycast, beetle-psx-hw.\n"
                    f"Try using a software-rendering core instead:\n"
                    f"  - SNES: snes9x_libretro, bsnes_libretro\n"
                    f"  - Genesis: genesis_plus_gx_libretro\n"
                    f"  - Game Boy: gambatte_libretro, mgba_libretro\n"
                    f"  - NES: nestopia_libretro, fceumm_libretro\n"
                    f"  - PSX: beetle-psx (software version)"
                )
            raise
        
        self._av_info = AVInfo.from_dict(_ra_wrapper.get_av_info())
        self._game_loaded = True
    
    def unload_game(self):
        if self._game_loaded:
            _ra_wrapper.unload_game()
            self._game_loaded = False
            self._av_info = None
    
    def reset(self):
        if not self._game_loaded:
            raise RuntimeError("No game loaded")
        _ra_wrapper.reset()
    
    def step(self):
        if not self._game_loaded:
            raise RuntimeError("No game loaded")
        _ra_wrapper.step()
    
    def get_video_frame(self) -> VideoFrame:
        return VideoFrame.from_dict(_ra_wrapper.get_video_frame())
    
    def get_audio_frame(self) -> AudioFrame:
        return AudioFrame.from_dict(_ra_wrapper.get_audio_frame())

    def set_button(self, port: int, button: int | RetroButton, pressed: bool):
        """Set button state
        
        Args:
            port: Controller port (0-3)
            button: Button ID (0-15) or RetroButton enum
            pressed: True if pressed, False if released
        
        Example:
            emu.set_button(0, RetroButton.A, True)
            emu.set_button(0, 8, True)  # Also valid
        """
        _ra_wrapper.set_button(port, int(button), pressed)

    def set_analog(self, port: int, stick: int | RetroAnalogStick, axis: int | RetroAnalogAxis, value: int):
        """Set analog stick axis value
        
        Args:
            port: Controller port (0-3)
            stick: Which stick (0=left, 1=right) or RetroAnalogStick enum
            axis: Which axis (0=X, 1=Y) or RetroAnalogAxis enum
            value: Analog value (-32768 to 32767, 0 is center)
        
        Example:
            emu.set_analog(0, RetroAnalogStick.LEFT, RetroAnalogAxis.X, 32767)
            emu.set_analog(0, 0, 0, 32767)  # Also valid
        """
        _ra_wrapper.set_analog(port, int(stick), int(axis), value)

    def clear_input(self):
        """Clear all input state (release all buttons, center all sticks)"""
        _ra_wrapper.clear_input()

    def get_memory(self, region: MemoryRegion | int) -> Memory:
        """Get access to a memory region
        
        Args:
            region: Memory region type (MemoryRegion enum or int)
            
        Returns:
            Memory object with direct NumPy array access
            
        Raises:
            RuntimeError: If memory region is not available
            
        Example:
            wram = emu.get_memory(MemoryRegion.SYSTEM_RAM)
            value = wram.read_byte(0x7E0010)  # Read from address
            wram.write_byte(0x7E0010, 99)     # Write to address
            wram.data[0x100:0x200] = 0        # Direct NumPy access
        """
        if not self._game_loaded:
            raise RuntimeError("No game loaded")
        
        region_type = MemoryRegion(region) if isinstance(region, int) else region
        mem_dict = _ra_wrapper.get_memory_region(int(region_type))
        
        return Memory(
            data=mem_dict['data'],
            size=mem_dict['size'],
            name=mem_dict['name'],
            region_type=region_type
        )

    def _frame_generator(self):
        while True:
            self.step()
            yield self.get_video_frame(), self.get_audio_frame()
    
    def _video_frame_generator(self):
        while True:
            self.step()
            yield self.get_video_frame()

    def _audio_frame_generator(self):
        while True:
            self.step()
            yield self.get_audio_frame()
    
    @property
    def frames(self):
        if not self._game_loaded:
            raise RuntimeError("No game loaded")
        return self._frame_generator()

    @property
    def video_frames(self):
        if not self._game_loaded:
            raise RuntimeError("No game loaded")
        return self._video_frame_generator()

    @property
    def audio_frames(self):
        if not self._game_loaded:
            raise RuntimeError("No game loaded")
        return self._audio_frame_generator()

    def __del__(self):
        try:
            _ra_wrapper.shutdown()
        except:
            pass