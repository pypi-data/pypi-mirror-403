
#include <stdexcept>
#include <iostream>
#include "dp_aux_api.h"
#include <Python.h>

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

static ctl_result_t _checkResultCode(ctl_result_t code){
    if (CTL_RESULT_SUCCESS == code ){
        return code;
    }
    else if (CTL_RESULT_ERROR_INSUFFICIENT_PERMISSIONS == code ){
        PyErr_SetString(PyExc_PermissionError, "Insufficient permission. Please run with elevated privileges.");
        throw py::error_already_set();        
    }
    else{
        std::stringstream ss;
        ss << "Error code: 0x" << std::hex << code ;
        throw std::runtime_error(ss.str());
    }
}

py::array_t<uint8_t> dp_display_prop_t::pyAUXRead(uint32_t address, uint32_t size ){
    // Allocate a new NumPy array of the specified size
    py::array_t<uint8_t> array(size);
    auto buffer = array.request();
    uint8_t* ptr = static_cast<uint8_t*>(buffer.ptr);
    
    ctl_result_t code = AUXRead(address, size, ptr);

    _checkResultCode(code);
    return array;
}

uint32_t dp_display_prop_t::pyAUXWrite(uint32_t address, py::array_t<uint8_t> data){
    // Request a buffer info object for the array
    py::buffer_info buf_info = data.request();

    // Access array dimensions and pointer to data
    uint8_t *ptr = static_cast<uint8_t *>(buf_info.ptr);

    ctl_result_t code = AUXWrite(address, (uint32_t)buf_info.size, ptr);
    return (uint32_t) _checkResultCode(code);
}

py::array_t<uint8_t> dp_display_prop_t::pyI2CRead(uint32_t address, uint32_t offset, uint32_t size ){
    // Allocate a new NumPy array of the specified size
    py::array_t<uint8_t> array(size);
    auto buffer = array.request();
    uint8_t* ptr = static_cast<uint8_t*>(buffer.ptr);
    
    ctl_result_t code = I2CRead(address, offset, size, ptr);

    _checkResultCode(code);
    return array;
}

uint32_t dp_display_prop_t::pyI2CWrite(uint32_t address, uint32_t offset, py::array_t<uint8_t> data){
    // Request a buffer info object for the array
    py::buffer_info buf_info = data.request();

    // Access array dimensions and pointer to data
    uint8_t *ptr = static_cast<uint8_t *>(buf_info.ptr);

    ctl_result_t code = I2CWrite(address, offset, buf_info.size, ptr);
    return (uint32_t) _checkResultCode(code);
}

uint32_t dp_display_prop_t::pyRefreshHandle(void){
    ctl_result_t code = dpRefreshDisplayOutputHandle(this);
    return (uint32_t) _checkResultCode(code);
}

class ModuleInitializer {
public:
    ModuleInitializer() {
        //dpInit();
    }
    ~ModuleInitializer() {
        dpDeInit();
    }
};

// Create a static instance to ensure cleanup
static ModuleInitializer s_module_initializer; 

PYBIND11_MODULE(_core, m, py::mod_gil_not_used(), py::multiple_interpreters::per_interpreter_gil()) {
    m.doc() = R"pbdoc(
        pydpaux plugin
    )pbdoc";

    py::class_<dp_display_prop_t>(m, "Display")
        //.def(py::init<>()) // Bind constructor
        .def("i2c_read", &dp_display_prop_t::pyI2CRead)
        .def("i2c_write", &dp_display_prop_t::pyI2CWrite)
        .def("aux_read", &dp_display_prop_t::pyAUXRead)
        .def("aux_write", &dp_display_prop_t::pyAUXWrite)
        .def("refresh_handle", &dp_display_prop_t::pyRefreshHandle)
        .def_readonly("edid_size", &dp_display_prop_t::EdidSize)
        .def_readonly("name", &dp_display_prop_t::name)
        .def_readonly("serial", &dp_display_prop_t::serial)
        .def_property_readonly("edid",  [](py::object& obj) {
            dp_display_prop_t& o = obj.cast<dp_display_prop_t&>();
            return py::array(o.EdidSize, o.edid, obj); // Size, pointer to data, owner
        });

    m.def("get_displays", &dpGetDisplays, py::return_value_policy::reference, R"pbdoc(
        Get display list
    )pbdoc");

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}
