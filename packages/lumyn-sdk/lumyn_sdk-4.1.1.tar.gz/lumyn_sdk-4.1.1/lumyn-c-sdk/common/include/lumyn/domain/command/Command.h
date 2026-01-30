#pragma once

#include "lumyn/domain/command/CommandType.h"
#include "lumyn/domain/command/led/LEDCommandType.h"
#include "lumyn/domain/command/system/SystemCommandType.h"
#include "lumyn/packed.h"

namespace lumyn::internal::Command
{
  PACK(struct CommandHeader {
    CommandType type;
    union
    {
      LED::LEDCommandType ledType;
      System::SystemCommandType systemType;
    };
  });
};