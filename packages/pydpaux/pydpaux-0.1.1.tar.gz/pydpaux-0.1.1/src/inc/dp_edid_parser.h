#ifndef _DP_EDID_PARSER_H
#define _DP_EDID_PARSER_H
#if defined(__cplusplus)
#pragma once
#endif
#if defined(__cplusplus)
extern "C" {
#endif

#include <stdint.h>

#define EDID_MAX_SIZE 256   //must be multiple of 16
#define EDID_MAX_TEXT_DESCRIPTOR_LENGTH  13

void edidPrintAll(const uint8_t *data);
bool edidReformat(uint8_t *data);
bool edidFindSerialNumber(const uint8_t *data, char *StrBuf, uint16_t MaxSize);
bool edidFindMonitorName(const uint8_t *data, char *StrBuf, uint16_t MaxSize);
bool edidFindUnspeficiedText(const uint8_t *data, char *StrBuf, uint16_t MaxSize);

#if defined(__cplusplus)
} // extern "C"
#endif

#endif // _DP_EDID_PARSER_H