#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace lumyn::internal::Configuration
{

  enum class BitmapType
  {
    Static = 0,
    Animated,
  };

  struct Bitmap
  {
    std::string id;
    BitmapType type = BitmapType::Static;
    std::optional<std::string> path;
    std::optional<std::string> folder;
    std::optional<uint16_t> frameDelay;
  };

} // namespace lumyn::internal::Configuration
