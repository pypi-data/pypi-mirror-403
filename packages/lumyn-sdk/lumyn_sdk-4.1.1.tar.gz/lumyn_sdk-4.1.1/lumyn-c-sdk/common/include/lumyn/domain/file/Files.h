#pragma once

#include <cinttypes>

#include "FileType.h"
#include "lumyn/packed.h"

namespace lumyn::internal::Files
{
  // Payload definitions remain for separate parsing:
  PACK(struct FileTransferInfoHeader { char path[32]; });
  PACK(struct SendConfigInfoHeader{});
  PACK(struct SetZonePixelBuffer { uint16_t zoneId; uint16_t zoneLength; });

  PACK(union FilesInfo {
    FileTransferInfoHeader fileTransfer;
    SendConfigInfoHeader sendConfig;
    SetZonePixelBuffer setZonePixels;
  });

  PACK(struct FilesHeader {
    FileType type;
    uint32_t fileSize;
    FilesInfo info;
  });

  PACK(struct Files {
    FilesHeader header;
    uint8_t *bytes;  // Variable-length payload parsed according to `header.type`
  });
} // namespace lumyn::internal::Files