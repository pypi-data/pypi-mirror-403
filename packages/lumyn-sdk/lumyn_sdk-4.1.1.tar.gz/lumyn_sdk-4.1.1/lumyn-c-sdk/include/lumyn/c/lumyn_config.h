/**
 * @file lumyn_config.h
 * @brief Configuration parsing utilities
 *
 * This header contains functions for parsing and querying device configuration
 * returned as JSON from Lumyn devices.
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // Configuration Parsing
  // =============================================================================

  /**
   * @brief Parse JSON configuration string into a structured configuration object.
   * @param json Pointer to JSON string (not null-terminated, use json_len)
   * @param json_len Length of JSON string in bytes
   * @param out_config Output pointer to parsed configuration (must be freed with lumyn_FreeConfig)
   * @return LUMYN_OK on success, LUMYN_ERR_PARSE on JSON parsing failure, LUMYN_ERR_INVALID_ARGUMENT on NULL pointers
   */
  LUMYN_SDK_API lumyn_error_t lumyn_ParseConfig(
      const char *json,
      size_t json_len,
      lumyn_config_t **out_config);

  /**
   * @brief Free a parsed configuration object.
   * @param config Configuration object to free (safe to call with NULL)
   */
  LUMYN_SDK_API void lumyn_FreeConfig(lumyn_config_t *config);

  // =============================================================================
  // Configuration Queries
  // =============================================================================

  /**
   * @brief Get the number of channels in a configuration.
   * @param config Configuration object
   * @return Number of channels, or 0 if config is NULL
   */
  LUMYN_SDK_API int lumyn_ConfigGetChannelCount(const lumyn_config_t *config);

  /**
   * @brief Get a channel by index.
   * @param config Configuration object
   * @param index Channel index (0-based)
   * @return Pointer to channel, or NULL if index is out of bounds or config is NULL
   */
  LUMYN_SDK_API const lumyn_channel_t *lumyn_ConfigGetChannel(
      const lumyn_config_t *config,
      int index);

  // =============================================================================
  // Channel Queries
  // =============================================================================

  /**
   * @brief Get the ID of a channel.
   * @param channel Channel object
   * @return Channel ID string, or NULL if channel is NULL
   */
  LUMYN_SDK_API const char *lumyn_ChannelGetId(const lumyn_channel_t *channel);

  /**
   * @brief Get the number of zones in a channel.
   * @param channel Channel object
   * @return Number of zones, or 0 if channel is NULL
   */
  LUMYN_SDK_API int lumyn_ChannelGetZoneCount(const lumyn_channel_t *channel);

  /**
   * @brief Get a zone by index.
   * @param channel Channel object
   * @param index Zone index (0-based)
   * @return Pointer to zone, or NULL if index is out of bounds or channel is NULL
   */
  LUMYN_SDK_API const lumyn_zone_t *lumyn_ChannelGetZone(
      const lumyn_channel_t *channel,
      int index);

  // =============================================================================
  // Module Queries
  // =============================================================================

  /**
   * @brief Get the number of modules (sensors) in a configuration.
   * @param config Configuration object
   * @return Number of modules, or 0 if config is NULL
   */
  LUMYN_SDK_API int lumyn_ConfigGetModuleCount(const lumyn_config_t *config);

  /**
   * @brief Get a module by index.
   * @param config Configuration object
   * @param index Module index (0-based)
   * @return Pointer to module, or NULL if index is out of bounds or config is NULL
   */
  LUMYN_SDK_API const lumyn_module_t *lumyn_ConfigGetModule(
      const lumyn_config_t *config,
      int index);

  /**
   * @brief Get the ID of a module.
   * @param module Module object
   * @return Module ID string, or NULL if module is NULL
   */
  LUMYN_SDK_API const char *lumyn_ModuleGetId(const lumyn_module_t *module);

  /**
   * @brief Get the type of a module.
   * @param module Module object
   * @return Module type string, or NULL if module is NULL
   */
  LUMYN_SDK_API const char *lumyn_ModuleGetType(const lumyn_module_t *module);

  /**
   * @brief Get the polling rate of a module in milliseconds.
   * @param module Module object
   * @return Polling rate in ms, or 0 if module is NULL
   */
  LUMYN_SDK_API uint16_t lumyn_ModuleGetPollingRateMs(const lumyn_module_t *module);

  /**
   * @brief Get the connection type of a module.
   * @param module Module object
   * @return Connection type enum, or LUMYN_MODULE_CONNECTION_I2C if module is NULL
   */
  LUMYN_SDK_API lumyn_module_connection_type_t lumyn_ModuleGetConnectionType(const lumyn_module_t *module);

  // =============================================================================
  // Zone Queries
  // =============================================================================

  /**
   * @brief Get the ID of a zone.
   * @param zone Zone object
   * @return Zone ID string, or NULL if zone is NULL
   */
  LUMYN_SDK_API const char *lumyn_ZoneGetId(const lumyn_zone_t *zone);

  /**
   * @brief Get the number of LEDs in a zone.
   * @param zone Zone object
   * @return Number of LEDs, or 0 if zone is NULL
   */
  LUMYN_SDK_API int lumyn_ZoneGetLedCount(const lumyn_zone_t *zone);

  // =============================================================================
  // Configuration Application
  // =============================================================================

  /**
   * @brief Apply configuration JSON to a connected device.
   * @param inst Device instance
   * @param json Pointer to JSON string (not null-terminated, use json_len)
   * @param json_len Length of JSON string in bytes
   * @return LUMYN_OK on success, LUMYN_ERR_NOT_CONNECTED if not connected, LUMYN_ERR_INVALID_ARGUMENT on NULL pointers
   */
  LUMYN_SDK_API lumyn_error_t lumyn_ApplyConfig(
      cx_base_t *inst,
      const char *json,
      size_t json_len);

#ifdef __cplusplus
} // extern "C"
#endif
