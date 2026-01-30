#pragma once

#include <string>
#include <vector>

namespace lumyn::internal::Configuration
{

  struct AnimationGroup
  {
    std::string id;
    std::vector<std::string> zoneIds;
  };

} // namespace lumyn::internal::Configuration
