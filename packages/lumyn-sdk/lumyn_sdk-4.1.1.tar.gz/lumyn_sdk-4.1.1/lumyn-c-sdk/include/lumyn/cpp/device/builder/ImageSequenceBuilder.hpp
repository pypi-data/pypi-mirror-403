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

namespace lumyn
{
  namespace device
  {

    class LUMYN_SDK_CPP_API ImageSequenceBuilder : public lumyn::BuilderBase<ImageSequenceBuilder>
    {
    public:
      ImageSequenceBuilder(const lumyn::internal::ILEDDevice &device, std::string_view sequenceId)
          : _device(&device), _sequenceId(sequenceId)
      {
      }

      ImageSequenceBuilder &ForZone(std::string_view zoneId)
      {
        return this->setZone(zoneId);
      }

      ImageSequenceBuilder &ForGroup(std::string_view groupId)
      {
        return this->setGroup(groupId);
      }

      ImageSequenceBuilder &WithColor(lumyn_color_t color)
      {
        this->checkNotExecuted();
        _color = color;
        return *this;
      }

      ImageSequenceBuilder &SetColor(bool setColor)
      {
        this->checkNotExecuted();
        _setColor = setColor;
        return *this;
      }

      ImageSequenceBuilder &RunOnce(bool oneShot)
      {
        this->checkNotExecuted();
        _oneShot = oneShot;
        execute();
        return *this;
      }

      void execute() override;

      // Getter methods for testing/inspection
      std::string_view GetSequenceId() const { return _sequenceId; }
      lumyn_color_t GetColor() const { return _color; }
      bool GetSetColor() const { return _setColor; }
      bool IsOneShot() const { return _oneShot; }
      const std::optional<std::string> &GetZoneId() const { return this->getZoneId(); }
      const std::optional<std::string> &GetGroupId() const { return this->getGroupId(); }

    private:
      const lumyn::internal::ILEDDevice *_device;
      std::string _sequenceId;
      lumyn_color_t _color{255, 255, 255};
      bool _setColor{true};
      bool _oneShot{false};
    };
  }
}
