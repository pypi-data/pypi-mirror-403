#pragma once

#include <lumyn/cpp/export.hpp>
#include "lumyn/cpp/device/IModuleDevice.hpp"

#include <unordered_map>
#include <string>
#include <memory>
#include <functional>
#include <vector>
#include <cstdint>

// Forward declaration
namespace lumyn::internal
{
  class BaseLumynDevice;
}

namespace lumyn::internal
{
  /**
   * @brief Base class for devices with module support
   *
   * Implements IModuleDevice with an unordered_map for efficient module callback lookup.
   * Provides full implementation of module data retrieval and callback management.
   */
  class LUMYN_SDK_CPP_API BaseModuleDevice : public IModuleDevice
  {
  public:
    BaseModuleDevice() = default;
    virtual ~BaseModuleDevice() = default;

    // Non-copyable due to unique_ptr members
    BaseModuleDevice(const BaseModuleDevice &) = delete;
    BaseModuleDevice &operator=(const BaseModuleDevice &) = delete;
    BaseModuleDevice(BaseModuleDevice &&) = default;
    BaseModuleDevice &operator=(BaseModuleDevice &&) = default;

    // IModuleDevice implementation - these are fully implemented
    lumyn_error_t GetLatestModuleData(std::string_view module_id, std::vector<uint8_t> &out) override;
    void RegisterModule(std::string_view module_id, std::function<void(const std::vector<uint8_t> &)> callback) override;
    void SetModulePollingEnabled(bool enabled) override;
    void PollModules() override;

  protected:
    /**
     * @brief Get the base device pointer for accessing module data
     * Subclasses must implement this to provide their device instance
     */
    virtual BaseLumynDevice *GetModuleBasePtr() = 0;
    virtual const BaseLumynDevice *GetModuleBasePtr() const = 0;

    /**
     * @brief Invoke registered callback for a module
     */
    void InvokeModuleCallback(std::string_view module_id, const std::vector<uint8_t> &data);

    /**
     * @brief Check if module polling is enabled
     */
    bool IsModulePollingEnabled() const { return module_polling_enabled_; }

  private:
    // Use unordered_map for O(1) module callback lookup
    std::unordered_map<std::string, std::unique_ptr<std::function<void(const std::vector<uint8_t> &)>>> module_callbacks_;
    bool module_polling_enabled_{false};
  };
}
