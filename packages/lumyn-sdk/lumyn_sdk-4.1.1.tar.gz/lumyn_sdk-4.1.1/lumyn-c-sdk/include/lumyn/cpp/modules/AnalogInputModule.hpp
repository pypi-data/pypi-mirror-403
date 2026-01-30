#pragma once

#include <cstdint>

#include "lumyn/cpp/modules/ModuleBase.hpp"

namespace lumyn::modules
{
  struct AnalogInputPayload
  {
    uint16_t raw_value{0};
    uint32_t scaled_value{0};
  };

  // Header-only module - no DLL export needed
  class AnalogInputModule : public ModuleBase<AnalogInputPayload>
  {
  public:
    AnalogInputModule(lumyn::device::ConnectorX &device, std::string module_id)
        : ModuleBase<AnalogInputPayload>(device, std::move(module_id))
    {
    }

  protected:
    AnalogInputPayload Parse(const ModuleDataEntry &entry) override
    {
      AnalogInputPayload payload{};
      if (entry.data.size() >= 2)
      {
        payload.raw_value = static_cast<uint16_t>((entry.data[0] & 0xFF) |
                                                  ((entry.data[1] & 0xFF) << 8));
      }
      if (entry.data.size() >= 6)
      {
        payload.scaled_value = static_cast<uint32_t>((entry.data[2] & 0xFF) |
                                                     ((entry.data[3] & 0xFF) << 8) |
                                                     ((entry.data[4] & 0xFF) << 16) |
                                                     ((entry.data[5] & 0xFF) << 24));
      }
      return payload;
    }
  };

} // namespace lumyn::modules
