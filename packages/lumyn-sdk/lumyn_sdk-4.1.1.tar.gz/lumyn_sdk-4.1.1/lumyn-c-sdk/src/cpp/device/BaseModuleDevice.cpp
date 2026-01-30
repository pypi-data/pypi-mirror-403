#include "lumyn/cpp/device/BaseModuleDevice.hpp"
#include "lumyn/cpp/device/BaseLumynDevice.hpp"
#include "lumyn/util/hashing/IDCreator.h"

namespace lumyn::internal
{
  lumyn_error_t BaseModuleDevice::GetLatestModuleData(std::string_view module_id, std::vector<uint8_t>& out)
  {
    if (module_id.empty())
    {
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    // Get the module ID hash
    const uint16_t moduleKey = lumyn::internal::IDCreator::createId(module_id);
    
    // Get base device pointer
    auto* base = GetModuleBasePtr();
    if (!base)
    {
      return LUMYN_ERR_INVALID_HANDLE;
    }

    // Retrieve module data from base device
    std::vector<std::vector<uint8_t>> moduleData;
    if (!base->GetModuleDataByHash(moduleKey, moduleData))
    {
      // No data available for this module (treat as timeout/not found)
      return LUMYN_ERR_TIMEOUT;
    }

    // Return the data from the first (and should be only) entry
    if (!moduleData.empty())
    {
      out = std::move(moduleData[0]);
      return LUMYN_OK;
    }

    return LUMYN_ERR_TIMEOUT;
  }

  void BaseModuleDevice::RegisterModule(std::string_view module_id, std::function<void(const std::vector<uint8_t>&)> callback)
  {
    std::string key(module_id);
    module_callbacks_[key] = std::make_unique<std::function<void(const std::vector<uint8_t>&)>>(std::move(callback));
  }

  void BaseModuleDevice::SetModulePollingEnabled(bool enabled)
  {
    module_polling_enabled_ = enabled;
  }

  void BaseModuleDevice::PollModules()
  {
    if (!module_polling_enabled_)
    {
      return;
    }

    // Iterate through all registered modules and invoke their callbacks with latest data
    for (const auto& [module_id, callback] : module_callbacks_)
    {
      if (callback)
      {
        std::vector<uint8_t> data;
        if (GetLatestModuleData(module_id, data) == LUMYN_OK)
        {
          (*callback)(data);
        }
      }
    }
  }

  void BaseModuleDevice::InvokeModuleCallback(std::string_view module_id, const std::vector<uint8_t>& data)
  {
    std::string key(module_id);
    auto it = module_callbacks_.find(key);
    if (it != module_callbacks_.end() && it->second)
    {
      (*it->second)(data);
    }
  }
}
