
#define _CRTDBG_MAP_ALLOC
#include <crtdbg.h>
#include <iostream>
#include <sstream>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#define CTL_APIEXPORT // caller of control API DLL shall define this before
                      // including igcl_api.h
#include "igcl_api.h"
#include "GenericIGCLApp.h"
#include "dp_aux_api.h"

//ctl_result_t GResult = CTL_RESULT_SUCCESS;

// global handle to the DLL module.
// Must be initialized before using any ctl* APIs.
static ctl_api_handle_t hAPIHandle;

std::vector<dp_display_prop_t> ActiveDisplays;

static ctl_result_t dpEnumerateDevices(void);

static void _checkDataSize(uint32_t size, uint32_t MaxSize){
    if (size > MaxSize){
        std::stringstream ss;
        ss << "Up to " << MaxSize << " bytes allowed in one operation.";
        throw std::runtime_error(ss.str());
    }
}

// Try to find best match from existing list
// If match level is below threshold, add as new display
static void _findMatchedDisplay(dp_display_prop_t *info ){
    dp_match_level_t MaxMatchedLevel = DP_MATCH_LEVEL_NONE;
    
    dp_display_prop_t *MatchedDisplay = nullptr;

    for (auto& display : ActiveDisplays) {
        dp_match_level_t CurrentMatchedLevel = DP_MATCH_LEVEL_NONE;

        if (display.AdapterIndex == info->AdapterIndex){
            CurrentMatchedLevel += DP_MATCH_LEVEL_ADAPTER_INDEX;
        }
        if (display.DisplayIndex == info->DisplayIndex){
            CurrentMatchedLevel += DP_MATCH_LEVEL_DISPLAY_INDEX;      
        }
        if (display.hDisplayOutput == info->hDisplayOutput){
            CurrentMatchedLevel += DP_MATCH_LEVEL_DISPLAY_HANDLE;      
        }   
        if ( display.edid[127] == info->edid[127] ){
            CurrentMatchedLevel += DP_MATCH_LEVEL_EDID_HASH;      
        }   

        if (CurrentMatchedLevel > MaxMatchedLevel){
            MaxMatchedLevel = CurrentMatchedLevel;
            MatchedDisplay = &display;
            //printf("Update match level for %s: display %s at level0x%02X\n", info->name, display.name, (uint32_t)MaxMatchedLevel);
        }
    }

    if (MaxMatchedLevel >= DP_MATCH_LEVEL_THRESHOLD){
        MatchedDisplay->MatchLevel = MaxMatchedLevel;
        if (MaxMatchedLevel < DP_MATCH_LEVEL_ALL){
            if (MatchedDisplay->hDisplayOutput != info->hDisplayOutput){
                //update to new handle
                printf("Update display handler for %s: 0x%08u -> 0x%08u\n", MatchedDisplay->name, (uint32_t)MatchedDisplay->hDisplayOutput, (uint32_t)info->hDisplayOutput);   
                MatchedDisplay->hDisplayOutput  = info->hDisplayOutput;
            }
            MatchedDisplay->AdapterIndex = info->AdapterIndex;
            MatchedDisplay->DisplayIndex = info->DisplayIndex;
        }
    } else {
        printf("Add new display, Name: %s, Serial : %s\n", info->name, info->serial );  
        info->MatchLevel = DP_MATCH_LEVEL_ALL;

        ActiveDisplays.push_back(*info);
    }
}

//refresh display handle by re-enumerating devices and finding best match
//throw exception if no match found
ctl_result_t dpRefreshDisplayOutputHandle(dp_display_prop_t *targetDisplay){
    ctl_result_t Result = CTL_RESULT_SUCCESS;

    for (auto& display : ActiveDisplays) {
        display.MatchLevel = DP_MATCH_LEVEL_NONE;
    }

    Result = dpEnumerateDevices();

    if (targetDisplay && targetDisplay->MatchLevel == DP_MATCH_LEVEL_NONE){
        std::stringstream ss;
        ss << "No matched display for " << targetDisplay->name << " after refresh."; ;
        throw std::runtime_error(ss.str());
    }

    for (auto& display : ActiveDisplays) {
        if (display.hDisplayOutput && display.MatchLevel == DP_MATCH_LEVEL_NONE){
            printf("WARNING: No matched display for %s, who was on Adapter[%u].Display[%u]\n", display.name, display.AdapterIndex, display.DisplayIndex ); 
            display.hDisplayOutput = nullptr;
        }
    }

    return Result;
}
/***************************************************************
 * @brief EnumerateDisplayHandles
 * Retrieve and Save detailed information for specific display
 * @param hDisplayOutput, DisplayCount
 * @return ctl_result_t
 ***************************************************************/
ctl_result_t EnumerateDisplayHandles(ctl_display_output_handle_t *hDisplayOutput, uint32_t DisplayCount, uint32_t AdapterIndex)
{
    ctl_result_t Result = CTL_RESULT_SUCCESS;

    for (uint32_t DisplayIndex = 0; DisplayIndex < DisplayCount; DisplayIndex++)
    {
        ctl_display_properties_t DisplayProperties = { 0 };
        DisplayProperties.Size                     = sizeof(ctl_display_properties_t);

        Result = ctlGetDisplayProperties(hDisplayOutput[DisplayIndex], &DisplayProperties);
        LOG_AND_EXIT_ON_ERROR(Result, "ctlGetDisplayProperties");

        bool IsDisplayAttached = (0 != (DisplayProperties.DisplayConfigFlags & CTL_DISPLAY_CONFIG_FLAG_DISPLAY_ATTACHED));

        if (FALSE == IsDisplayAttached)
        {
            continue;
        }
        else{
            dp_display_prop_t *info = dpSaveDisplayInfo(hDisplayOutput[DisplayIndex]);
                        
            if (info){
                //printf("Found display[%d], Name: %s, Serial : %s\n", DisplayIndex, info->name, info->serial );   
                info->DisplayIndex = DisplayIndex;
                info->AdapterIndex = AdapterIndex;         
                _findMatchedDisplay(info);
                //ActiveDisplays.push_back(*info);                
                free(info);
            }
        }
    }

Exit:
    return Result;
}

/***************************************************************
 * @brief EnumerateTargetDisplays
 * Enumerates all the possible target display's for the adapters
 * @param hDisplayOutput, AdapterCount, hDevices
 * @return ctl_result_t
 ***************************************************************/
ctl_result_t EnumerateTargetDisplays(uint32_t AdapterCount, ctl_device_adapter_handle_t *hDevices)
{
    ctl_display_output_handle_t *hDisplayOutput = NULL;
    ctl_result_t Result                         = CTL_RESULT_SUCCESS;
    uint32_t DisplayCount                       = 0;

    for (uint32_t AdapterIndex = 0; AdapterIndex < AdapterCount; AdapterIndex++)
    {
        // enumerate all the possible target display's for the adapters
        // first step is to get the count
        DisplayCount = 0;

        Result = ctlEnumerateDisplayOutputs(hDevices[AdapterIndex], &DisplayCount, hDisplayOutput);
        LOG_AND_EXIT_ON_ERROR(Result, "ctlEnumerateDisplayOutputs");

        if (DisplayCount <= 0)
        {
            printf("Invalid Display Count. skipping display enumration for adapter:%d\n", AdapterIndex);
            continue;
        }

        hDisplayOutput = (ctl_display_output_handle_t *)malloc(sizeof(ctl_display_output_handle_t) * DisplayCount);
        EXIT_ON_MEM_ALLOC_FAILURE(hDisplayOutput, "hDisplayOutput");

        Result = ctlEnumerateDisplayOutputs(hDevices[AdapterIndex], &DisplayCount, hDisplayOutput);
        LOG_AND_EXIT_ON_ERROR(Result, "ctlEnumerateDisplayOutputs");

        Result = EnumerateDisplayHandles(hDisplayOutput, DisplayCount, AdapterIndex);
        LOG_AND_EXIT_ON_ERROR(Result, "EnumerateDisplayHandles");

        CTL_FREE_MEM(hDisplayOutput);
    }

Exit:
    CTL_FREE_MEM(hDisplayOutput);
    return Result;
}


//Called at Init/Refresh function to update display list
static ctl_result_t dpEnumerateDevices(void)
{
    ctl_result_t Result = CTL_RESULT_SUCCESS;
    ctl_device_adapter_handle_t *hDevices = NULL;    
    
    uint32_t AdapterCount = 0;

    // Initialization successful
    // Get the list of Intel Adapters
    Result = ctlEnumerateDevices(hAPIHandle, &AdapterCount, hDevices);
    LOG_AND_EXIT_ON_ERROR(Result, "ctlEnumerateDevices");

    hDevices = (ctl_device_adapter_handle_t *)malloc(sizeof(ctl_device_adapter_handle_t) * AdapterCount);
    EXIT_ON_MEM_ALLOC_FAILURE(hDevices, "hDevices");

    Result = ctlEnumerateDevices(hAPIHandle, &AdapterCount, hDevices);
    LOG_AND_EXIT_ON_ERROR(Result, "ctlEnumerateDevices");

    Result = EnumerateTargetDisplays(AdapterCount, hDevices);
    LOG_AND_EXIT_ON_ERROR(Result, "EnumerateTargetDisplays");

Exit:
    CTL_FREE_MEM(hDevices);
    return Result;
}

ctl_result_t dpInit(void)
{
    ctl_result_t Result = CTL_RESULT_SUCCESS;
    _CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF);

    ctl_init_args_t CtlInitArgs;

    ZeroMemory(&CtlInitArgs, sizeof(ctl_init_args_t));

    CtlInitArgs.AppVersion = CTL_MAKE_VERSION(CTL_IMPL_MAJOR_VERSION, CTL_IMPL_MINOR_VERSION);
    CtlInitArgs.flags      = 0;
    CtlInitArgs.Size       = sizeof(CtlInitArgs);
    CtlInitArgs.Version    = 0;

    // Get a handle to the DLL module.
    Result = ctlInit(&CtlInitArgs, &hAPIHandle);
    LOG_AND_EXIT_ON_ERROR(Result, "ctlInit");

    Result = dpEnumerateDevices();

Exit:
    return Result;
}

//always called at module unload.
//If not called, API behavior may be unpredictable next time when module is loaded again.
void  dpDeInit(void)
{
    if (hAPIHandle){
        ctlClose(hAPIHandle);
        hAPIHandle = NULL;
    }
}

//retrieve full info for a display, validate it, then save in dp_display_prop_t structure if valid
dp_display_prop_t * dpSaveDisplayInfo(ctl_display_output_handle_t hDisplayOutput){
    ctl_result_t Result  = CTL_RESULT_SUCCESS;

    dp_display_prop_t * ptr = (dp_display_prop_t *)malloc(sizeof(dp_display_prop_t));
    if (NULL == ptr)                                                 
    {                                                                
        Result = CTL_RESULT_ERROR_INVALID_NULL_POINTER;              
        printf("Memory Allocation Failed: %s \n", "dp_display_prop_t"); 
        return NULL;
    }                              
    
    dp_display_prop_t* entry = new (ptr) dp_display_prop_t(hDisplayOutput);

    Result = entry->RetrieveEDID();
    if (CTL_RESULT_SUCCESS != Result){
        printf("dpSaveDisplayInfo: RetrieveEDID returned failure code: 0x%X\n", Result);

        free(entry);        
        return NULL;
    }

    //validate EDID data
    if (! edidReformat(entry->edid)){
        printf("dpSaveDisplayInfo: Invalid EDID data\n");
        edidPrintAll(entry->edid);
        free(entry);        
        return NULL;        
    }

    entry->EdidSize = entry->edid[126] ? 256 : 128;
    entry->name[0] = 0;   //initialize
    entry->serial[0] = 0;   //initialize
    
    //parse EDID data
     if (! edidFindMonitorName(entry->edid, entry->name, EDID_MAX_TEXT_DESCRIPTOR_LENGTH)){
        //printf("Use unspecified info instead of monitor name\n");
        edidFindUnspeficiedText(entry->edid, entry->name, EDID_MAX_TEXT_DESCRIPTOR_LENGTH);
     }
     edidFindSerialNumber(entry->edid, entry->serial, EDID_MAX_TEXT_DESCRIPTOR_LENGTH);

     entry->hDisplayOutput = hDisplayOutput;

    return entry;
}

// Retrieve raw EDID data from display by I2CRead
// For some reason, Header does not always start at offset 0, so we read full 256 bytes
// and reformat it later
ctl_result_t dp_display_prop_t::RetrieveEDID(void){
        ctl_result_t Result  = CTL_RESULT_SUCCESS;
        uint8_t *buf = edid;
        for (int i = 0; i < EDID_MAX_SIZE / 16; i++) {
            Result = I2CRead(0xA0, i * 16, 16, buf);
            if (CTL_RESULT_SUCCESS != Result){ 
                printf("RetrieveEDID: I2CRead returned failure code: 0x%X\n", Result);
                return Result;
            }

            buf += 16;
        }    

        return Result;
}

ctl_result_t dp_display_prop_t::AUXRead(uint32_t address,  uint32_t size, uint8_t *buf ){
    ctl_result_t Result           = CTL_RESULT_SUCCESS;
    ctl_aux_access_args_t AUXArgs = { 0 }; // AUX Access WRITE

    _checkDataSize(size, CTL_AUX_MAX_DATA_SIZE);

    AUXArgs.Size                  = sizeof(ctl_aux_access_args_t);
    AUXArgs.OpType                = CTL_OPERATION_TYPE_READ;
    AUXArgs.Address               = address; // DPCD offset for TRAINING_LANE0_SET
    AUXArgs.DataSize              = size;
    AUXArgs.Flags                 = CTL_AUX_FLAG_NATIVE_AUX; // CTL_AUX_FLAG_NATIVE_AUX for DPCD Access & CTL_AUX_FLAG_I2C_AUX for EDID access for DP/eDP displays.

    Result = ctlAUXAccess(hDisplayOutput, &AUXArgs);

    if (CTL_RESULT_SUCCESS != Result)
    {
        printf("ctlAUXAccess: ctlAUXAccess for AUX read returned failure code: 0x%X\n", Result);
        return Result;
    }
    else{
        for (uint32_t i = 0; i < size; i++) {
            buf[i] = AUXArgs.Data[i];
        }       
    }
    return Result;
}

ctl_result_t dp_display_prop_t::AUXWrite(uint32_t address, uint32_t size, uint8_t *buf ){
    ctl_result_t Result           = CTL_RESULT_SUCCESS;
    ctl_aux_access_args_t AUXArgs = { 0 }; // AUX Access WRITE

    _checkDataSize(size, CTL_I2C_MAX_DATA_SIZE);

    AUXArgs.Size                  = sizeof(ctl_aux_access_args_t);
    AUXArgs.OpType                = CTL_OPERATION_TYPE_WRITE;
    AUXArgs.Address               = address; // DPCD offset for TRAINING_LANE0_SET
    AUXArgs.DataSize              = size;
    AUXArgs.Flags                 = CTL_AUX_FLAG_NATIVE_AUX; // CTL_AUX_FLAG_NATIVE_AUX for DPCD Access & CTL_AUX_FLAG_I2C_AUX for EDID access for DP/eDP displays.

    for (int i = 0; i < size; i++){
        AUXArgs.Data[i] = buf[i];
    }
    
    Result = ctlAUXAccess(hDisplayOutput, &AUXArgs);

    return Result;
}

ctl_result_t dp_display_prop_t::I2CRead(uint32_t address, uint32_t offset, uint32_t size, uint8_t *buf ){
    ctl_result_t Result           = CTL_RESULT_SUCCESS;
    ctl_i2c_access_args_t I2CArgs = { 0 }; // I2C Access

    _checkDataSize(size, CTL_I2C_MAX_DATA_SIZE);

    I2CArgs.Size = sizeof(ctl_i2c_access_args_t);
    I2CArgs.OpType = CTL_OPERATION_TYPE_READ;
    I2CArgs.Address = address;
    I2CArgs.Offset = offset;
    I2CArgs.DataSize = size;

    Result = ctlI2CAccess(hDisplayOutput, &I2CArgs);

    if (CTL_RESULT_SUCCESS != Result)
    {
        printf("I2CRead: ctlI2CAccess for I2C read returned failure code: 0x%X\n", Result);
        return Result;
    }
    else{
        for (uint32_t i = 0; i < size; i++) {
            buf[i] = I2CArgs.Data[i];
        }       
    }
    return Result;
}

ctl_result_t dp_display_prop_t::I2CWrite(uint32_t address, uint32_t offset, uint32_t size, uint8_t *buf ){
    ctl_result_t Result           = CTL_RESULT_SUCCESS;
    ctl_i2c_access_args_t I2CArgs = { 0 }; // I2C Access

    _checkDataSize(size, CTL_I2C_MAX_DATA_SIZE);

    I2CArgs.Size     = sizeof(ctl_i2c_access_args_t);
    I2CArgs.OpType   = CTL_OPERATION_TYPE_WRITE;
    I2CArgs.Address  = address; // Address used for demonstration purpose
    I2CArgs.Offset   = offset; // Offset used for demonstration purpose
    I2CArgs.DataSize = size;

    for (int i = 0; i < size; i++){
        I2CArgs.Data[i] = buf[i];
    }
    
    Result = ctlI2CAccess(hDisplayOutput, &I2CArgs);

    return Result;
}

std::vector<dp_display_prop_t> dpGetDisplays(void){
    ctl_result_t Result = CTL_RESULT_SUCCESS;
    if (! hAPIHandle){
        Result = dpInit();
    }
    else{
        Result = dpRefreshDisplayOutputHandle(nullptr);
    }

    if (CTL_RESULT_SUCCESS == Result ){
        return ActiveDisplays;
    }    
    else{
        throw std::runtime_error("Failed to retrieve display list.");
    }        
}