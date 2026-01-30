#pragma once

#include <functional>
#include <chrono>
#include <string_view>
#include <lumyn/types/animation.h>

// Forward declarations
namespace lumyn::internal {
  namespace Command::LED { class LEDCommand; struct AnimationColor; }
}

using namespace std::chrono_literals;

namespace lumyn::internal {
  class LEDCommander
  {
  public:
    LEDCommander(std::function<void(Command::LED::LEDCommand &)> handler) : _cmdHandler{handler} {}

    Command::LED::LEDCommand SetColor(std::string_view, Command::LED::AnimationColor) const;
    Command::LED::LEDCommand SetGroupColor(std::string_view, Command::LED::AnimationColor) const;
    Command::LED::LEDCommand SetAnimation(std::string_view, led::Animation,
                                          Command::LED::AnimationColor, std::chrono::milliseconds delay = 250ms,
                                          bool reversed = false, bool oneShot = false) const;
    Command::LED::LEDCommand SetGroupAnimation(std::string_view, led::Animation,
                                               Command::LED::AnimationColor, std::chrono::milliseconds delay = 250ms,
                                               bool reversed = false, bool oneShot = false) const;
    Command::LED::LEDCommand SetAnimationSequence(std::string_view, std::string_view) const;
    Command::LED::LEDCommand SetGroupAnimationSequence(std::string_view, std::string_view) const;

  private:
    std::function<void(Command::LED::LEDCommand &)> _cmdHandler;
  };
}
