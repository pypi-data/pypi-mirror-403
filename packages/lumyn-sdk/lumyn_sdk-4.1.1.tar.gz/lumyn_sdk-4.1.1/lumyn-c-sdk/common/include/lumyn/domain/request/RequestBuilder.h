#pragma once

#include "Request.h"
#include "RequestType.h"
#include <vector>
#include <cstdint>
#include <cstddef>

namespace lumyn::internal::Request
{
  class RequestBuilder
  {
  public:
    // Build a request buffer: RequestHeader + optional body struct
    static std::vector<uint8_t> build(RequestType type, uint32_t id, const void* bodyStruct = nullptr, size_t bodySize = 0);

    // Convenience methods for specific request types (return serialized buffers)
    static std::vector<uint8_t> buildHandshake(uint32_t id, HostConnectionSource hostSource);
    static std::vector<uint8_t> buildStatus(uint32_t id);
    static std::vector<uint8_t> buildProductSKU(uint32_t id);
    static std::vector<uint8_t> buildProductSerialNumber(uint32_t id);
    static std::vector<uint8_t> buildConfigHash(uint32_t id);
    static std::vector<uint8_t> buildAssignedId(uint32_t id);
    static std::vector<uint8_t> buildFaults(uint32_t id);
    static std::vector<uint8_t> buildConfigFull(uint32_t id);
    static std::vector<uint8_t> buildModuleStatus(uint32_t id, uint16_t moduleId);
    static std::vector<uint8_t> buildModuleData(uint32_t id, uint16_t moduleId);
    static std::vector<uint8_t> buildLEDChannelStatus(uint32_t id, uint16_t channelId);
    static std::vector<uint8_t> buildLEDZoneStatus(uint32_t id, uint16_t zoneId);
    static std::vector<uint8_t> buildLatestEvent(uint32_t id);
    static std::vector<uint8_t> buildEventFlags(uint32_t id);
  };
} // namespace lumyn::internal::Request

