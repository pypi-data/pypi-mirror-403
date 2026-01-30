#pragma once

#include <stddef.h>
#include <stdint.h>

#include "lumyn/c/lumyn_sdk.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Configuration structure for serial I/O operations
 * @param path Serial port path (e.g., "/dev/ttyACM0" on Linux, "COM3" on Windows)
 * @param baud Baud rate (common values: 9600, 19200, 38400, 57600, 115200). If <= 0, baud is not configured.
 * @param timeout_ms Poll timeout in milliseconds for manual updates. If < 0, uses default (100ms).
 * @param threaded If true, use background thread for polling; if false, requires manual updates via lumyn_serial_update()
 */
typedef struct lumyn_serial_io_cfg {
  const char* path;
  int baud;
  int timeout_ms;
  bool threaded;
} lumyn_serial_io_cfg_t;

/**
 * @brief Initializer for default serial config
 * @note baud value matches lumyn::internal::Constants::Serial::kDefaultBaudRate (115200)
 */
#define LUMYN_SERIAL_CFG_DEFAULT { \
  .path = NULL, \
  .baud = 115200, \
  .timeout_ms = 100, \
  .threaded = true \
}

typedef struct lumyn_serial_io {
  void (*write)(void* user, const uint8_t* data, size_t len);
  void (*write_bytes)(void* user, const uint8_t* data, size_t len);
  void (*set_read_callback)(void* user, void (*cb)(const uint8_t*, size_t, void*), void* cb_user);
  void (*close)(void* user);
  void* user;
} lumyn_serial_io_t;

// These helpers create a lumyn_serial_io_t suitable for internal use by the C++ API.
// When the SDK is compiled without the built-in serial backend, lumyn_serial_open()
// returns LUMYN_ERR_NOT_SUPPORTED.

/**
 * @brief Open a serial port and create a serial I/O vtable
 * @param cfg Configuration structure for the serial connection
 * @param out_io Output parameter for the serial I/O vtable
 * @return LUMYN_OK on success, error code on failure
 * @note The returned vtable must be closed with lumyn_serial_io_close()
 * @note On embedded targets, call lumyn_serial_update() periodically to process incoming data when threading is disabled
 * @warning This function is NOT thread-safe. Do not call concurrently with other serial functions.
 */
LUMYN_SDK_API lumyn_error_t lumyn_serial_open(const lumyn_serial_io_cfg_t* cfg, lumyn_serial_io_t* out_io);

/**
 * @brief Close a serial I/O vtable and release resources
 * @param io Serial I/O vtable to close
 * @warning This function is NOT thread-safe. Do not call concurrently with lumyn_serial_update().
 */
LUMYN_SDK_API void lumyn_serial_io_close(lumyn_serial_io_t* io);

/**
 * @brief Enable or disable background thread polling for serial I/O
 * @param io Serial I/O vtable
 * @param enable true to use background thread, false to require manual updates
 * @return LUMYN_OK on success, LUMYN_ERR_NOT_SUPPORTED if threading is not available on this platform
 * @note This overrides the threaded setting from the configuration struct
 * @note Disable threading on embedded targets without thread support, then call lumyn_serial_update()
 * @note Only available when the SDK is compiled with thread support
 */
#ifdef LUMYN_HAS_THREADS
LUMYN_SDK_API lumyn_error_t lumyn_serial_set_threaded(lumyn_serial_io_t* io, bool enable);
#else
#define lumyn_serial_set_threaded(io, enable) LUMYN_ERR_NOT_SUPPORTED
#endif

/**
 * @brief Manually update serial port to process incoming data (for embedded targets without threading)
 * @param io Serial I/O vtable
 * @return LUMYN_OK on success, error code on failure
 * @note Call this periodically from your main loop when threading is disabled
 * @note This function processes any pending incoming data and invokes registered callbacks
 * @note The poll timeout configured in lumyn_serial_io_cfg_t is used for blocking
 */
LUMYN_SDK_API lumyn_error_t lumyn_serial_update(lumyn_serial_io_t* io);

#ifdef __cplusplus
} // extern "C"
#endif
