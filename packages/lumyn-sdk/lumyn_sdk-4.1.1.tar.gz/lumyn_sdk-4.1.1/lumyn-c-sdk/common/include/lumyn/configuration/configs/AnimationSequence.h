#pragma once

#include <string>
#include <vector>

#include "lumyn/configuration/configs/Animation.h"

namespace lumyn::internal::Configuration
{

  struct AnimationSequence
  {
    std::string id;
    std::vector<Animation> steps;
  };

} // namespace lumyn::internal::Configuration
