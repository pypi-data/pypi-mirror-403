#pragma once

#include <cstdint>

#include "lumyn/cpp/modules/ModuleBase.hpp"

namespace lumyn::modules
{
  struct DigitalInputPayload
  {
    uint8_t state{0};
  };

  // Header-only module - no DLL export needed
  class DigitalInputModule : public ModuleBase<DigitalInputPayload>
  {
  public:
    DigitalInputModule(lumyn::device::ConnectorX &device, std::string module_id)
        : ModuleBase<DigitalInputPayload>(device, std::move(module_id))
    {
    }

  protected:
    DigitalInputPayload Parse(const ModuleDataEntry &entry) override
    {
      DigitalInputPayload payload{};
      if (!entry.data.empty())
      {
        payload.state = entry.data[0];
      }
      return payload;
    }
  };

} // namespace lumyn::modules
