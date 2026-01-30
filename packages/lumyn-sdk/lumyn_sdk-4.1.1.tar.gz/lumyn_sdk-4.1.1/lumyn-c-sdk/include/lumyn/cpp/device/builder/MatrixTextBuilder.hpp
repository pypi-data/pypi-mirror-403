#pragma once

#include <lumyn/cpp/builder_base.hpp>
#include <lumyn/cpp/device/ILEDDevice.hpp>
#include <lumyn/cpp/export.hpp>
#include <lumyn/cpp/types.hpp>
#include <lumyn/c/lumyn_sdk.h>

#include <string>
#include <string_view>
#include <optional>
#include <stdexcept>
#include <chrono>
#include <cstdint>

namespace lumyn
{
  namespace device
  {

    class LUMYN_SDK_CPP_API MatrixTextBuilder : public lumyn::BuilderBase<MatrixTextBuilder>
    {
    public:
      using Direction = lumyn::MatrixTextScrollDirection;
      using Font = lumyn::MatrixTextFont;
      using Align = lumyn::MatrixTextAlign;

      MatrixTextBuilder(const lumyn::internal::ILEDDevice &device, std::string_view text)
          : _device(&device), _text(text)
      {
      }

      MatrixTextBuilder &ForZone(std::string_view zoneId)
      {
        return this->setZone(zoneId);
      }

      MatrixTextBuilder &ForGroup(std::string_view groupId)
      {
        return this->setGroup(groupId);
      }

      MatrixTextBuilder &WithColor(lumyn_color_t color)
      {
        this->checkNotExecuted();
        _color = color;
        return *this;
      }

      MatrixTextBuilder &WithDelay(std::chrono::milliseconds delay)
      {
        this->checkNotExecuted();
        _delay = delay;
        return *this;
      }

      MatrixTextBuilder &WithDelay(uint32_t delayMs)
      {
        return WithDelay(std::chrono::milliseconds(delayMs));
      }

      MatrixTextBuilder &WithDirection(Direction direction)
      {
        this->checkNotExecuted();
        _direction = direction;
        return *this;
      }

      MatrixTextBuilder &WithBackgroundColor(lumyn_color_t color)
      {
        this->checkNotExecuted();
        _bgColor = color;
        return *this;
      }

      MatrixTextBuilder &WithFont(Font font)
      {
        this->checkNotExecuted();
        _font = font;
        return *this;
      }

      MatrixTextBuilder &WithAlign(Align align)
      {
        this->checkNotExecuted();
        _align = align;
        return *this;
      }

      MatrixTextBuilder &SmoothScroll(bool enabled)
      {
        this->checkNotExecuted();
        _flags.smoothScroll = enabled ? 1 : 0;
        return *this;
      }

      MatrixTextBuilder &ShowBackground(bool enabled)
      {
        this->checkNotExecuted();
        _flags.showBackground = enabled ? 1 : 0;
        return *this;
      }

      MatrixTextBuilder &PingPong(bool enabled)
      {
        this->checkNotExecuted();
        _flags.pingPong = enabled ? 1 : 0;
        return *this;
      }

      MatrixTextBuilder &NoScroll(bool enabled)
      {
        this->checkNotExecuted();
        _flags.noScroll = enabled ? 1 : 0;
        return *this;
      }

      MatrixTextBuilder &WithYOffset(int yOffset)
      {
        this->checkNotExecuted();
        _yOffset = static_cast<int8_t>(yOffset);
        return *this;
      }

      MatrixTextBuilder &RunOnce(bool oneShot)
      {
        this->checkNotExecuted();
        _oneShot = oneShot;
        execute();
        return *this;
      }

      void execute() override;

      // Getter methods for testing/inspection
      std::string_view GetText() const { return _text; }
      lumyn_color_t GetColor() const { return _color; }
      uint32_t GetDelayMs() const { return static_cast<uint32_t>(_delay.count()); }
      Direction GetDirection() const { return _direction; }
      lumyn_color_t GetBgColor() const { return _bgColor; }
      Font GetFont() const { return _font; }
      Align GetAlign() const { return _align; }
      lumyn_matrix_text_flags_t GetFlags() const { return _flags; }
      int8_t GetYOffset() const { return _yOffset; }
      bool IsOneShot() const { return _oneShot; }
      const std::optional<std::string> &GetZoneId() const { return this->getZoneId(); }
      const std::optional<std::string> &GetGroupId() const { return this->getGroupId(); }

    private:
      const lumyn::internal::ILEDDevice *_device;
      std::string _text;
      lumyn_color_t _color{255, 255, 255};
      std::chrono::milliseconds _delay{50};
      Direction _direction{LUMYN_MATRIX_TEXT_SCROLL_LEFT};
      lumyn_color_t _bgColor{0, 0, 0};
      Font _font{LUMYN_MATRIX_TEXT_FONT_BUILTIN};
      Align _align{LUMYN_MATRIX_TEXT_ALIGN_LEFT};
      lumyn_matrix_text_flags_t _flags{1, 0, 0, 0, 0}; // smoothScroll=true by default
      int8_t _yOffset{0};
      bool _oneShot{false};
    };
  }
}
