#pragma once

#include "Files.h"
#include "FileType.h"
#include <vector>
#include <cstdint>
#include <cstring>

namespace lumyn::internal::Files
{
  class FilesBuilder
  {
  public:
    /**
     * Build file transmission buffer: FilesHeader + bytes
     */
    static std::vector<uint8_t> build(FileType type, uint32_t fileSize, const void* headerData, size_t headerSize, const uint8_t* bytes, size_t bytesLength);

    /**
     * Build Transfer file transmission
     */
    static std::vector<uint8_t> buildTransfer(const char* path, const uint8_t* bytes, size_t bytesLength);

    /**
     * Build SendConfig file transmission
     */
    static std::vector<uint8_t> buildSendConfig(const uint8_t* bytes, size_t bytesLength);

    /**
     * Build SetPixelBuffer file transmission
     */
    static std::vector<uint8_t> buildSetPixelBuffer(uint16_t zoneId, uint16_t zoneLength, const uint8_t* bytes, size_t bytesLength);
  };
} // namespace lumyn::internal::Files

