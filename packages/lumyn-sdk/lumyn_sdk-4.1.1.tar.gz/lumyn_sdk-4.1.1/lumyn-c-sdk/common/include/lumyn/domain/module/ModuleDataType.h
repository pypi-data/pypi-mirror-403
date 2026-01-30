#pragma once

#include <stdint.h>

namespace lumyn::internal::ModuleData
{
  enum class ModuleDataType : uint8_t
  {
    NewData = 0,
    PushData,
  };
} // namespace lumyn::internal::ModuleData