#pragma once

#include <functional>
#include <chrono>
#include <string_view>
#include <vector>
#include <cstdint>
#include <lumyn/types/led_command.h>
#include <lumyn/types/animation.h>

// Forward declarations
namespace lumyn::internal {
  namespace Command::LED { class LEDCommand; struct AnimationColor; }
}

using namespace std::chrono_literals;

namespace lumyn::internal {
  class MatrixCommander
  {
  public:
    MatrixCommander(std::function<void(Command::LED::LEDCommand &)> handler) : _cmdHandler{handler} {}

    Command::LED::LEDCommand SetMatrixColor(Command::LED::AnimationColor) const;
    Command::LED::LEDCommand SetMatrixAnimation(led::Animation, bool oneShot = false) const;
    Command::LED::LEDCommand SetBitmap(std::string_view, std::string_view, Command::LED::AnimationColor,
                                       bool setColor = false, bool oneShot = false) const;
    Command::LED::LEDCommand SetGroupBitmap(std::string_view, std::string_view, Command::LED::AnimationColor,
                                            bool setColor = false, bool oneShot = false) const;
    Command::LED::LEDCommand SetText(std::string_view, std::string_view, Command::LED::AnimationColor,
                                     Command::LED::MatrixTextScrollDirection = Command::LED::MatrixTextScrollDirection::LEFT,
                                     std::chrono::milliseconds delayMs = 500ms, bool oneShot = false) const;
    Command::LED::LEDCommand SetText(std::string_view, std::string_view, Command::LED::AnimationColor,
                                     Command::LED::MatrixTextScrollDirection,
                                     std::chrono::milliseconds delayMs, bool oneShot,
                                     Command::LED::AnimationColor bgColor,
                                     Command::LED::MatrixTextFont font,
                                     Command::LED::MatrixTextAlign align,
                                     Command::LED::MatrixTextFlags flags,
                                     int8_t yOffset) const;
    Command::LED::LEDCommand SetGroupText(std::string_view, std::string_view, Command::LED::AnimationColor,
                                          Command::LED::MatrixTextScrollDirection = Command::LED::MatrixTextScrollDirection::LEFT,
                                          std::chrono::milliseconds delayMs = 500ms, bool oneShot = false) const;
    Command::LED::LEDCommand SetGroupText(std::string_view, std::string_view, Command::LED::AnimationColor,
                                          Command::LED::MatrixTextScrollDirection,
                                          std::chrono::milliseconds delayMs, bool oneShot,
                                          Command::LED::AnimationColor bgColor,
                                          Command::LED::MatrixTextFont font,
                                          Command::LED::MatrixTextAlign align,
                                          Command::LED::MatrixTextFlags flags,
                                          int8_t yOffset) const;

  private:
    std::function<void(Command::LED::LEDCommand &)> _cmdHandler;
  };
}
