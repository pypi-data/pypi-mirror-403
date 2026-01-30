#pragma once

#include <lumyn/cpp/export.hpp>
#include "../../../../include/lumyn/c/lumyn_sdk.h"

#include <cstdint>
#include <functional>
#include <string_view>
#include <vector>

namespace lumyn::internal
{
  /**
   * @brief Interface for devices with module support
   *
   * Provides methods for getting module data and registering module callbacks.
   */
  class LUMYN_SDK_CPP_API IModuleDevice
  {
  public:
    virtual ~IModuleDevice() = default;

    /**
     * @brief Get the latest data from a specific module
     * @param module_id The identifier of the module
     * @param out Vector to store the retrieved data
     * @return LUMYN_OK on success, LUMYN_* error values on failure.
     */
    virtual lumyn_error_t GetLatestModuleData(std::string_view module_id, std::vector<uint8_t> &out) = 0;

    /**
     * @brief Register a callback for a specific module
     * @param module_id The identifier of the module
     * @param callback Function to be called when module data is available
     */
    virtual void RegisterModule(std::string_view module_id, std::function<void(const std::vector<uint8_t> &)> callback) = 0;

    /**
     * @brief Enable or disable automatic module polling
     * @param enabled true to enable polling, false to disable
     */
    virtual void SetModulePollingEnabled(bool enabled) = 0;

    /**
     * @brief Manually poll all registered modules once
     */
    virtual void PollModules() = 0;
  };
}
