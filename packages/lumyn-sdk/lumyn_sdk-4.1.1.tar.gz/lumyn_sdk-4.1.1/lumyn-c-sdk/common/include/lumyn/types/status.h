/**
 * @file status.h
 * @brief C-compatible device status type definitions
 */
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Device status codes
 */
typedef enum lumyn_status {
  LUMYN_STATUS_UNKNOWN = -1,
  LUMYN_STATUS_BOOTING = 0,
  LUMYN_STATUS_ACTIVE = 1,
  LUMYN_STATUS_ERROR = 2,
  LUMYN_STATUS_FATAL = 3,
} lumyn_status_t;

#ifdef __cplusplus
} // extern "C"

#endif // __cplusplus

