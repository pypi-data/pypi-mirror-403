#include "ra_wrapper.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#define LIB_HANDLE HMODULE
#define lib_open(path) LoadLibraryA(path)
#define lib_sym(handle, name) GetProcAddress(handle, name)
#define lib_close(handle) FreeLibrary(handle)
#else
#include <dlfcn.h>
#define LIB_HANDLE void *
#define lib_open(path) dlopen(path, RTLD_LAZY)
#define lib_sym(handle, name) dlsym(handle, name)
#define lib_close(handle) dlclose(handle)
#endif

#define RETRO_API_VERSION 1
#define RETRO_DEVICE_JOYPAD 1
#define RETRO_DEVICE_ANALOG 2
#define RETRO_DEVICE_INDEX_ANALOG_LEFT 0
#define RETRO_DEVICE_INDEX_ANALOG_RIGHT 1
#define RETRO_ENVIRONMENT_SET_PIXEL_FORMAT 10
#define RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY 9
#define RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY 31
#define RETRO_ENVIRONMENT_SET_HW_RENDER 14
#define RETRO_MEMORY_SAVE_RAM 0
#define RETRO_MEMORY_RTC 1
#define RETRO_MEMORY_SYSTEM_RAM 2
#define RETRO_MEMORY_VIDEO_RAM 3

typedef struct retro_system_info
{
    const char *library_name;
    const char *library_version;
    const char *valid_extensions;
    bool need_fullpath;
    bool block_extract;
} retro_system_info;

typedef struct retro_game_geometry
{
    unsigned base_width;
    unsigned base_height;
    unsigned max_width;
    unsigned max_height;
    float aspect_ratio;
} retro_game_geometry;

typedef struct retro_system_timing
{
    double fps;
    double sample_rate;
} retro_system_timing;

typedef struct retro_system_av_info
{
    retro_game_geometry geometry;
    retro_system_timing timing;
} retro_system_av_info;

typedef struct retro_game_info
{
    const char *path;
    const void *data;
    size_t size;
    const char *meta;
} retro_game_info;

typedef void (*retro_init_t)(void);
typedef void (*retro_deinit_t)(void);
typedef unsigned (*retro_api_version_t)(void);
typedef void (*retro_get_system_info_t)(retro_system_info *info);
typedef void (*retro_get_system_av_info_t)(retro_system_av_info *info);
typedef bool (*retro_set_environment_t)(void *callback);
typedef void (*retro_set_video_refresh_t)(void *callback);
typedef void (*retro_set_audio_sample_t)(void *callback);
typedef void (*retro_set_audio_sample_batch_t)(void *callback);
typedef void (*retro_set_input_poll_t)(void *callback);
typedef void (*retro_set_input_state_t)(void *callback);
typedef bool (*retro_load_game_t)(const retro_game_info *game);
typedef void (*retro_unload_game_t)(void);
typedef void (*retro_run_t)(void);
typedef void (*retro_reset_t)(void);
typedef size_t (*retro_serialize_size_t)(void);
typedef bool (*retro_serialize_t)(void *data, size_t size);
typedef bool (*retro_unserialize_t)(const void *data, size_t size);
typedef void *(*retro_get_memory_data_t)(unsigned id);
typedef size_t (*retro_get_memory_size_t)(unsigned id);

typedef struct
{
    LIB_HANDLE handle;
    retro_init_t retro_init;
    retro_deinit_t retro_deinit;
    retro_api_version_t retro_api_version;
    retro_get_system_info_t retro_get_system_info;
    retro_get_system_av_info_t retro_get_system_av_info;
    retro_set_environment_t retro_set_environment;
    retro_set_video_refresh_t retro_set_video_refresh;
    retro_set_audio_sample_t retro_set_audio_sample;
    retro_set_audio_sample_batch_t retro_set_audio_sample_batch;
    retro_set_input_poll_t retro_set_input_poll;
    retro_set_input_state_t retro_set_input_state;
    retro_load_game_t retro_load_game;
    retro_unload_game_t retro_unload_game;
    retro_run_t retro_run;
    retro_reset_t retro_reset;
    retro_serialize_size_t retro_serialize_size;
    retro_serialize_t retro_serialize;
    retro_unserialize_t retro_unserialize;
    retro_get_memory_data_t retro_get_memory_data;  // ADD THIS
    retro_get_memory_size_t retro_get_memory_size;  // ADD THIS

    bool game_loaded;
    retro_system_info system_info;
    retro_system_av_info av_info;

    void *video_buffer;
    size_t video_width;
    size_t video_height;
    size_t video_pitch;
    ra_pixel_format_t video_format;

    int16_t *audio_buffer;
    size_t audio_buffer_size;
    size_t audio_frames;

    bool input_state[4][16];
    int16_t analog_state[4][2][2];

    bool hw_render_requested;
} core_state_t;

static core_state_t g_core = {0};

static void video_refresh_callback(const void *data, unsigned width, unsigned height, size_t pitch)
{
    if (data)
    {
        g_core.video_buffer = (void *)data;
        g_core.video_width = width;
        g_core.video_height = height;
        g_core.video_pitch = pitch;
    }
}

static void audio_sample_callback(int16_t left, int16_t right)
{
    if (g_core.audio_frames * 2 + 2 > g_core.audio_buffer_size)
    {
        g_core.audio_buffer_size = (g_core.audio_buffer_size == 0) ? 4096 : g_core.audio_buffer_size * 2;
        g_core.audio_buffer = realloc(g_core.audio_buffer, g_core.audio_buffer_size * sizeof(int16_t));
    }

    g_core.audio_buffer[g_core.audio_frames * 2] = left;
    g_core.audio_buffer[g_core.audio_frames * 2 + 1] = right;
    g_core.audio_frames++;
}

static size_t audio_sample_batch_callback(const int16_t *data, size_t frames)
{
    if (g_core.audio_frames * 2 + frames * 2 > g_core.audio_buffer_size)
    {
        while (g_core.audio_frames * 2 + frames * 2 > g_core.audio_buffer_size)
        {
            g_core.audio_buffer_size = (g_core.audio_buffer_size == 0) ? 4096 : g_core.audio_buffer_size * 2;
        }
        g_core.audio_buffer = realloc(g_core.audio_buffer, g_core.audio_buffer_size * sizeof(int16_t));
    }

    memcpy(&g_core.audio_buffer[g_core.audio_frames * 2], data, frames * 2 * sizeof(int16_t));
    g_core.audio_frames += frames;
    return frames;
}

static void input_poll_callback(void)
{
}

static int16_t input_state_callback(unsigned port, unsigned device, unsigned index, unsigned id)
{
    if (port >= 4)
        return 0;

    if (device == RETRO_DEVICE_JOYPAD)
    {
        if (id >= 16)
            return 0;
        return g_core.input_state[port][id] ? 1 : 0;
    }

    if (device == RETRO_DEVICE_ANALOG)
    {
        if (index >= 2 || id >= 2)
            return 0;
        return g_core.analog_state[port][index][id];
    }

    return 0;
}

static bool environment_callback(unsigned cmd, void *data)
{
    switch (cmd)
    {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
    {
        const unsigned *format = (const unsigned *)data;
        if (*format == 0)
        {
            g_core.video_format = RA_PIXEL_FORMAT_0RGB1555;
        }
        else if (*format == 1)
        {
            g_core.video_format = RA_PIXEL_FORMAT_XRGB8888;
        }
        else if (*format == 2)
        {
            g_core.video_format = RA_PIXEL_FORMAT_RGB565;
        }
        return true;
    }
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
    {
        const char **dir = (const char **)data;
        *dir = ".";
        return true;
    }
    case RETRO_ENVIRONMENT_SET_HW_RENDER:
    {
        g_core.hw_render_requested = true;
        return false;
    }
    }
    return false;
}


ra_result_t ra_init_core(const char *core_path)
{
    if (g_core.handle)
    {
        return RA_ERROR_ALREADY_INIT;
    }

    g_core.handle = lib_open(core_path);
    if (!g_core.handle)
    {
        return RA_ERROR_CORE_LOAD;
    }

    g_core.retro_init = (retro_init_t)lib_sym(g_core.handle, "retro_init");
    g_core.retro_deinit = (retro_deinit_t)lib_sym(g_core.handle, "retro_deinit");
    g_core.retro_api_version = (retro_api_version_t)lib_sym(g_core.handle, "retro_api_version");
    g_core.retro_get_system_info = (retro_get_system_info_t)lib_sym(g_core.handle, "retro_get_system_info");
    g_core.retro_get_system_av_info = (retro_get_system_av_info_t)lib_sym(g_core.handle, "retro_get_system_av_info");
    g_core.retro_set_environment = (retro_set_environment_t)lib_sym(g_core.handle, "retro_set_environment");
    g_core.retro_set_video_refresh = (retro_set_video_refresh_t)lib_sym(g_core.handle, "retro_set_video_refresh");
    g_core.retro_set_audio_sample = (retro_set_audio_sample_t)lib_sym(g_core.handle, "retro_set_audio_sample");
    g_core.retro_set_audio_sample_batch = (retro_set_audio_sample_batch_t)lib_sym(g_core.handle, "retro_set_audio_sample_batch");
    g_core.retro_set_input_poll = (retro_set_input_poll_t)lib_sym(g_core.handle, "retro_set_input_poll");
    g_core.retro_set_input_state = (retro_set_input_state_t)lib_sym(g_core.handle, "retro_set_input_state");
    g_core.retro_load_game = (retro_load_game_t)lib_sym(g_core.handle, "retro_load_game");
    g_core.retro_unload_game = (retro_unload_game_t)lib_sym(g_core.handle, "retro_unload_game");
    g_core.retro_run = (retro_run_t)lib_sym(g_core.handle, "retro_run");
    g_core.retro_reset = (retro_reset_t)lib_sym(g_core.handle, "retro_reset");
    g_core.retro_serialize_size = (retro_serialize_size_t)lib_sym(g_core.handle, "retro_serialize_size");
    g_core.retro_serialize = (retro_serialize_t)lib_sym(g_core.handle, "retro_serialize");
    g_core.retro_unserialize = (retro_unserialize_t)lib_sym(g_core.handle, "retro_unserialize");
    
    g_core.retro_get_memory_data = (retro_get_memory_data_t)lib_sym(g_core.handle, "retro_get_memory_data");
    g_core.retro_get_memory_size = (retro_get_memory_size_t)lib_sym(g_core.handle, "retro_get_memory_size");

    if (!g_core.retro_init || !g_core.retro_deinit || !g_core.retro_api_version)
    {
        lib_close(g_core.handle);
        g_core.handle = NULL;
        return RA_ERROR_CORE_LOAD;
    }

    if (g_core.retro_api_version() != RETRO_API_VERSION)
    {
        lib_close(g_core.handle);
        g_core.handle = NULL;
        return RA_ERROR_CORE_LOAD;
    }

    g_core.retro_set_environment(environment_callback);
    g_core.retro_init();
    g_core.retro_set_video_refresh(video_refresh_callback);
    g_core.retro_set_audio_sample(audio_sample_callback);
    g_core.retro_set_audio_sample_batch(audio_sample_batch_callback);
    g_core.retro_set_input_poll(input_poll_callback);
    g_core.retro_set_input_state(input_state_callback);

    g_core.retro_get_system_info(&g_core.system_info);

    return RA_OK;
}

ra_result_t ra_get_system_info(ra_system_info_t *info)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    info->library_name = g_core.system_info.library_name;
    info->library_version = g_core.system_info.library_version;
    info->valid_extensions = g_core.system_info.valid_extensions;
    info->need_fullpath = g_core.system_info.need_fullpath;

    return RA_OK;
}

ra_result_t ra_get_av_info(ra_av_info_t *info)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    info->fps = g_core.av_info.timing.fps;
    info->sample_rate = g_core.av_info.timing.sample_rate;
    info->base_width = g_core.av_info.geometry.base_width;
    info->base_height = g_core.av_info.geometry.base_height;
    info->max_width = g_core.av_info.geometry.max_width;
    info->max_height = g_core.av_info.geometry.max_height;
    info->aspect_ratio = g_core.av_info.geometry.aspect_ratio;

    return RA_OK;
}

ra_result_t ra_shutdown(void)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (g_core.game_loaded)
    {
        g_core.retro_unload_game();
        g_core.game_loaded = false;
    }

    g_core.retro_deinit();
    lib_close(g_core.handle);

    if (g_core.audio_buffer)
    {
        free(g_core.audio_buffer);
    }

    memset(&g_core, 0, sizeof(g_core));

    return RA_OK;
}

ra_result_t ra_load_game(const char *rom_path)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (g_core.game_loaded)
    {
        g_core.retro_unload_game();
        g_core.game_loaded = false;
    }

    g_core.hw_render_requested = false;

    retro_game_info game_info = {0};
    game_info.path = rom_path;

    void *rom_data = NULL;
    size_t rom_size = 0;

    // If core doesn't need fullpath, load ROM into memory
    if (!g_core.system_info.need_fullpath)
    {
        FILE *f = fopen(rom_path, "rb");
        if (!f)
        {
            return RA_ERROR_GAME_LOAD;
        }

        // Get file size
        fseek(f, 0, SEEK_END);
        rom_size = ftell(f);
        fseek(f, 0, SEEK_SET);

        // Allocate and read
        rom_data = malloc(rom_size);
        if (!rom_data)
        {
            fclose(f);
            return RA_ERROR_GAME_LOAD;
        }

        size_t bytes_read = fread(rom_data, 1, rom_size, f);
        fclose(f);

        if (bytes_read != rom_size)
        {
            free(rom_data);
            return RA_ERROR_GAME_LOAD;
        }

        game_info.data = rom_data;
        game_info.size = rom_size;
    }

    bool load_result = g_core.retro_load_game(&game_info);

    // Free ROM data after loading (core copies it internally)
    if (rom_data)
    {
        free(rom_data);
    }

    if (!load_result)
    {
        return RA_ERROR_GAME_LOAD;
    }

    // Check if core requested hardware rendering
    if (g_core.hw_render_requested)
    {
        g_core.retro_unload_game();
        return RA_ERROR_HW_RENDER_REQUIRED;
    }

    g_core.game_loaded = true;
    g_core.retro_get_system_av_info(&g_core.av_info);

    return RA_OK;
}

ra_result_t ra_unload_game(void)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    g_core.retro_unload_game();
    g_core.game_loaded = false;

    return RA_OK;
}

ra_result_t ra_reset(void)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    g_core.retro_reset();

    return RA_OK;
}

ra_result_t ra_step(void)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    g_core.audio_frames = 0;
    g_core.retro_run();

    return RA_OK;
}

ra_result_t ra_get_video_frame(ra_video_frame_t *frame)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    frame->data = g_core.video_buffer;
    frame->width = g_core.video_width;
    frame->height = g_core.video_height;
    frame->pitch = g_core.video_pitch;
    frame->format = g_core.video_format;

    return RA_OK;
}

ra_result_t ra_get_audio_frame(ra_audio_frame_t *audio)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    audio->data = g_core.audio_buffer;
    audio->frames = g_core.audio_frames;
    audio->sample_rate = g_core.av_info.timing.sample_rate;

    return RA_OK;
}

ra_result_t ra_set_button(uint32_t port, ra_button_t button, bool pressed)
{
    if (port >= 4)
    {
        return RA_ERROR_INVALID_PORT;
    }

    if (button >= 16)
    {
        return RA_ERROR_INVALID_PARAM;
    }

    g_core.input_state[port][button] = pressed;

    return RA_OK;
}

ra_result_t ra_set_analog(uint32_t port, ra_analog_stick_t stick, ra_analog_axis_t axis, int16_t value)
{
    if (port >= 4)
    {
        return RA_ERROR_INVALID_PORT;
    }

    if (stick >= 2 || axis >= 2)
    {
        return RA_ERROR_INVALID_PARAM;
    }

    g_core.analog_state[port][stick][axis] = value;

    return RA_OK;
}

ra_result_t ra_clear_input(void)
{
    memset(g_core.input_state, 0, sizeof(g_core.input_state));
    memset(g_core.analog_state, 0, sizeof(g_core.analog_state));

    return RA_OK;
}

size_t ra_get_state_size(void)
{
    if (!g_core.handle || !g_core.game_loaded)
    {
        return 0;
    }

    if (!g_core.retro_serialize_size)
    {
        return 0;
    }

    return g_core.retro_serialize_size();
}

ra_result_t ra_serialize_state(void *data, size_t size)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    if (!g_core.retro_serialize)
    {
        return RA_ERROR_INVALID_PARAM;
    }

    if (!g_core.retro_serialize(data, size))
    {
        return RA_ERROR_INVALID_PARAM;
    }

    return RA_OK;
}

ra_result_t ra_unserialize_state(const void *data, size_t size)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    if (!g_core.retro_unserialize)
    {
        return RA_ERROR_INVALID_PARAM;
    }

    if (!g_core.retro_unserialize(data, size))
    {
        return RA_ERROR_INVALID_PARAM;
    }

    return RA_OK;
}

bool ra_core_requires_hw_render(void)
{
    return g_core.hw_render_requested;
}

ra_result_t ra_get_memory_region(ra_memory_type_t type, ra_memory_region_t *region)
{
    if (!g_core.handle)
    {
        return RA_ERROR_NOT_INIT;
    }

    if (!g_core.game_loaded)
    {
        return RA_ERROR_NO_GAME;
    }

    if (!g_core.retro_get_memory_data || !g_core.retro_get_memory_size)
    {
        return RA_ERROR_NO_MEMORY;
    }

    unsigned retro_type;
    const char *name;

    switch (type)
    {
    case RA_MEMORY_SAVE_RAM:
        retro_type = RETRO_MEMORY_SAVE_RAM;
        name = "SRAM";
        break;
    case RA_MEMORY_RTC:
        retro_type = RETRO_MEMORY_RTC;
        name = "RTC";
        break;
    case RA_MEMORY_SYSTEM_RAM:
        retro_type = RETRO_MEMORY_SYSTEM_RAM;
        name = "WRAM";
        break;
    case RA_MEMORY_VIDEO_RAM:
        retro_type = RETRO_MEMORY_VIDEO_RAM;
        name = "VRAM";
        break;
    default:
        return RA_ERROR_INVALID_PARAM;
    }

    void *data = g_core.retro_get_memory_data(retro_type);
    size_t size = g_core.retro_get_memory_size(retro_type);

    if (!data || size == 0)
    {
        return RA_ERROR_NO_MEMORY;
    }

    region->data = (uint8_t *)data;
    region->size = size;
    region->name = name;

    return RA_OK;
}

ra_result_t ra_read_memory_byte(ra_memory_type_t type, size_t address, uint8_t *value)
{
    ra_memory_region_t region;
    ra_result_t result = ra_get_memory_region(type, &region);

    if (result != RA_OK)
    {
        return result;
    }

    if (address >= region.size)
    {
        return RA_ERROR_INVALID_ADDRESS;
    }

    *value = region.data[address];
    return RA_OK;
}

ra_result_t ra_write_memory_byte(ra_memory_type_t type, size_t address, uint8_t value)
{
    ra_memory_region_t region;
    ra_result_t result = ra_get_memory_region(type, &region);

    if (result != RA_OK)
    {
        return result;
    }

    if (address >= region.size)
    {
        return RA_ERROR_INVALID_ADDRESS;
    }

    region.data[address] = value;
    return RA_OK;
}

ra_result_t ra_read_memory(ra_memory_type_t type, size_t address, void *buffer, size_t size)
{
    ra_memory_region_t region;
    ra_result_t result = ra_get_memory_region(type, &region);

    if (result != RA_OK)
    {
        return result;
    }

    if (address + size > region.size)
    {
        return RA_ERROR_INVALID_ADDRESS;
    }

    memcpy(buffer, &region.data[address], size);
    return RA_OK;
}

ra_result_t ra_write_memory(ra_memory_type_t type, size_t address, const void *buffer, size_t size)
{
    ra_memory_region_t region;
    ra_result_t result = ra_get_memory_region(type, &region);

    if (result != RA_OK)
    {
        return result;
    }

    if (address + size > region.size)
    {
        return RA_ERROR_INVALID_ADDRESS;
    }

    memcpy(&region.data[address], buffer, size);
    return RA_OK;
}

const char *ra_get_error_string(ra_result_t result)
{
    switch (result)
    {
    case RA_OK:
        return "Success";
    case RA_ERROR_INIT:
        return "Initialization error";
    case RA_ERROR_CORE_LOAD:
        return "Failed to load core";
    case RA_ERROR_GAME_LOAD:
        return "Failed to load game";
    case RA_ERROR_NO_CORE:
        return "No core loaded";
    case RA_ERROR_NO_GAME:
        return "No game loaded";
    case RA_ERROR_INVALID_PORT:
        return "Invalid controller port";
    case RA_ERROR_INVALID_PARAM:
        return "Invalid parameter";
    case RA_ERROR_ALREADY_INIT:
        return "Core already initialized";
    case RA_ERROR_NOT_INIT:
        return "Core not initialized";
    case RA_ERROR_HW_RENDER_REQUIRED:
        return "Core requires hardware rendering (not supported)";
    case RA_ERROR_NO_MEMORY:
        return "Memory region not available";
    case RA_ERROR_INVALID_ADDRESS:
        return "Invalid memory address";
    default:
        return "Unknown error";
    }
}

const char *ra_get_version(void)
{
    return "0.1.1";
}