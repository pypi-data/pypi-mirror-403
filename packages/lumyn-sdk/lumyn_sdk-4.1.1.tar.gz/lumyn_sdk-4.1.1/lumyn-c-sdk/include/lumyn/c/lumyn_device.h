/**
 * @file lumyn_device.h
 * @brief Device creation, destruction, and connection management
 *
 * This header contains functions for creating and managing Lumyn device instances,
 * as well as connection and status functions.
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // Device Creation and Destruction
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_CreateConnectorX(cx_t *inst);
  LUMYN_SDK_API lumyn_error_t lumyn_CreateConnectorXAlloc(cx_t **out_inst);
  LUMYN_SDK_API lumyn_error_t lumyn_CreateConnectorXAnimate(cx_animate_t *inst);
  LUMYN_SDK_API lumyn_error_t lumyn_CreateConnectorXAnimateAlloc(cx_animate_t **out_inst);

  /**
   * @brief Destroy a ConnectorX instance and release all internal resources.
   * @param inst Instance to destroy
   * @note Disconnects if connected.
   */
  LUMYN_SDK_API void lumyn_DestroyConnectorX(cx_t *inst);

  /**
   * @brief Destroy a heap-allocated ConnectorX instance and free the handle.
   * @param inst Instance to destroy and free
   */
  LUMYN_SDK_API void lumyn_DestroyConnectorXAlloc(cx_t *inst);

  /**
   * @brief Destroy a ConnectorX Animate instance and release all internal resources.
   * @param inst Instance to destroy
   * @note Disconnects if connected.
   */
  LUMYN_SDK_API void lumyn_DestroyConnectorXAnimate(cx_animate_t *inst);

  /**
   * @brief Destroy a heap-allocated ConnectorX Animate instance and free the handle.
   * @param inst Instance to destroy and free
   */
  LUMYN_SDK_API void lumyn_DestroyConnectorXAnimateAlloc(cx_animate_t *inst);

  // =============================================================================
  // Connection Management
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_Connect(cx_base_t *inst, const char *port);
  LUMYN_SDK_API lumyn_error_t lumyn_ConnectWithBaud(cx_base_t *inst, const char *port, int baud_rate);
  LUMYN_SDK_API lumyn_error_t lumyn_Disconnect(cx_base_t *inst);

  LUMYN_SDK_API lumyn_error_t lumyn_ConnectIO_internal(cx_base_t *inst, const lumyn_serial_io_t *io);
  LUMYN_SDK_API bool lumyn_IsConnected(cx_base_t *inst);

  // =============================================================================
  // Status and Health
  // =============================================================================

  /**
   * @brief Get current connectivity and enablement status.
   * @param inst Device instance
   * @return Connection status structure
   */
  LUMYN_SDK_API lumyn_connection_status_t lumyn_GetCurrentStatus(cx_base_t *inst);

  /**
   * @brief Get current device health status.
   * @param inst Device instance
   * @return Device health status
   */
  LUMYN_SDK_API lumyn_status_t lumyn_GetDeviceHealth(cx_base_t *inst);

  LUMYN_SDK_API void lumyn_SetConnectionStateCallback(cx_base_t *inst, void (*cb)(bool connected, void *user), void *user);

  // =============================================================================
  // Device Configuration and Control
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_RequestConfig(cx_base_t *inst, char *out, size_t *size, uint32_t timeout_ms);
  LUMYN_SDK_API lumyn_error_t lumyn_RequestConfigAlloc(cx_base_t *inst, char **out, uint32_t timeout_ms);
  LUMYN_SDK_API void lumyn_RestartDevice(cx_base_t *inst, uint32_t delay_ms);

#ifdef __cplusplus
} // extern "C"
#endif
