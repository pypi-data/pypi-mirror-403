#ifndef RA_WRAPPER_H
#define RA_WRAPPER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C"
{
#endif

    /* ============================================================================
     * Return Codes
     * ========================================================================= */

    typedef enum
    {
        RA_OK = 0,
        RA_ERROR_INIT = -1,
        RA_ERROR_CORE_LOAD = -2,
        RA_ERROR_GAME_LOAD = -3,
        RA_ERROR_NO_CORE = -4,
        RA_ERROR_NO_GAME = -5,
        RA_ERROR_INVALID_PORT = -6,
        RA_ERROR_INVALID_PARAM = -7,
        RA_ERROR_ALREADY_INIT = -8,
        RA_ERROR_NOT_INIT = -9,
        RA_ERROR_HW_RENDER_REQUIRED = -10,
        RA_ERROR_NO_MEMORY = -11,
        RA_ERROR_INVALID_ADDRESS = -12,
    } ra_result_t;

    /* ============================================================================
     * Data Structures
     * ========================================================================= */

    /* Pixel format */
    typedef enum
    {
        RA_PIXEL_FORMAT_0RGB1555 = 0, /* 16-bit */
        RA_PIXEL_FORMAT_XRGB8888 = 1, /* 32-bit */
        RA_PIXEL_FORMAT_RGB565 = 2    /* 16-bit */
    } ra_pixel_format_t;

    /* Video frame */
    typedef struct
    {
        const void *data;         /* Frame buffer (read-only) */
        size_t width;             /* Width in pixels */
        size_t height;            /* Height in pixels */
        size_t pitch;             /* Bytes per row */
        ra_pixel_format_t format; /* Pixel format */
    } ra_video_frame_t;

    /* Audio frame */
    typedef struct
    {
        const int16_t *data; /* Interleaved stereo samples (L, R, L, R, ...) */
        size_t frames;       /* Number of stereo frames */
        double sample_rate;  /* Sample rate in Hz */
    } ra_audio_frame_t;

    /* System info */
    typedef struct
    {
        const char *library_name;
        const char *library_version;
        const char *valid_extensions;
        bool need_fullpath;
    } ra_system_info_t;

    /* AV timing info */
    typedef struct
    {
        double fps;          /* Target frames per second */
        double sample_rate;  /* Audio sample rate */
        size_t base_width;   /* Base video width */
        size_t base_height;  /* Base video height */
        size_t max_width;    /* Maximum video width */
        size_t max_height;   /* Maximum video height */
        double aspect_ratio; /* Pixel aspect ratio (0 = use base dimensions) */
    } ra_av_info_t;

    /* Memory region info */
    typedef struct
    {
        uint8_t *data;       /* Pointer to memory region */
        size_t size;         /* Size of region in bytes */
        const char *name;    /* Region name (e.g., "WRAM", "SRAM", "VRAM") */
    } ra_memory_region_t;

    /* ============================================================================
     * Core Management
     * ========================================================================= */

    /**
     * Initialize a libretro core.
     *
     * @param core_path Path to libretro core (.so/.dll/.dylib)
     * @return RA_OK on success
     */
    ra_result_t ra_init_core(const char *core_path);

    /**
     * Get system information from the core.
     *
     * @param info Structure to fill
     * @return RA_OK on success
     */
    ra_result_t ra_get_system_info(ra_system_info_t *info);

    /**
     * Get AV timing information (call after loading a game).
     *
     * @param info Structure to fill
     * @return RA_OK on success
     */
    ra_result_t ra_get_av_info(ra_av_info_t *info);

    /**
     * Shutdown the core and free resources.
     *
     * @return RA_OK on success
     */
    ra_result_t ra_shutdown(void);

    /* ============================================================================
     * Game Management
     * ========================================================================= */

    /**
     * Load a game ROM.
     *
     * @param rom_path Path to ROM file
     * @return RA_OK on success
     */
    ra_result_t ra_load_game(const char *rom_path);

    /**
     * Unload the current game.
     *
     * @return RA_OK on success
     */
    ra_result_t ra_unload_game(void);

    /**
     * Reset the game to initial state.
     *
     * @return RA_OK on success
     */
    ra_result_t ra_reset(void);

    /* ============================================================================
     * Emulation
     * ========================================================================= */

    /**
     * Advance emulation by one frame.
     *
     * @return RA_OK on success
     */
    ra_result_t ra_step(void);

    /**
     * Get the latest video frame (valid until next ra_step).
     *
     * @param frame Structure to fill
     * @return RA_OK on success
     */
    ra_result_t ra_get_video_frame(ra_video_frame_t *frame);

    /**
     * Get the latest audio samples (valid until next ra_step).
     *
     * @param audio Structure to fill
     * @return RA_OK on success
     */
    ra_result_t ra_get_audio_frame(ra_audio_frame_t *audio);

    /* ============================================================================
     * Input - Buttons
     * ========================================================================= */

    /* Standard button IDs (matches libretro RETRO_DEVICE_ID_JOYPAD_*) */
    typedef enum
    {
        RA_BUTTON_B = 0,
        RA_BUTTON_Y = 1,
        RA_BUTTON_SELECT = 2,
        RA_BUTTON_START = 3,
        RA_BUTTON_UP = 4,
        RA_BUTTON_DOWN = 5,
        RA_BUTTON_LEFT = 6,
        RA_BUTTON_RIGHT = 7,
        RA_BUTTON_A = 8,
        RA_BUTTON_X = 9,
        RA_BUTTON_L = 10,
        RA_BUTTON_R = 11,
        RA_BUTTON_L2 = 12,
        RA_BUTTON_R2 = 13,
        RA_BUTTON_L3 = 14,
        RA_BUTTON_R3 = 15
    } ra_button_t;

    /**
     * Set button state.
     *
     * @param port Controller port (0-3)
     * @param button Button ID
     * @param pressed True if pressed, false if released
     * @return RA_OK on success
     */
    ra_result_t ra_set_button(uint32_t port, ra_button_t button, bool pressed);

    /* ============================================================================
     * Input - Analog Sticks
     * ========================================================================= */

    /* Analog stick selection */
    typedef enum
    {
        RA_ANALOG_LEFT = 0,
        RA_ANALOG_RIGHT = 1
    } ra_analog_stick_t;

    /* Analog axis selection */
    typedef enum
    {
        RA_ANALOG_X = 0,
        RA_ANALOG_Y = 1
    } ra_analog_axis_t;

    /**
     * Set analog stick axis value.
     *
     * @param port Controller port (0-3)
     * @param stick Which stick (left or right)
     * @param axis Which axis (X or Y)
     * @param value Analog value (-32768 to 32767, 0 is center)
     * @return RA_OK on success
     */
    ra_result_t ra_set_analog(uint32_t port, ra_analog_stick_t stick,
                              ra_analog_axis_t axis, int16_t value);

    /**
     * Clear all input state (release all buttons, center all sticks).
     *
     * @return RA_OK on success
     */
    ra_result_t ra_clear_input(void);

    /* ============================================================================
     * Save States
     * ========================================================================= */

    /**
     * Get save state size in bytes.
     *
     * @return Size in bytes, or 0 if not supported
     */
    size_t ra_get_state_size(void);

    /**
     * Save state to buffer.
     *
     * @param data Buffer (must be at least ra_get_state_size() bytes)
     * @param size Size of buffer
     * @return RA_OK on success
     */
    ra_result_t ra_serialize_state(void *data, size_t size);

    /**
     * Load state from buffer.
     *
     * @param data Buffer containing state
     * @param size Size of buffer
     * @return RA_OK on success
     */
    ra_result_t ra_unserialize_state(const void *data, size_t size);

    /* ============================================================================
     * Memory Access
     * ========================================================================= */

    /* Memory region types (matches libretro RETRO_MEMORY_*) */
    typedef enum
    {
        RA_MEMORY_SAVE_RAM = 0,      /* Battery-backed save RAM */
        RA_MEMORY_RTC = 1,            /* Real-time clock data */
        RA_MEMORY_SYSTEM_RAM = 2,     /* Main system RAM (WRAM on SNES) */
        RA_MEMORY_VIDEO_RAM = 3       /* Video RAM */
    } ra_memory_type_t;

    /**
     * Get a memory region from the core.
     *
     * @param type Memory region type
     * @param region Structure to fill with memory info
     * @return RA_OK on success, RA_ERROR_NO_MEMORY if region doesn't exist
     */
    ra_result_t ra_get_memory_region(ra_memory_type_t type, ra_memory_region_t *region);

    /**
     * Read a single byte from memory.
     *
     * @param type Memory region type
     * @param address Address within region
     * @param value Pointer to store read value
     * @return RA_OK on success
     */
    ra_result_t ra_read_memory_byte(ra_memory_type_t type, size_t address, uint8_t *value);

    /**
     * Write a single byte to memory.
     *
     * @param type Memory region type
     * @param address Address within region
     * @param value Value to write
     * @return RA_OK on success
     */
    ra_result_t ra_write_memory_byte(ra_memory_type_t type, size_t address, uint8_t value);

    /**
     * Read multiple bytes from memory.
     *
     * @param type Memory region type
     * @param address Starting address within region
     * @param buffer Buffer to store read data
     * @param size Number of bytes to read
     * @return RA_OK on success
     */
    ra_result_t ra_read_memory(ra_memory_type_t type, size_t address, void *buffer, size_t size);

    /**
     * Write multiple bytes to memory.
     *
     * @param type Memory region type
     * @param address Starting address within region
     * @param buffer Data to write
     * @param size Number of bytes to write
     * @return RA_OK on success
     */
    ra_result_t ra_write_memory(ra_memory_type_t type, size_t address, const void *buffer, size_t size);

    /* ============================================================================
     * Utilities
     * ========================================================================= */

    /**
     * Get error message for a result code.
     *
     * @param result Result code
     * @return Error message string
     */
    const char *ra_get_error_string(ra_result_t result);

    /**
     * Get wrapper version string.
     *
     * @return Version string "major.minor.patch"
     */
    const char *ra_get_version(void);

    bool ra_core_requires_hw_render(void);

#ifdef __cplusplus
}
#endif

#endif /* RA_WRAPPER_H */