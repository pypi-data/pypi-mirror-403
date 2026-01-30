#pragma once

#include <lumyn/cpp/builder_base.hpp>
#include <lumyn/cpp/device/ILEDDevice.hpp>
#include <lumyn/cpp/export.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/led/BuiltInAnimations.h>

#include <string>
#include <string_view>
#include <optional>
#include <stdexcept>
#include <chrono>

namespace lumyn
{
  namespace device
  {

    /**
     * Builder for setting LED animations with a fluent API.
     */
    class LUMYN_SDK_CPP_API AnimationBuilder : public lumyn::BuilderBase<AnimationBuilder>
    {
    public:
      AnimationBuilder(const lumyn::internal::ILEDDevice &device, lumyn::led::Animation animation)
          : _device(&device), _animation(animation)
      {
        _color = defaultColor(animation);
        _delay = defaultDelay(animation);
      }

      AnimationBuilder &ForZone(std::string_view zoneId)
      {
        return this->setZone(zoneId);
      }

      AnimationBuilder &ForGroup(std::string_view groupId)
      {
        return this->setGroup(groupId);
      }

      AnimationBuilder &WithColor(lumyn_color_t color)
      {
        this->checkNotExecuted();
        _color = color;
        return *this;
      }

      AnimationBuilder &WithDelay(std::chrono::milliseconds delay)
      {
        this->checkNotExecuted();
        _delay = delay;
        return *this;
      }

      // Overload for plain integer milliseconds
      AnimationBuilder &WithDelay(uint32_t delayMs)
      {
        return WithDelay(std::chrono::milliseconds(delayMs));
      }

      AnimationBuilder &Reverse(bool reversed)
      {
        this->checkNotExecuted();
        _reversed = reversed;
        return *this;
      }

      AnimationBuilder &RunOnce(bool oneShot)
      {
        this->checkNotExecuted();
        _oneShot = oneShot;
        execute();
        return *this;
      }

      void execute() override;

      // Getter methods for testing/inspection
      lumyn_color_t GetColor() const { return _color; }
      uint32_t GetDelayMs() const { return static_cast<uint32_t>(_delay.count()); }
      bool IsReversed() const { return _reversed; }
      bool IsOneShot() const { return _oneShot; }
      lumyn::led::Animation GetAnimation() const { return _animation; }
      const std::optional<std::string> &GetZoneId() const { return this->getZoneId(); }
      const std::optional<std::string> &GetGroupId() const { return this->getGroupId(); }

      static lumyn_color_t defaultColor(lumyn::led::Animation animation);
      static std::chrono::milliseconds defaultDelay(lumyn::led::Animation animation)
      {
        const auto *instance = lumyn::led::GetAnimationInstance(animation);
        if (instance)
        {
          return std::chrono::milliseconds(instance->defaultDelay);
        }
        // Fallback to default delay (250ms) - hardcoded to avoid private Constants.h dependency
        return std::chrono::milliseconds(250);
      }

    private:
      const lumyn::internal::ILEDDevice *_device;
      lumyn::led::Animation _animation;
      lumyn_color_t _color{255, 255, 255};
      std::chrono::milliseconds _delay{50};
      bool _reversed{false};
      bool _oneShot{false};
    };
  }
}
