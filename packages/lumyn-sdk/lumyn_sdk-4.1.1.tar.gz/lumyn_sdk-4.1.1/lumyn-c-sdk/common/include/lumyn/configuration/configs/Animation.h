#pragma once

#include <optional>
#include <string>
#include <string_view>

#include "lumyn/domain/Color.h"
#include "lumyn/domain/command/led/LEDCommand.h"

namespace lumyn::internal::Configuration
{
  struct Animation
  {
    std::string id;
    bool reversed;
    uint16_t delay;
    std::optional<lumyn::internal::domain::Color> color;
    std::optional<uint8_t> repeatCount;
  };
} // namespace lumyn::internal::Configuration