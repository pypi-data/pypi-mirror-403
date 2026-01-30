#pragma once

#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "lumyn/cpp/export.hpp"
#include "lumyn/cpp/connectorXVariant/BaseConnectorXVariant.hpp"
#include "lumyn/cpp/device/BaseModuleDevice.hpp"

namespace lumyn::modules
{
  class ModuleDataDispatcher;
}

namespace lumyn::device {

/**
 * @brief ConnectorX device with full LED and module support
 *
 * Inherits shared functionality from BaseConnectorXVariant.
 * Adds module support via BaseModuleDevice.
 */
class LUMYN_SDK_CPP_API ConnectorX 
  : public BaseConnectorXVariant,
    public internal::BaseModuleDevice {
public:
  ConnectorX();
  ~ConnectorX() override;

  // Internal accessors required by BaseModuleDevice
  internal::BaseLumynDevice* GetModuleBasePtr() override;
  const internal::BaseLumynDevice* GetModuleBasePtr() const override;

  ConnectorX(const ConnectorX&) = delete;
  ConnectorX& operator=(const ConnectorX&) = delete;
  ConnectorX(ConnectorX&&) = delete;
  ConnectorX& operator=(ConnectorX&&) = delete;

  // SetAutoPollEvents - override to also control module polling
  ConnectorX& SetAutoPollEvents(bool enabled);

  // RestartDevice - ConnectorX-specific
  void RestartDevice(uint32_t delay_ms = 0);

  // Module data - simplified to raw bytes (from BaseModuleDevice)
  using internal::BaseModuleDevice::GetLatestModuleData;
  using internal::BaseModuleDevice::RegisterModule;
  using internal::BaseModuleDevice::SetModulePollingEnabled;
  using internal::BaseModuleDevice::PollModules;
  
  // Module dispatcher accessor
  ::lumyn::modules::ModuleDataDispatcher& GetModuleDispatcher();

  // Connection state callback
  void SetConnectionStateCallback(std::function<void(bool)> callback);

  // Overrides from BaseLumynDevice
  void OnEvent(const internal::Eventing::Event &evt) override;
  void* GetBasePtr() override;
  const void* GetBasePtr() const override;

protected:
  // Hook from BaseConnectorXVariant for disconnect cleanup
  void OnDisconnect() override;

private:
  std::unique_ptr<std::function<void(bool)>> connection_callback_;
  std::unique_ptr<::lumyn::modules::ModuleDataDispatcher> module_dispatcher_;
};

} // namespace lumyn::device
