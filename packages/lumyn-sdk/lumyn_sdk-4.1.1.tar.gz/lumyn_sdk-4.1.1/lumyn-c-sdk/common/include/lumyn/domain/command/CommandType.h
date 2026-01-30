#pragma once

#include <cstdint>

namespace lumyn::internal::Command {
enum class CommandType : uint8_t { System = 0, LED, Device };
}