#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "Zone.h"

namespace lumyn::internal::Configuration
{

  struct Channel
  {
    std::string key;
    std::string id;
    uint16_t length;
    std::optional<uint8_t> brightness;
    std::vector<Zone> zones;
  };

} // namespace lumyn::internal::Configuration