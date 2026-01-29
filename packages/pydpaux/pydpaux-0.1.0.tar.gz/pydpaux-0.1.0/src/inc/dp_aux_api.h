/**
 *
 * @file ap_aux_api.h
 * @version v1-r0
 *
 */
#ifndef _DP_AUX_API_H
#define _DP_AUX_API_H
#if defined(__cplusplus)
#pragma once
#endif
#if defined(__cplusplus)
//extern "C" {
#endif

#include <stdint.h>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Required for STL containers
#include <pybind11/numpy.h>

#include "igcl_api.h"
#include "dp_edid_parser.h"

namespace py = pybind11;

typedef enum dp_match_level_t
{
    DP_MATCH_LEVEL_NONE             = 0x00,
    DP_MATCH_LEVEL_DISPLAY_INDEX    = 0x01,
    DP_MATCH_LEVEL_ADAPTER_INDEX     = 0x02,
    DP_MATCH_LEVEL_EDID_HASH        = 0x04,
    DP_MATCH_LEVEL_DISPLAY_HANDLE   = 0x08,
    DP_MATCH_LEVEL_ALL              = 0x0F,

    DP_MATCH_LEVEL_THRESHOLD        = 0x07  //minimum level to consider a match
}dp_match_level_t;

inline dp_match_level_t operator+=(dp_match_level_t& lhs, dp_match_level_t rhs) {
    return lhs = static_cast<dp_match_level_t>(static_cast<std::underlying_type_t<dp_match_level_t>>(lhs) + static_cast<std::underlying_type_t<dp_match_level_t>>(rhs));
}

struct dp_display_prop_t{
    ctl_display_output_handle_t hDisplayOutput;

    //edia related members  
    uint8_t edid[EDID_MAX_SIZE];
    uint16_t EdidSize;
    char name[EDID_MAX_TEXT_DESCRIPTOR_LENGTH + 1];
    char serial[EDID_MAX_TEXT_DESCRIPTOR_LENGTH + 1];

    ctl_result_t RetrieveEDID(void);

    //used to map display handle when refreshing display list
    dp_match_level_t MatchLevel;
    uint32_t DisplayIndex;
    uint32_t AdapterIndex;  

    //low level AUX and I2C access methods
    ctl_result_t I2CRead (uint32_t address, uint32_t offset, uint32_t size, uint8_t *buf );
    ctl_result_t I2CWrite(uint32_t address, uint32_t offset, uint32_t size, uint8_t *buf );
    ctl_result_t AUXRead (uint32_t address, uint32_t size, uint8_t *buf );
    ctl_result_t AUXWrite(uint32_t address, uint32_t size, uint8_t *buf );

    //python wrapper for corresponding C++ methods
    py::array_t<uint8_t> pyAUXRead(uint32_t address, uint32_t size );
    py::array_t<uint8_t> pyI2CRead(uint32_t address, uint32_t offset, uint32_t size );
    
    uint32_t pyAUXWrite(uint32_t address, py::array_t<uint8_t> data);    
    uint32_t pyI2CWrite(uint32_t address, uint32_t offset, py::array_t<uint8_t> data);

    uint32_t pyRefreshHandle(void);

    //constructor to initialize .hDisplayOutput with given handle(h)
    dp_display_prop_t (ctl_display_output_handle_t h) : hDisplayOutput(h) {}
} ;

//functions exposed to python
std::vector<dp_display_prop_t> dpGetDisplays(void);

//functions used internally
ctl_result_t dpInit(void);

//automatically called when module is unloaded
void dpDeInit(void);

ctl_result_t dpRefreshDisplayOutputHandle(dp_display_prop_t *targetDisplay);

//retrieve full info for a display, validate it, then save in dp_display_prop_t structure if valid
dp_display_prop_t * dpSaveDisplayInfo(ctl_display_output_handle_t hDisplayOutput);

#if defined(__cplusplus)
//} // extern "C"
#endif

#endif // _DP_AUX_API_H