#pragma once

#include <cstdint>

#include "lumyn/cpp/modules/ModuleBase.hpp"

namespace lumyn::modules
{
  struct VL53L1XPayload
  {
    uint8_t valid{0};
    uint16_t dist_mm{0};
  };

  // Header-only module - no DLL export needed
  class VL53L1XModule : public ModuleBase<VL53L1XPayload>
  {
  public:
    VL53L1XModule(lumyn::device::ConnectorX &device, std::string module_id)
        : ModuleBase<VL53L1XPayload>(device, std::move(module_id))
    {
    }

  protected:
    VL53L1XPayload Parse(const ModuleDataEntry &entry) override
    {
      VL53L1XPayload payload{};
      if (entry.data.size() >= 3)
      {
        payload.valid = entry.data[0];
        payload.dist_mm = static_cast<uint16_t>((entry.data[1] & 0xFF) |
                                                ((entry.data[2] & 0xFF) << 8));
      }
      return payload;
    }
  };

} // namespace lumyn::modules
