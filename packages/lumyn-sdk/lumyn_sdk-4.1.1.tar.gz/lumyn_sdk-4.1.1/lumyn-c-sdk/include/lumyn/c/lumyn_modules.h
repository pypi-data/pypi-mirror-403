/**
 * @file lumyn_modules.h
 * @brief Module registration and data retrieval
 *
 * This header contains functions for registering external modules with
 * Lumyn devices and retrieving data from them.
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // Module Registration
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_RegisterModule(cx_base_t *inst, const char *module_id, lumyn_module_data_callback_t cb, void *user);
  LUMYN_SDK_API lumyn_error_t lumyn_UnregisterModule(cx_base_t *inst, const char *module_id);

  // =============================================================================
  // Module Data Retrieval
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_GetLatestData(cx_base_t *inst, const char *module_id, void *out, size_t size);

  // =============================================================================
  // Module Polling
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_SetModulePollingEnabled(cx_base_t *inst, bool enabled);
  LUMYN_SDK_API lumyn_error_t lumyn_PollModules(cx_base_t *inst);

#ifdef __cplusplus
} // extern "C"
#endif
