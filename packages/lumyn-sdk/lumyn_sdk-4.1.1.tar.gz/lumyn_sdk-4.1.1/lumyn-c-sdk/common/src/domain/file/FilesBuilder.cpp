#include "lumyn/domain/file/FilesBuilder.h"
#include <cstring>

namespace lumyn::internal::Files
{
  std::vector<uint8_t> FilesBuilder::build(FileType type, uint32_t fileSize, const void* headerData, size_t headerSize, const uint8_t* bytes, size_t bytesLength)
  {
    FilesHeader header{};
    header.type = type;
    header.fileSize = fileSize;
    
    // Copy header-specific data into the union
    if (headerData && headerSize > 0)
    {
      std::memcpy(&header.info, headerData, headerSize);
    }

    std::vector<uint8_t> buffer;
    buffer.reserve(sizeof(FilesHeader) + bytesLength);
    buffer.assign(reinterpret_cast<const uint8_t*>(&header), reinterpret_cast<const uint8_t*>(&header) + sizeof(FilesHeader));
    
    if (bytes && bytesLength > 0)
    {
      buffer.insert(buffer.end(), bytes, bytes + bytesLength);
    }

    return buffer;
  }

  std::vector<uint8_t> FilesBuilder::buildTransfer(const char* path, const uint8_t* bytes, size_t bytesLength)
  {
    FileTransferInfoHeader info;
    if (path)
    {
      std::strncpy(info.path, path, sizeof(info.path) - 1);
      info.path[sizeof(info.path) - 1] = '\0';
    }
    else
    {
      info.path[0] = '\0';
    }

    return build(FileType::Transfer, static_cast<uint32_t>(bytesLength), &info, sizeof(FileTransferInfoHeader), bytes, bytesLength);
  }

  std::vector<uint8_t> FilesBuilder::buildSendConfig(const uint8_t* bytes, size_t bytesLength)
  {
    SendConfigInfoHeader info{};
    return build(FileType::SendConfig, static_cast<uint32_t>(bytesLength), &info, sizeof(SendConfigInfoHeader), bytes, bytesLength);
  }

  std::vector<uint8_t> FilesBuilder::buildSetPixelBuffer(uint16_t zoneId, uint16_t zoneLength, const uint8_t* bytes, size_t bytesLength)
  {
    SetZonePixelBuffer info;
    info.zoneId = zoneId;
    info.zoneLength = zoneLength;

    return build(FileType::SetPixelBuffer, static_cast<uint32_t>(bytesLength), &info, sizeof(SetZonePixelBuffer), bytes, bytesLength);
  }
} // namespace lumyn::internal::Files

