#define PY_SSIZE_T_CLEAN
#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>
#include "ra_wrapper.h"

static PyObject* py_ra_init_core(PyObject* self, PyObject* args) {
    const char* core_path;
    if (!PyArg_ParseTuple(args, "s", &core_path)) {
        return NULL;
    }
    
    ra_result_t result = ra_init_core(core_path);
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_shutdown(PyObject* self, PyObject* args) {
    ra_result_t result = ra_shutdown();
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_load_game(PyObject* self, PyObject* args) {
    const char* rom_path;
    if (!PyArg_ParseTuple(args, "s", &rom_path)) {
        return NULL;
    }
    
    ra_result_t result = ra_load_game(rom_path);
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_unload_game(PyObject* self, PyObject* args) {
    ra_result_t result = ra_unload_game();
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_reset(PyObject* self, PyObject* args) {
    ra_result_t result = ra_reset();
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_step(PyObject* self, PyObject* args) {
    ra_result_t result = ra_step();
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_get_system_info(PyObject* self, PyObject* args) {
    ra_system_info_t info;
    ra_result_t result = ra_get_system_info(&info);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    return Py_BuildValue("{s:s,s:s,s:s,s:O}",
        "library_name", info.library_name,
        "library_version", info.library_version,
        "valid_extensions", info.valid_extensions,
        "need_fullpath", info.need_fullpath ? Py_True : Py_False
    );
}

static PyObject* py_ra_get_av_info(PyObject* self, PyObject* args) {
    ra_av_info_t info;
    ra_result_t result = ra_get_av_info(&info);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    return Py_BuildValue("{s:d,s:d,s:k,s:k,s:k,s:k,s:d}",
        "fps", info.fps,
        "sample_rate", info.sample_rate,
        "base_width", (unsigned long)info.base_width,
        "base_height", (unsigned long)info.base_height,
        "max_width", (unsigned long)info.max_width,
        "max_height", (unsigned long)info.max_height,
        "aspect_ratio", info.aspect_ratio
    );
}

static PyObject* py_ra_get_video_frame(PyObject* self, PyObject* args) {
    ra_video_frame_t frame;
    ra_result_t result = ra_get_video_frame(&frame);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    npy_intp dims[2] = {(npy_intp)frame.height, (npy_intp)frame.pitch};
    PyObject* array = PyArray_SimpleNewFromData(2, dims, NPY_UINT8, (void*)frame.data);
    
    if (array == NULL) {
        return NULL;
    }
    
    PyArray_CLEARFLAGS((PyArrayObject*)array, NPY_ARRAY_WRITEABLE);
    
    return Py_BuildValue("{s:N,s:k,s:k,s:k,s:i}",
        "data", array,
        "width", (unsigned long)frame.width,
        "height", (unsigned long)frame.height,
        "pitch", (unsigned long)frame.pitch,
        "format", frame.format
    );
}

static PyObject* py_ra_get_audio_frame(PyObject* self, PyObject* args) {
    ra_audio_frame_t audio;
    ra_result_t result = ra_get_audio_frame(&audio);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    npy_intp dims[2] = {(npy_intp)audio.frames, 2};
    PyObject* array = PyArray_SimpleNewFromData(2, dims, NPY_INT16, (void*)audio.data);
    
    if (array == NULL) {
        return NULL;
    }
    
    PyArray_CLEARFLAGS((PyArrayObject*)array, NPY_ARRAY_WRITEABLE);
    
    return Py_BuildValue("{s:N,s:k,s:d}",
        "data", array,
        "frames", (unsigned long)audio.frames,
        "sample_rate", audio.sample_rate
    );
}

static PyObject* py_ra_set_button(PyObject* self, PyObject* args) {
    unsigned int port;
    int button;
    int pressed;
    
    if (!PyArg_ParseTuple(args, "Iip", &port, &button, &pressed)) {
        return NULL;
    }
    
    ra_result_t result = ra_set_button((uint32_t)port, (ra_button_t)button, pressed != 0);
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_set_analog(PyObject* self, PyObject* args) {
    unsigned int port;
    int stick;
    int axis;
    int value;
    
    if (!PyArg_ParseTuple(args, "Iiih", &port, &stick, &axis, &value)) {
        return NULL;
    }
    
    ra_result_t result = ra_set_analog((uint32_t)port, (ra_analog_stick_t)stick, (ra_analog_axis_t)axis, (int16_t)value);
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_clear_input(PyObject* self, PyObject* args) {
    ra_result_t result = ra_clear_input();
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_get_state_size(PyObject* self, PyObject* args) {
    size_t size = ra_get_state_size();
    return PyLong_FromSize_t(size);
}

static PyObject* py_ra_serialize_state(PyObject* self, PyObject* args) {
    size_t size = ra_get_state_size();
    if (size == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Save states not supported");
        return NULL;
    }
    
    PyObject* bytes = PyBytes_FromStringAndSize(NULL, size);
    if (bytes == NULL) {
        return NULL;
    }
    
    char* buffer = PyBytes_AsString(bytes);
    ra_result_t result = ra_serialize_state(buffer, size);
    
    if (result != RA_OK) {
        Py_DECREF(bytes);
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    return bytes;
}

static PyObject* py_ra_unserialize_state(PyObject* self, PyObject* args) {
    const char* data;
    Py_ssize_t size;
    
    if (!PyArg_ParseTuple(args, "y#", &data, &size)) {
        return NULL;
    }
    
    ra_result_t result = ra_unserialize_state(data, size);
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_get_version(PyObject* self, PyObject* args) {
    return PyUnicode_FromString(ra_get_version());
}

static PyObject* py_ra_core_requires_hw_render(PyObject* self, PyObject* args) {
    if (ra_core_requires_hw_render()) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject* py_ra_get_memory_region(PyObject* self, PyObject* args) {
    int memory_type;
    
    if (!PyArg_ParseTuple(args, "i", &memory_type)) {
        return NULL;
    }
    
    ra_memory_region_t region;
    ra_result_t result = ra_get_memory_region((ra_memory_type_t)memory_type, &region);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    // Create NumPy array view of memory (writable)
    npy_intp dims[1] = {(npy_intp)region.size};
    PyObject* array = PyArray_SimpleNewFromData(1, dims, NPY_UINT8, region.data);
    
    if (array == NULL) {
        return NULL;
    }
    
    // Make array writable (user can modify memory)
    PyArray_ENABLEFLAGS((PyArrayObject*)array, NPY_ARRAY_WRITEABLE);
    
    return Py_BuildValue("{s:N,s:k,s:s}",
        "data", array,
        "size", (unsigned long)region.size,
        "name", region.name
    );
}

static PyObject* py_ra_read_memory_byte(PyObject* self, PyObject* args) {
    int memory_type;
    size_t address;
    
    if (!PyArg_ParseTuple(args, "ik", &memory_type, &address)) {
        return NULL;
    }
    
    uint8_t value;
    ra_result_t result = ra_read_memory_byte((ra_memory_type_t)memory_type, address, &value);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    return PyLong_FromUnsignedLong(value);
}

static PyObject* py_ra_write_memory_byte(PyObject* self, PyObject* args) {
    int memory_type;
    size_t address;
    int value;
    
    if (!PyArg_ParseTuple(args, "iki", &memory_type, &address, &value)) {
        return NULL;
    }
    
    if (value < 0 || value > 255) {
        PyErr_SetString(PyExc_ValueError, "Value must be 0-255");
        return NULL;
    }
    
    ra_result_t result = ra_write_memory_byte((ra_memory_type_t)memory_type, address, (uint8_t)value);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_ra_read_memory(PyObject* self, PyObject* args) {
    int memory_type;
    size_t address;
    size_t size;
    
    if (!PyArg_ParseTuple(args, "ikk", &memory_type, &address, &size)) {
        return NULL;
    }
    
    PyObject* bytes = PyBytes_FromStringAndSize(NULL, size);
    if (bytes == NULL) {
        return NULL;
    }
    
    char* buffer = PyBytes_AsString(bytes);
    ra_result_t result = ra_read_memory((ra_memory_type_t)memory_type, address, buffer, size);
    
    if (result != RA_OK) {
        Py_DECREF(bytes);
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    return bytes;
}

static PyObject* py_ra_write_memory(PyObject* self, PyObject* args) {
    int memory_type;
    size_t address;
    const char* data;
    Py_ssize_t size;
    
    if (!PyArg_ParseTuple(args, "iky#", &memory_type, &address, &data, &size)) {
        return NULL;
    }
    
    ra_result_t result = ra_write_memory((ra_memory_type_t)memory_type, address, data, size);
    
    if (result != RA_OK) {
        PyErr_SetString(PyExc_RuntimeError, ra_get_error_string(result));
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyMethodDef module_methods[] = {
    {"init_core", py_ra_init_core, METH_VARARGS, "Initialize a libretro core"},
    {"shutdown", py_ra_shutdown, METH_NOARGS, "Shutdown the core"},
    {"load_game", py_ra_load_game, METH_VARARGS, "Load a game ROM"},
    {"unload_game", py_ra_unload_game, METH_NOARGS, "Unload the current game"},
    {"reset", py_ra_reset, METH_NOARGS, "Reset the game"},
    {"step", py_ra_step, METH_NOARGS, "Advance emulation by one frame"},
    {"get_system_info", py_ra_get_system_info, METH_NOARGS, "Get system information"},
    {"get_av_info", py_ra_get_av_info, METH_NOARGS, "Get AV timing information"},
    {"get_video_frame", py_ra_get_video_frame, METH_NOARGS, "Get the latest video frame"},
    {"get_audio_frame", py_ra_get_audio_frame, METH_NOARGS, "Get the latest audio samples"},
    {"set_button", py_ra_set_button, METH_VARARGS, "Set button state"},
    {"set_analog", py_ra_set_analog, METH_VARARGS, "Set analog stick state"},
    {"clear_input", py_ra_clear_input, METH_NOARGS, "Clear all input"},
    {"get_state_size", py_ra_get_state_size, METH_NOARGS, "Get save state size"},
    {"serialize_state", py_ra_serialize_state, METH_NOARGS, "Save state to bytes"},
    {"unserialize_state", py_ra_unserialize_state, METH_VARARGS, "Load state from bytes"},
    {"get_version", py_ra_get_version, METH_NOARGS, "Get wrapper version"},
    {"core_requires_hw_render", py_ra_core_requires_hw_render, METH_NOARGS, "Check if core requires hardware rendering"},
    {"get_memory_region", py_ra_get_memory_region, METH_VARARGS, "Get memory region"},
    {"read_memory_byte", py_ra_read_memory_byte, METH_VARARGS, "Read single byte from memory"},
    {"write_memory_byte", py_ra_write_memory_byte, METH_VARARGS, "Write single byte to memory"},
    {"read_memory", py_ra_read_memory, METH_VARARGS, "Read multiple bytes from memory"},
    {"write_memory", py_ra_write_memory, METH_VARARGS, "Write multiple bytes to memory"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "_ra_wrapper",
    "Low-level libretro wrapper",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit__ra_wrapper(void) {
    import_array();
    return PyModule_Create(&module_def);
}