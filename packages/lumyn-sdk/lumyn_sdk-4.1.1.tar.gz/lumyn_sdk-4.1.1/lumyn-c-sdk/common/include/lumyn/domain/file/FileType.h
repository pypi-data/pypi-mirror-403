#pragma once

#include <cinttypes>

namespace lumyn::internal::Files
{
  enum class FileType : uint8_t
  {
    Transfer = 0,
    SendConfig,
    SetPixelBuffer
  };
} // namespace lumyn::internal::Files