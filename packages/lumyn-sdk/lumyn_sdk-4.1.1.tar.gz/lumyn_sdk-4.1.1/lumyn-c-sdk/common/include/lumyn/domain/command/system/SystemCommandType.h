#pragma once

#include <cinttypes>

namespace lumyn::internal::Command
{
  namespace System
  {
    enum class SystemCommandType : uint8_t
    {
      ClearStatusFlag = 0,
      SetAssignedId,
      RestartDevice,
    };
  }
} // namespace lumyn::internal::Command