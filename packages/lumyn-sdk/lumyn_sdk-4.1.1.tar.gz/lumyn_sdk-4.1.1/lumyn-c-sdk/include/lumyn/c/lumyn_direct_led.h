/**
 * @file lumyn_direct_led.h
 * @brief DirectLED API for high-performance LED control
 *
 * This header contains the DirectLED API, which provides optimized LED control
 * using delta compression to minimize data transfer. The DirectLED system
 * automatically tracks changes and only sends modified LED data to the device.
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // DirectLED Types
  // =============================================================================

  /**
   * @brief Opaque handle to a DirectLED instance
   */
  typedef struct lumyn_direct_led lumyn_direct_led_t;

  // =============================================================================
  // DirectLED Lifecycle
  // =============================================================================

  /**
   * @brief Create a DirectLED controller for a zone.
   * @param inst Device instance (ConnectorX or ConnectorXAnimate)
   * @param zone_id Zone identifier string
   * @param num_leds Number of LEDs in the zone
   * @param full_refresh_interval How often to force a full refresh (0 to disable, default 100)
   * @param out_handle Output pointer to receive the DirectLED handle
   * @return LUMYN_OK on success
   */
  LUMYN_SDK_API lumyn_error_t lumyn_DirectLEDCreate(
      cx_base_t *inst,
      const char *zone_id,
      size_t num_leds,
      int full_refresh_interval,
      lumyn_direct_led_t **out_handle);

  /**
   * @brief Destroy a DirectLED instance and free resources.
   * @param handle DirectLED handle (safe to call with NULL)
   */
  LUMYN_SDK_API void lumyn_DirectLEDDestroy(lumyn_direct_led_t *handle);

  // =============================================================================
  // DirectLED Update Functions
  // =============================================================================

  /**
   * @brief Update LEDs with an array of colors. Uses delta compression automatically.
   * @param handle DirectLED handle
   * @param colors Array of lumyn_color_t (must have at least num_leds elements)
   * @param count Number of colors in the array
   * @return LUMYN_OK on success
   */
  LUMYN_SDK_API lumyn_error_t lumyn_DirectLEDUpdate(
      lumyn_direct_led_t *handle,
      const lumyn_color_t *colors,
      size_t count);

  /**
   * @brief Update LEDs with raw RGB byte data. Uses delta compression automatically.
   * @param handle DirectLED handle
   * @param rgb_data Raw RGB bytes (3 bytes per LED: R, G, B)
   * @param length Number of bytes (must be num_leds * 3)
   * @return LUMYN_OK on success
   */
  LUMYN_SDK_API lumyn_error_t lumyn_DirectLEDUpdateRaw(
      lumyn_direct_led_t *handle,
      const uint8_t *rgb_data,
      size_t length);

  /**
   * @brief Force a full update (no delta compression).
   * @param handle DirectLED handle
   * @param colors Array of lumyn_color_t
   * @param count Number of colors in the array
   * @return LUMYN_OK on success
   */
  LUMYN_SDK_API lumyn_error_t lumyn_DirectLEDForceFullUpdate(
      lumyn_direct_led_t *handle,
      const lumyn_color_t *colors,
      size_t count);

  /**
   * @brief Force a full update with raw RGB data.
   * @param handle DirectLED handle
   * @param rgb_data Raw RGB bytes
   * @param length Number of bytes
   * @return LUMYN_OK on success
   */
  LUMYN_SDK_API lumyn_error_t lumyn_DirectLEDForceFullUpdateRaw(
      lumyn_direct_led_t *handle,
      const uint8_t *rgb_data,
      size_t length);

  // =============================================================================
  // DirectLED Control
  // =============================================================================

  /**
   * @brief Reset the internal buffer state. Forces next update to be full.
   * @param handle DirectLED handle
   */
  LUMYN_SDK_API void lumyn_DirectLEDReset(lumyn_direct_led_t *handle);

  /**
   * @brief Set the full refresh interval.
   * @param handle DirectLED handle
   * @param interval Number of updates between full refreshes (0 to disable)
   */
  LUMYN_SDK_API void lumyn_DirectLEDSetRefreshInterval(lumyn_direct_led_t *handle, int interval);

  // =============================================================================
  // DirectLED Information
  // =============================================================================

  /**
   * @brief Get the number of LEDs this DirectLED controls.
   * @param handle DirectLED handle
   * @return Number of LEDs, or 0 if handle is invalid
   */
  LUMYN_SDK_API size_t lumyn_DirectLEDGetLength(const lumyn_direct_led_t *handle);

  /**
   * @brief Get the zone ID this DirectLED controls.
   * @param handle DirectLED handle
   * @return Zone ID string, or NULL if handle is invalid
   */
  LUMYN_SDK_API const char *lumyn_DirectLEDGetZoneId(const lumyn_direct_led_t *handle);

  /**
   * @brief Check if the DirectLED was successfully initialized.
   * @param handle DirectLED handle
   * @return true if initialized
   */
  LUMYN_SDK_API bool lumyn_DirectLEDIsInitialized(const lumyn_direct_led_t *handle);

#ifdef __cplusplus
} // extern "C"
#endif
