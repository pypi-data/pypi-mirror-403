#pragma once

#include <array>
#include <optional>
#include <string>
#include <vector>

#include "configs/AnimationGroup.h"
#include "configs/AnimationSequence.h"
#include "configs/Bitmap.h"
#include "configs/Channel.h"
#include "configs/Network.h"
#include "configs/Module.h"

namespace lumyn::internal::Configuration
{

  struct LumynConfiguration
  {
    std::array<uint8_t, 16> md5;
    std::optional<std::string> teamNumber;
    Network network;
    std::optional<std::vector<Channel>> channels;
    std::optional<std::vector<AnimationSequence>> sequences;
    std::optional<std::vector<Bitmap>> bitmaps;
    std::optional<std::vector<AnimationGroup>> animationGroups;
    std::optional<std::vector<Module>> sensors;
  };

} // namespace lumyn::internal::Configuration