#include "lumyn/cpp/ConfigManager.h"
#include <lumyn/cpp/device/BaseLumynDevice.hpp>
#include "../../c_abi/internal/DeviceInternalBase.hpp"

#include <cstring>

namespace lumyn
{
  namespace managers
  {

    ConfigManager::ConfigManager(cx_base_t *base) : base_(base) {}

    lumyn_error_t ConfigManager::RequestConfig(std::string &out_json, uint32_t timeout_ms)
    {
      if (!base_ || !base_->_internal)
        return LUMYN_ERR_INVALID_ARGUMENT;

      auto *device = dynamic_cast<lumyn::internal::BaseLumynDevice *>(
          static_cast<lumyn_c_sdk::internal::DeviceInternalBase *>(base_->_internal));
      if (!device)
        return LUMYN_ERR_INVALID_ARGUMENT;

      if (device->RequestConfig(out_json, static_cast<int>(timeout_ms)))
      {
        return LUMYN_OK;
      }
      return LUMYN_ERR_TIMEOUT;
    }

    lumyn_error_t ConfigManager::RequestConfigAlloc(char **out, uint32_t timeout_ms)
    {
      if (!base_ || !out)
        return LUMYN_ERR_INVALID_ARGUMENT;

      std::string json;
      lumyn_error_t res = RequestConfig(json, timeout_ms);
      if (res != LUMYN_OK)
        return res;

      *out = static_cast<char *>(LUMYN_SDK_MALLOC(json.size() + 1));
      if (!*out)
        return LUMYN_ERR_INTERNAL;

      std::memcpy(*out, json.data(), json.size());
      (*out)[json.size()] = '\0';

      return LUMYN_OK;
    }

    lumyn_error_t ConfigManager::SetConfig(const std::string &config_json)
    {
      if (!base_ || config_json.empty())
        return LUMYN_ERR_INVALID_ARGUMENT;
      return lumyn_ApplyConfig(base_, config_json.c_str(), config_json.size());
    }

  } // namespace managers
} // namespace lumyn
