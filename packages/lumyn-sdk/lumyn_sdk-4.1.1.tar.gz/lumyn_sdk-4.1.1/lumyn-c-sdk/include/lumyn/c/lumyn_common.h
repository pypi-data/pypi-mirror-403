/**
 * @file lumyn_common.h
 * @brief Common types, macros, and error codes for the Lumyn SDK
 *
 * This header contains foundational types and macros used throughout the SDK,
 * including export macros, error codes, device handle types, and callback types.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#include <lumyn/sdk_version.h>
#include <lumyn/version.h>

#include <lumyn/types/animation.h>
#include <lumyn/types/color.h>
#include <lumyn/types/status.h>
#include <lumyn/types/events.h>
#include <lumyn/types/led_command.h>
#include <lumyn/types/config.h>

// =============================================================================
// Export Macros
// =============================================================================

#if defined(_WIN32) || defined(__CYGWIN__)
#if defined(LUMYN_SDK_BUILDING)
#define LUMYN_SDK_API __declspec(dllexport)
#else
#define LUMYN_SDK_API __declspec(dllimport)
#endif
#else
#if defined(__GNUC__) && __GNUC__ >= 4
#define LUMYN_SDK_API __attribute__((visibility("default")))
#else
#define LUMYN_SDK_API
#endif
#endif

// =============================================================================
// Memory Allocation Macros
// =============================================================================

#ifndef LUMYN_SDK_MALLOC
#define LUMYN_SDK_MALLOC malloc
#endif

#ifndef LUMYN_SDK_FREE
#define LUMYN_SDK_FREE free
#endif

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // Forward Declarations
  // =============================================================================

  typedef struct lumyn_serial_io lumyn_serial_io_t;

  // =============================================================================
  // Callback Types
  // =============================================================================

  typedef void (*lumyn_event_callback_t)(lumyn_event_t *evt, void *user);
  typedef void (*lumyn_module_data_callback_t)(const char *module_id, const uint8_t *data, size_t len, void *user);

  // =============================================================================
  // Error Codes
  // =============================================================================

  typedef enum lumyn_error
  {
    LUMYN_OK = 0,                   /**< Success */
    LUMYN_ERR_INVALID_ARGUMENT = 1, /**< Invalid argument provided */
    LUMYN_ERR_INVALID_HANDLE = 2,   /**< Invalid handle */
    LUMYN_ERR_NOT_CONNECTED = 3,    /**< Device not connected */
    LUMYN_ERR_TIMEOUT = 4,          /**< Operation timed out */
    LUMYN_ERR_IO = 5,               /**< I/O error */
    LUMYN_ERR_INTERNAL = 6,         /**< Internal error */
    LUMYN_ERR_NOT_SUPPORTED = 7,    /**< Operation not supported */
    LUMYN_ERR_PARSE = 8,            /**< Parse error */
  } lumyn_error_t;

  LUMYN_SDK_API const char *Lumyn_ErrorString(lumyn_error_t error);

  // =============================================================================
  // Version Information
  // =============================================================================

  /**
   * @brief Get the SDK version string at runtime
   * @return SDK version string (e.g., "4.1.0")
   * @note The major version matches the protocol version for firmware compatibility
   */
  LUMYN_SDK_API const char *lumyn_GetVersion(void);

  /**
   * @brief Get the SDK major version number
   * @return Major version number (matches protocol version for compatibility)
   */
  LUMYN_SDK_API int lumyn_GetVersionMajor(void);

  /**
   * @brief Get the SDK minor version number
   * @return Minor version number
   */
  LUMYN_SDK_API int lumyn_GetVersionMinor(void);

  /**
   * @brief Get the SDK patch version number
   * @return Patch version number
   */
  LUMYN_SDK_API int lumyn_GetVersionPatch(void);

  // =============================================================================
  // Connection Status
  // =============================================================================

  typedef struct lumyn_connection_status
  {
    bool connected; /**< Whether the device is connected */
    bool enabled;   /**< Whether the device is enabled */
  } lumyn_connection_status_t;

  // =============================================================================
  // Device Handle Types
  // =============================================================================

  /**
   * @brief Base device handle structure.
   *
   * This is the base type for all device handles. Functions that work with
   * any device type accept cx_base_t*. You can cast cx_t* or cx_animate_t*
   * to cx_base_t* using the LUMYN_BASE_PTR macro.
   */
  typedef struct
  {
    void *_internal;                           /**< Internal implementation pointer */
    const struct lumyn_device_vtable *_vtable; /**< Virtual function table */
  } cx_base_t;

  /**
   * @brief ConnectorX device handle.
   */
  typedef struct
  {
    cx_base_t base;
  } cx_t;

  /**
   * @brief ConnectorX Animate device handle.
   */
  typedef struct
  {
    cx_base_t base;
  } cx_animate_t;

  // =============================================================================
  // Utility Macros
  // =============================================================================

#define LUMYN_BASE_PTR(inst) ((cx_base_t *)(inst))
#define LUMYN_BASE_PTR_CONST(inst) ((const cx_base_t *)(inst))

  // =============================================================================
  // Memory Management
  // =============================================================================

  /**
   * @brief Free strings allocated by SDK functions that return heap-allocated strings.
   * @param str String to free
   * @note Currently used by lumyn_RequestConfigAlloc().
   */
  LUMYN_SDK_API void lumyn_FreeString(char *str);

#ifdef __cplusplus
} // extern "C"
#endif
