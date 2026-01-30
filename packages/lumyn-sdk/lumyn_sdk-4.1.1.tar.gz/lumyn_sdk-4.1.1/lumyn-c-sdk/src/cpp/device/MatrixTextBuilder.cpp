#include "lumyn/cpp/device/builder/MatrixTextBuilder.hpp"

#include "lumyn/cpp/led/MatrixCommander.hpp"
#include "lumyn/domain/command/led/LEDCommand.h"

#include <chrono>

namespace lumyn {
namespace device {

void MatrixTextBuilder::execute()
{
  if (this->isExecuted()) return;

  this->validateTarget();

  // Convert lumyn_color_t to lumyn::internal::Command::LED::AnimationColor
  lumyn::internal::Command::LED::AnimationColor animColor{_color.r, _color.g, _color.b};
  lumyn::internal::Command::LED::AnimationColor bgColor{_bgColor.r, _bgColor.g, _bgColor.b};
  // Convert C enum to C++ enum class
  auto dir = static_cast<lumyn::internal::Command::LED::MatrixTextScrollDirection>(_direction);
  auto font = static_cast<lumyn::internal::Command::LED::MatrixTextFont>(_font);
  auto align = static_cast<lumyn::internal::Command::LED::MatrixTextAlign>(_align);
  lumyn::internal::Command::LED::MatrixTextFlags flags{};
  flags.smoothScroll = _flags.smoothScroll ? 1 : 0;
  flags.showBackground = _flags.showBackground ? 1 : 0;
  flags.pingPong = _flags.pingPong ? 1 : 0;
  flags.noScroll = _flags.noScroll ? 1 : 0;

  if (this->hasZone()) {
    _device->GetMatrixCommander().SetText(this->getZoneId().value(), _text, animColor, dir,
                                          std::chrono::milliseconds(_delay.count()), _oneShot,
                                          bgColor, font, align, flags, _yOffset);
  } else {
    _device->GetMatrixCommander().SetGroupText(this->getGroupId().value(), _text, animColor, dir,
                                               std::chrono::milliseconds(_delay.count()), _oneShot,
                                               bgColor, font, align, flags, _yOffset);
  }

  this->markExecuted();
}

} // namespace device
} // namespace lumyn
