/**
 * @file lumyn_modules_typed.h
 * @brief Typed module helper parsers for common sensors
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  typedef struct lumyn_digital_input_payload
  {
    uint8_t state; // 0 = LOW, non-zero = HIGH
  } lumyn_digital_input_payload_t;

  typedef struct lumyn_analog_input_payload
  {
    uint16_t raw_value;
    uint32_t scaled_value;
  } lumyn_analog_input_payload_t;

  typedef struct lumyn_vl53l1x_payload
  {
    uint8_t valid;
    uint16_t dist_mm;
  } lumyn_vl53l1x_payload_t;

  static inline bool lumyn_ParseDigitalInputPayload(const uint8_t *data, size_t len, lumyn_digital_input_payload_t *out)
  {
    if (!out)
      return false;
    out->state = 0;
    if (!data || len < 1)
      return false;
    out->state = data[0];
    return true;
  }

  static inline bool lumyn_ParseAnalogInputPayload(const uint8_t *data, size_t len, lumyn_analog_input_payload_t *out)
  {
    if (!out)
      return false;
    out->raw_value = 0;
    out->scaled_value = 0;
    if (!data || len < 2)
      return false;
    out->raw_value = (uint16_t)((data[0] & 0xFF) | ((data[1] & 0xFF) << 8));
    if (len >= 6)
    {
      out->scaled_value = (uint32_t)((data[2] & 0xFF) |
                                     ((data[3] & 0xFF) << 8) |
                                     ((data[4] & 0xFF) << 16) |
                                     ((data[5] & 0xFF) << 24));
    }
    return true;
  }

  static inline bool lumyn_ParseVL53L1XPayload(const uint8_t *data, size_t len, lumyn_vl53l1x_payload_t *out)
  {
    if (!out)
      return false;
    out->valid = 0;
    out->dist_mm = 0;
    if (!data || len < 3)
      return false;
    out->valid = data[0];
    out->dist_mm = (uint16_t)((data[1] & 0xFF) | ((data[2] & 0xFF) << 8));
    return true;
  }

#ifdef __cplusplus
} // extern "C"
#endif
