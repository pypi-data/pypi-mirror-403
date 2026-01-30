/**
 * @file events.h
 * @brief C-compatible event type definitions
 * 
 * This header defines event types and structures that work in both C and C++.
 */
#pragma once

#include <stdint.h>
#include "status.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Event type identifiers (bitmask values)
 */
typedef enum lumyn_event_type {
  LUMYN_EVENT_BEGIN_INITIALIZATION = 0x00,
  LUMYN_EVENT_FINISH_INITIALIZATION = 0x01 << 0,
  LUMYN_EVENT_ENABLED = 0x01 << 1,
  LUMYN_EVENT_DISABLED = 0x01 << 2,
  LUMYN_EVENT_CONNECTED = 0x01 << 3,
  LUMYN_EVENT_DISCONNECTED = 0x01 << 4,
  LUMYN_EVENT_ERROR = 0x01 << 5,
  LUMYN_EVENT_FATAL_ERROR = 0x01 << 6,
  LUMYN_EVENT_REGISTERED_ENTITY = 0x01 << 7,
  LUMYN_EVENT_CUSTOM = 0x01 << 8,
  LUMYN_EVENT_PIN_INTERRUPT = 0x01 << 9,
  LUMYN_EVENT_HEARTBEAT = 0x01 << 10,
  LUMYN_EVENT_OTA = 0x01 << 11,
  LUMYN_EVENT_MODULE = 0x01 << 12,
} lumyn_event_type_t;

/**
 * @brief Cause of device being disabled
 */
typedef enum lumyn_disabled_cause {
  LUMYN_DISABLED_NO_HEARTBEAT = 0,
  LUMYN_DISABLED_MANUAL = 1,
  LUMYN_DISABLED_ESTOP = 2,
  LUMYN_DISABLED_RESTART = 3,
} lumyn_disabled_cause_t;

/**
 * @brief Connection type identifiers
 */
typedef enum lumyn_connection_type {
  LUMYN_CONNECTION_USB = 0,
  LUMYN_CONNECTION_WEBUSB = 1,
  LUMYN_CONNECTION_I2C = 2,
  LUMYN_CONNECTION_CAN = 3,
  LUMYN_CONNECTION_UART = 4,
} lumyn_connection_type_t;

/**
 * @brief Non-fatal error type identifiers
 */
typedef enum lumyn_error_type {
  LUMYN_ERROR_FILE_NOT_FOUND = 0,
  LUMYN_ERROR_INVALID_FILE = 1,
  LUMYN_ERROR_ENTITY_NOT_FOUND = 2,
  LUMYN_ERROR_DEVICE_MALFUNCTION = 3,
  LUMYN_ERROR_QUEUE_FULL = 4,
  LUMYN_ERROR_LED_STRIP = 5,
  LUMYN_ERROR_LED_MATRIX = 6,
  LUMYN_ERROR_INVALID_ANIMATION_SEQUENCE = 7,
  LUMYN_ERROR_INVALID_CHANNEL = 8,
  LUMYN_ERROR_DUPLICATE_ID = 9,
  LUMYN_ERROR_INVALID_CONFIG_UPLOAD = 10,
  LUMYN_ERROR_MODULE = 11,
} lumyn_error_type_t;

/**
 * @brief Fatal error type identifiers
 */
typedef enum lumyn_fatal_error_type {
  LUMYN_FATAL_INIT_ERROR = 0,
  LUMYN_FATAL_BAD_CONFIG = 1,
  LUMYN_FATAL_START_TASK = 2,
  LUMYN_FATAL_CREATE_QUEUE = 3,
} lumyn_fatal_error_type_t;

// ---------------------------
// Event info structures
// ---------------------------

typedef struct lumyn_disabled_info {
  lumyn_disabled_cause_t cause;
} lumyn_disabled_info_t;

typedef struct lumyn_connected_info {
  lumyn_connection_type_t type;
} lumyn_connected_info_t;

typedef struct lumyn_disconnected_info {
  lumyn_connection_type_t type;
} lumyn_disconnected_info_t;

typedef struct lumyn_error_info {
  lumyn_error_type_t type;
  char message[32];  // Extended from 16 for C API usability
} lumyn_error_info_t;

typedef struct lumyn_fatal_error_info {
  lumyn_fatal_error_type_t type;
  char message[32];  // Extended from 16 for C API usability
} lumyn_fatal_error_info_t;

typedef struct lumyn_registered_entity_info {
  int32_t id;
} lumyn_registered_entity_info_t;

typedef struct lumyn_custom_info {
  uint8_t type;
  uint8_t data[16];
  uint8_t length;
} lumyn_custom_info_t;

typedef struct lumyn_pin_interrupt_info {
  uint8_t pin;
} lumyn_pin_interrupt_info_t;

typedef struct lumyn_heartbeat_info {
  lumyn_status_t status;
  uint8_t enabled;
  uint8_t connected_usb;
  uint8_t can_ok;
} lumyn_heartbeat_info_t;

/**
 * @brief Complete event structure
 */
typedef struct lumyn_event {
  lumyn_event_type_t type;
  union {
    lumyn_disabled_info_t disabled;
    lumyn_connected_info_t connected;
    lumyn_disconnected_info_t disconnected;
    lumyn_error_info_t error;
    lumyn_fatal_error_info_t fatal_error;
    lumyn_registered_entity_info_t registered_entity;
    lumyn_custom_info_t custom;
    lumyn_pin_interrupt_info_t pin_interrupt;
    lumyn_heartbeat_info_t heartbeat;
  } data;
  char* extra_message;  // Caller must free if non-NULL
} lumyn_event_t;

#ifdef __cplusplus
} // extern "C"

#endif // __cplusplus

