#include "lumyn/Constants.h"  // Required for BuiltInAnimations.h (included via AnimationBuilder.hpp)
#include "lumyn/cpp/device/builder/AnimationBuilder.hpp"

#include "lumyn/cpp/led/LEDCommander.hpp"
#include "lumyn/domain/command/led/LEDCommand.h"
#include "lumyn/c/lumyn_led.h"
#include "lumyn/c/lumyn_sdk.h"
#include "lumyn/cpp/connectorXVariant/ConnectorX.hpp"
#include "lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp"
#include "lumyn/led/BuiltInAnimations.h"

#include <chrono>

namespace lumyn {
namespace device {

void AnimationBuilder::execute()
{
  if (this->isExecuted()) {
    return;
  }

  this->validateTarget();

  const cx_base_t* c_base_ptr = nullptr;
  if (auto cx = dynamic_cast<const lumyn::device::ConnectorX*>(_device)) {
    c_base_ptr = cx->GetCBasePtr();
  } else if (auto cxa = dynamic_cast<const lumyn::device::ConnectorXAnimate*>(_device)) {
    c_base_ptr = cxa->GetCBasePtr();
  }

  if (c_base_ptr) {
    if (this->hasZone()) {
      lumyn_SetAnimation(const_cast<cx_base_t*>(c_base_ptr),
                         std::string(this->getZoneId().value()).c_str(),
                         _animation, _color,
                         static_cast<uint32_t>(_delay.count()),
                         _reversed, _oneShot);
    } else {
      lumyn_SetGroupAnimation(const_cast<cx_base_t*>(c_base_ptr),
                              std::string(this->getGroupId().value()).c_str(),
                              _animation, _color,
                              static_cast<uint32_t>(_delay.count()),
                              _reversed, _oneShot);
    }
  } else {
    lumyn::internal::Command::LED::AnimationColor animColor{_color.r, _color.g, _color.b};
    if (this->hasZone()) {
      _device->GetLEDCommander().SetAnimation(this->getZoneId().value(), _animation, animColor,
                                              std::chrono::milliseconds(_delay.count()),
                                              _reversed, _oneShot);
    } else {
      _device->GetLEDCommander().SetGroupAnimation(this->getGroupId().value(), _animation, animColor,
                                                   std::chrono::milliseconds(_delay.count()),
                                                   _reversed, _oneShot);
    }
  }

  this->markExecuted();
}

lumyn_color_t AnimationBuilder::defaultColor(lumyn::led::Animation animation)
{
  const auto* instance = lumyn::led::GetAnimationInstance(animation);
  if (instance) {
    return {instance->defaultColor.r, instance->defaultColor.g, instance->defaultColor.b};
  }
  // Fallback to default color (blue: {0, 0, 240}) - hardcoded to avoid private Constants.h dependency
  return {0, 0, 240};
}

} // namespace device
} // namespace lumyn
