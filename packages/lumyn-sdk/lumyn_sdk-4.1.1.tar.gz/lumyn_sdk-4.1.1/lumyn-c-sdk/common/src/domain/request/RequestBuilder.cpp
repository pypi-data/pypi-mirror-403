#include "lumyn/domain/request/RequestBuilder.h"
#include <cstring>

namespace lumyn::internal::Request
{
  std::vector<uint8_t> RequestBuilder::build(RequestType type, uint32_t id, const void* bodyStruct, size_t bodySize)
  {
    RequestHeader header;
    header.type = type;
    header.id = id;

    std::vector<uint8_t> buffer;
    buffer.reserve(sizeof(RequestHeader) + bodySize);
    buffer.assign(reinterpret_cast<const uint8_t*>(&header), reinterpret_cast<const uint8_t*>(&header) + sizeof(RequestHeader));
    
    if (bodyStruct && bodySize > 0)
    {
      buffer.insert(buffer.end(), reinterpret_cast<const uint8_t*>(bodyStruct), reinterpret_cast<const uint8_t*>(bodyStruct) + bodySize);
    }

    return buffer;
  }

  std::vector<uint8_t> RequestBuilder::buildHandshake(uint32_t id, HostConnectionSource hostSource)
  {
    RequestHandshakeInfo body;
    body.hostSource = hostSource;
    return build(RequestType::Handshake, id, &body, sizeof(RequestHandshakeInfo));
  }

  std::vector<uint8_t> RequestBuilder::buildStatus(uint32_t id)
  {
    return build(RequestType::Status, id);
  }

  std::vector<uint8_t> RequestBuilder::buildProductSKU(uint32_t id)
  {
    return build(RequestType::ProductSKU, id);
  }

  std::vector<uint8_t> RequestBuilder::buildProductSerialNumber(uint32_t id)
  {
    return build(RequestType::ProductSerialNumber, id);
  }

  std::vector<uint8_t> RequestBuilder::buildConfigHash(uint32_t id)
  {
    return build(RequestType::ConfigHash, id);
  }

  std::vector<uint8_t> RequestBuilder::buildAssignedId(uint32_t id)
  {
    return build(RequestType::AssignedId, id);
  }

  std::vector<uint8_t> RequestBuilder::buildFaults(uint32_t id)
  {
    return build(RequestType::Faults, id);
  }

  std::vector<uint8_t> RequestBuilder::buildConfigFull(uint32_t id)
  {
    return build(RequestType::ConfigFull, id);
  }

  std::vector<uint8_t> RequestBuilder::buildModuleStatus(uint32_t id, uint16_t moduleId)
  {
    RequestModuleStatusInfo body;
    body.moduleId = moduleId;
    return build(RequestType::ModuleStatus, id, &body, sizeof(RequestModuleStatusInfo));
  }

  std::vector<uint8_t> RequestBuilder::buildModuleData(uint32_t id, uint16_t moduleId)
  {
    RequestModuleDataInfo body;
    body.moduleId = moduleId;
    return build(RequestType::ModuleData, id, &body, sizeof(RequestModuleDataInfo));
  }

  std::vector<uint8_t> RequestBuilder::buildLEDChannelStatus(uint32_t id, uint16_t channelId)
  {
    RequestLEDChannelStatusInfo body;
    body.channelId = channelId;
    return build(RequestType::LEDChannelStatus, id, &body, sizeof(RequestLEDChannelStatusInfo));
  }

  std::vector<uint8_t> RequestBuilder::buildLEDZoneStatus(uint32_t id, uint16_t zoneId)
  {
    RequestLEDZoneStatusInfo body;
    body.zoneId = zoneId;
    return build(RequestType::LEDZoneStatus, id, &body, sizeof(RequestLEDZoneStatusInfo));
  }

  std::vector<uint8_t> RequestBuilder::buildLatestEvent(uint32_t id)
  {
    return build(RequestType::LatestEvent, id);
  }

  std::vector<uint8_t> RequestBuilder::buildEventFlags(uint32_t id)
  {
    return build(RequestType::EventFlags, id);
  }
} // namespace lumyn::internal::Request

