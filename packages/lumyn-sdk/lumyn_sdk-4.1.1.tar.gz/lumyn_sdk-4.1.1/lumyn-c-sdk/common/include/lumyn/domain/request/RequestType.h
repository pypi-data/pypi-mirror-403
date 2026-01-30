#pragma once
#include <cinttypes>

namespace lumyn::internal::Request
{
  enum class RequestType : uint8_t
  {
    Handshake = 0,
    Status,
    ProductSKU,
    ProductSerialNumber,
    ConfigHash,
    AssignedId,
    Faults,
    ModuleStatus,
    ModuleData,
    LEDChannelStatus,
    LEDZoneStatus,
    LatestEvent,
    EventFlags,
    ConfigFull,
  };

  enum class HostConnectionSource : uint8_t
  {
    Unknown = 0,
    Studio,
    Roborio,
    LumynSDK,
  };
}; // namespace lumyn::internal::Request