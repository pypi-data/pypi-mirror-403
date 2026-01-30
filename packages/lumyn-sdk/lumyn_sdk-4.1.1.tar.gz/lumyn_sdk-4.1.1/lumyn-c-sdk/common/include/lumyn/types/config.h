#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Opaque types for configuration structures
typedef struct lumyn_config lumyn_config_t;
typedef struct lumyn_channel lumyn_channel_t;
typedef struct lumyn_zone lumyn_zone_t;
typedef struct lumyn_module lumyn_module_t;

typedef enum lumyn_module_connection_type
{
  LUMYN_MODULE_CONNECTION_I2C = 0,
  LUMYN_MODULE_CONNECTION_SPI = 1,
  LUMYN_MODULE_CONNECTION_UART = 2,
  LUMYN_MODULE_CONNECTION_DIO = 3,
  LUMYN_MODULE_CONNECTION_AIO = 4
} lumyn_module_connection_type_t;

#ifdef __cplusplus
} // extern "C"
#endif
