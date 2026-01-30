#pragma once

#include "lumyn/domain/event/Event.h"
#include "lumyn/domain/module/ModuleData.h"
#include "lumyn/domain/request/RequestType.h"
#include "lumyn/packed.h"

namespace lumyn::internal {
namespace Response {
PACK(struct ResponseStatusInfo { Eventing::Status status; });
PACK(struct ResponseProductSKUInfo { uint16_t sku; });
PACK(struct ResponseProductSerialNumberInfo { uint64_t serialNumber; });
PACK(struct ResponseConfigHashInfo { uint8_t hash[16]; });
PACK(struct ResponseAssignedIdInfo {
  uint8_t valid;
  char id[24];
});
PACK(struct ResponseVersionInfo {
  uint8_t major;
  uint8_t minor;
  uint8_t patch;
});
PACK(struct ResponseHandshakeInfo {
  ResponseStatusInfo status;
  ResponseProductSKUInfo sku;
  ResponseProductSerialNumberInfo serNumber;
  ResponseConfigHashInfo configHash;
  ResponseAssignedIdInfo assignedId;
  ResponseVersionInfo version;
});

PACK(struct ResponseFaultsInfo { uint32_t faultFlags; });
PACK(struct ResponseModuleStatusInfo {
  uint16_t moduleId;
  uint8_t status;
});

PACK(struct ResponseLEDChannelStatusInfo { uint16_t channelId; });
PACK(struct ResponseLEDZoneStatusInfo { uint16_t zoneId; });
PACK(struct ResponseLatestEventInfo { Eventing::EventType eventType; });
PACK(struct ResponseEventFlagsInfo { uint32_t eventFlags; });

PACK(struct ResponseConfigFullInfo {
  uint32_t configSize;
  // Variable-length config data follows
  uint8_t* data;
});

// Compact header-only response; payload parsed separately based on type.
PACK(struct ResponseHeader {
  Request::RequestType type;
  // Should match the incoming Request's ID
  uint32_t id;
});

PACK(union ResponseData {
  ResponseHandshakeInfo handshake;
  ResponseStatusInfo status;
  ResponseProductSKUInfo productSku;
  ResponseProductSerialNumberInfo productSerialNumber;
  ResponseConfigHashInfo configHash;
  ResponseAssignedIdInfo assignedId;
  ResponseFaultsInfo faults;
  ResponseModuleStatusInfo moduleStatus;
  ModuleData::ModuleDataUnitHeader moduleData;
  ResponseLEDChannelStatusInfo ledChannelStatus;
  ResponseLEDZoneStatusInfo ledZoneStatus;
  ResponseLatestEventInfo latestEvent;
  ResponseEventFlagsInfo eventFlags;
});

PACK(struct Response {
  ResponseHeader header;
  ResponseData data;
});
}  // namespace Response

}  // namespace lumyn::internal