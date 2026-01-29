
#include "dp_edid_parser.h"
#include <stdio.h>
#include <cstring>
#include <crtdbg.h>
#include <stdlib.h>

static const uint8_t EDID_HEADER[] = { 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00 };

//Potential positions of text descriptors in EDID blocks, 
//can be either of SerialNumber, MonitorName or UnspecifiedText
static const uint16_t DESCRIPTOR_POSITIONS[] = { 108, 90, 72};

#define  EDID_HEADER_SIZE (sizeof(EDID_HEADER) / sizeof(EDID_HEADER[0]))

// Print entire EDID data in hex format, for debug purpose
void edidPrintAll(const uint8_t  *data){
    for (int i = 0; i < EDID_MAX_SIZE / 16; i++)
    {
        for (int j = 0; j < 16; j++)
        {
            printf("%02X ", data[i* 16 + j]);
        }
        printf("\n");
    }
}


uint8_t  *edidFindHeader( uint8_t  *data, uint16_t DataSize){
    uint16_t pos, i, j;

    for (i = 0; i < DataSize; i++){        
        for (j = 0; j < EDID_HEADER_SIZE; j++ ){
            pos = (i + j) % DataSize;
            if (data[pos] != EDID_HEADER[j]){
                break;
            }
        }

        if (j == EDID_HEADER_SIZE){
            return data + i;
        }
    }
    return NULL;
}

// Move EDID header to start postion of data buffer
// Returns true if successful
bool edidReformat(uint8_t  *data){
    uint8_t  *header = edidFindHeader(data, EDID_MAX_SIZE);
    uint16_t offset, TailSize;
    
    if (!header){
        return false;
    }

    if (header != data){
        offset = header - data;
        TailSize = sizeof(uint8_t) * (EDID_MAX_SIZE - offset);
        
        //printf("[EDID] Found header at offset %02x\n", offset);

        uint8_t * buf = (uint8_t *)malloc(sizeof(uint8_t) * EDID_MAX_SIZE);

        if (!buf){
            //not likely to happen
            return false;
        }

        memcpy(buf,  header, TailSize);
        memcpy(buf + TailSize, data, sizeof(uint8_t) * offset);
        
        memcpy(data, buf, EDID_MAX_SIZE);
        free(buf);
    }

    return true;
    //todo: add more validation terms
}

// Extract text from descriptor by searching for string terminator
// Returns true if found
static bool edidRetrieveString(const uint8_t *data, char *StrBuf, uint16_t MaxSize){
    int i = 0; 
    while (i < EDID_MAX_TEXT_DESCRIPTOR_LENGTH && i < MaxSize){
        if (0x0A == data[i]){   //LF code
            break;
        }

        StrBuf[i] = data[i];
        i++;
    }

    StrBuf[i] = 0;

    return (i != 0);
}

// Search for text descriptor of given type and extract string
// Returns true if found
static bool edidFindTextDescriptor(const uint8_t *data, uint8_t desc_type, char *StrBuf, uint16_t MaxSize){
    for (int i = 0; i < sizeof(DESCRIPTOR_POSITIONS) / sizeof(DESCRIPTOR_POSITIONS[0]); i++){
        uint16_t j = DESCRIPTOR_POSITIONS[i];
        if (0x00 == data[j] && 0x00 == data[j+1] && desc_type == data[j+3]){
            return edidRetrieveString(data + j + 5, StrBuf, MaxSize);
        }
    }
    return false;
}

bool edidFindSerialNumber(const uint8_t *data, char *StrBuf, uint16_t MaxSize){
    return edidFindTextDescriptor(data, 0xFF, StrBuf, MaxSize);
}

bool edidFindMonitorName(const uint8_t *data, char *StrBuf, uint16_t MaxSize){
    return edidFindTextDescriptor(data, 0xFC, StrBuf, MaxSize);
}

bool edidFindUnspeficiedText(const uint8_t *data, char *StrBuf, uint16_t MaxSize){
    return edidFindTextDescriptor(data, 0xFE, StrBuf, MaxSize);
}