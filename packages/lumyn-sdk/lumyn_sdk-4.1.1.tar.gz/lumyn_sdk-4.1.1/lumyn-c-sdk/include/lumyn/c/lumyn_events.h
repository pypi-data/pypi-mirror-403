/**
 * @file lumyn_events.h
 * @brief Event handling and callbacks
 *
 * This header contains functions for registering event handlers and
 * retrieving events from Lumyn devices.
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // Event Handler Registration
  // =============================================================================

  /**
   * @brief Register a callback for events.
   * @param inst Device instance
   * @param cb Callback function
   * @param user User-provided context pointer
   * @return LUMYN_OK on success
   * @note extra_message is only valid for the duration of the callback.
   */
  LUMYN_SDK_API lumyn_error_t lumyn_AddEventHandler(cx_base_t *inst, lumyn_event_callback_t cb, void *user);

  // =============================================================================
  // Event Retrieval
  // =============================================================================

  /**
   * @brief Get latest event (if any).
   * @param inst Device instance
   * @param evt Output event structure
   * @return LUMYN_OK if an event is available
   * @note extra_message is valid until the next call to lumyn_GetLatestEvent()/lumyn_GetEvents()
   *       on the same thread.
   */
  LUMYN_SDK_API lumyn_error_t lumyn_GetLatestEvent(cx_base_t *inst, lumyn_event_t *evt);

  /**
   * @brief Get buffered events (if any).
   * @param inst Device instance
   * @param arr Array to receive events
   * @param max_count Maximum number of events to retrieve
   * @param out_count Output pointer to receive actual count
   * @return LUMYN_OK on success
   * @note extra_message is valid until the next call to lumyn_GetLatestEvent()/lumyn_GetEvents()
   *       on the same thread.
   */
  LUMYN_SDK_API lumyn_error_t lumyn_GetEvents(cx_base_t *inst, lumyn_event_t *arr, int max_count, int *out_count);

#ifdef __cplusplus
} // extern "C"
#endif
