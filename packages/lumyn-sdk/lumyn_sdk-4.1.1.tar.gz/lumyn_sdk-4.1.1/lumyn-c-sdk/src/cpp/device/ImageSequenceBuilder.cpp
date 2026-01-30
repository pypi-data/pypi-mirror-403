#include "lumyn/cpp/device/builder/ImageSequenceBuilder.hpp"
#include "lumyn/cpp/led/LEDCommander.hpp"
#include "lumyn/domain/command/led/LEDCommand.h"
#include "lumyn/cpp/device/ILEDDevice.hpp"

namespace lumyn {
namespace device {

void ImageSequenceBuilder::execute()
{
  if (this->isExecuted()) return;

  this->validateTarget();

  if (this->hasZone()) {
    _device->GetLEDCommander().SetAnimationSequence(this->getZoneId().value(), _sequenceId);
  } else {
    _device->GetLEDCommander().SetGroupAnimationSequence(this->getGroupId().value(), _sequenceId);
  }

  this->markExecuted();
}

} // namespace device
} // namespace lumyn
