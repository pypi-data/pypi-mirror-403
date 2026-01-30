#pragma once

#include <cinttypes>

#include "RequestType.h"
#include "lumyn/packed.h"

namespace lumyn::internal::Request
{
  PACK(struct RequestHandshakeInfo {
    HostConnectionSource hostSource;
  });
  PACK(struct RequestStatusInfo{});
  PACK(struct RequestProductSKUInfo{});
  PACK(struct RequestProductSerialNumberInfo{});
  PACK(struct RequestConfigHashInfo{});
  PACK(struct RequestAssignedIdInfo{});
  PACK(struct RequestFaultsInfo{});
  PACK(struct RequestModuleStatusInfo {
    uint16_t moduleId;
  });
  PACK(struct RequestModuleDataInfo {
    uint16_t moduleId;
  });
  PACK(struct RequestLEDChannelStatusInfo {
    uint16_t channelId;
  });
  PACK(struct RequestLEDZoneStatusInfo {
    uint16_t zoneId;
  });
  PACK(struct RequestLatestEventInfo{});
  PACK(struct RequestEventFlagsInfo{});
  PACK(struct RequestConfigFullInfo {});

  PACK(union RequestData {
    RequestHandshakeInfo handshake;
    RequestStatusInfo status;
    RequestProductSKUInfo productSku;
    RequestProductSerialNumberInfo productSerialNumber;
    RequestConfigHashInfo configHash;
    RequestAssignedIdInfo assignedId;
    RequestFaultsInfo faults;
    RequestModuleStatusInfo moduleStatus;
    RequestModuleDataInfo moduleData;
    RequestLEDChannelStatusInfo ledChannelStatus;
    RequestLEDZoneStatusInfo ledZoneStatus;
    RequestLatestEventInfo latestEvent;
    RequestEventFlagsInfo eventFlags;
    RequestConfigFullInfo configFull;
  });

  // Compact header-only request; payload parsed separately based on type.
  PACK(struct RequestHeader {
    RequestType type;
    // Randomized request ID to correlate with the Response
    uint32_t id;
  });

  PACK(struct Request {
    RequestHeader header;
    RequestData data;
  });
} // namespace lumyn::internal::Request