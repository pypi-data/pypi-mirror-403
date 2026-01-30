#pragma once

#include <cstdint>

#include "./SystemCommandType.h"
#include "lumyn/packed.h"

namespace lumyn::internal::Command {
namespace System {
PACK(struct ClearStatusFlagData { uint32_t mask; });

PACK(struct SetAssignedIdData { char id[24]; });

PACK(struct RestartDeviceData { uint16_t delayMs; });

PACK(union SystemCommandData {
  ClearStatusFlagData clearStatusFlag;
  SetAssignedIdData assignedId;
  RestartDeviceData restartDevice;
});

PACK(struct SystemCommand {
  SystemCommandType type;
  SystemCommandData data;
});
}  // namespace System
}  // namespace lumyn::internal::Command