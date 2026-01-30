#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

#include "lumyn/configuration/Configuration.h"
#include "lumyn/domain/Color.h"
#include "lumyn/domain/module/ModuleInfo.h"

namespace lumyn
{
  namespace config
  {

    class ConfigBuilder
    {
    public:
      class ChannelBuilder
      {
      public:
        ChannelBuilder(ConfigBuilder &parent, std::string channelNum, std::string id, uint16_t length)
            : _parent(parent)
        {
          _channel.key = std::move(channelNum);
          _channel.id = std::move(id);
          _channel.length = length;
        }

        ChannelBuilder &Brightness(uint8_t brightness)
        {
          _channel.brightness = brightness;
          return *this;
        }

        ChannelBuilder &AddStripZone(const std::string &id, uint16_t length, bool reversed = false,
                                     std::optional<uint8_t> brightness = std::nullopt)
        {
          lumyn::internal::Configuration::Zone zone{};
          zone.type = lumyn::internal::Configuration::ZoneType::Strip;
          zone.id = id;
          zone.brightness = brightness;
          zone.strip.length = length;
          zone.strip.reversed = reversed;
          _channel.zones.emplace_back(std::move(zone));
          return *this;
        }

        ChannelBuilder &AddMatrixZone(const std::string &id, uint16_t rows, uint16_t cols,
                                      std::optional<uint8_t> brightness = std::nullopt,
                                      uint8_t orientation = 0)
        {
          lumyn::internal::Configuration::Zone zone{};
          zone.type = lumyn::internal::Configuration::ZoneType::Matrix;
          zone.id = id;
          zone.brightness = brightness;
          zone.matrix.rows = rows;
          zone.matrix.cols = cols;
          zone.matrix.orientation = orientation;
          _channel.zones.emplace_back(std::move(zone));
          return *this;
        }

        ConfigBuilder &EndChannel()
        {
          _parent._channels.emplace_back(std::move(_channel));
          return _parent;
        }

      private:
        ConfigBuilder &_parent;
        lumyn::internal::Configuration::Channel _channel{};
      };

      class SequenceBuilder
      {
      public:
        class StepBuilder
        {
        public:
          StepBuilder(SequenceBuilder &parent, std::string animationId)
              : _parent(parent), _animationId(std::move(animationId)) {}

          StepBuilder &WithColor(uint8_t r, uint8_t g, uint8_t b)
          {
            _color = lumyn::internal::domain::Color{r, g, b};
            return *this;
          }

          StepBuilder &WithDelay(int delayMs)
          {
            _delay = static_cast<uint16_t>(std::max(0, delayMs));
            return *this;
          }

          StepBuilder &Reverse(bool reversed)
          {
            _reversed = reversed;
            return *this;
          }

          StepBuilder &WithRepeat(int repeat)
          {
            const int clamped = std::clamp(repeat, 0, 255);
            _repeat = static_cast<uint8_t>(clamped);
            return *this;
          }

          SequenceBuilder &EndStep()
          {
            lumyn::internal::Configuration::Animation animation{};
            animation.id = _animationId;
            animation.delay = _delay;
            animation.reversed = _reversed;
            animation.color = _color;
            animation.repeatCount = _repeat;
            _parent._sequence.steps.emplace_back(std::move(animation));
            return _parent;
          }

        private:
          SequenceBuilder &_parent;
          std::string _animationId;
          uint16_t _delay = 0;
          bool _reversed = false;
          std::optional<lumyn::internal::domain::Color> _color;
          std::optional<uint8_t> _repeat;
        };

        SequenceBuilder(ConfigBuilder &parent, std::string id) : _parent(parent)
        {
          _sequence.id = std::move(id);
        }

        StepBuilder AddStep(const std::string &animationId)
        {
          return StepBuilder(*this, animationId);
        }

        ConfigBuilder &EndSequence()
        {
          _parent._sequences.emplace_back(std::move(_sequence));
          return _parent;
        }

      private:
        ConfigBuilder &_parent;
        lumyn::internal::Configuration::AnimationSequence _sequence{};
      };

      class BitmapBuilder
      {
      public:
        BitmapBuilder(ConfigBuilder &parent, std::string id) : _parent(parent)
        {
          _bitmap.id = std::move(id);
        }

        BitmapBuilder &Static(const std::string &path)
        {
          _bitmap.type = lumyn::internal::Configuration::BitmapType::Static;
          _bitmap.path = path;
          _bitmap.folder.reset();
          _bitmap.frameDelay.reset();
          return *this;
        }

        BitmapBuilder &Animated(const std::string &folder, uint16_t frameDelay)
        {
          _bitmap.type = lumyn::internal::Configuration::BitmapType::Animated;
          _bitmap.folder = folder;
          _bitmap.frameDelay = frameDelay;
          _bitmap.path.reset();
          return *this;
        }

        ConfigBuilder &EndBitmap()
        {
          _parent._bitmaps.emplace_back(std::move(_bitmap));
          return _parent;
        }

      private:
        ConfigBuilder &_parent;
        lumyn::internal::Configuration::Bitmap _bitmap{};
      };

      class ModuleBuilder
      {
      public:
        ModuleBuilder(ConfigBuilder &parent, std::string id, std::string type, int pollingRateMs,
                      const std::string &connectionType)
            : _parent(parent)
        {
          _sensor.id = std::move(id);
          _sensor.type = std::move(type);
          _sensor.pollingRateMs = static_cast<uint16_t>(std::max(0, pollingRateMs));
          _sensor.connectionType = ParseConnectionType(connectionType);
        }

        ModuleBuilder &WithConfig(const std::string &key, const std::string &value)
        {
          _config[key] = value;
          return *this;
        }

        ModuleBuilder &WithConfig(const std::string &key, uint64_t value)
        {
          _config[key] = value;
          return *this;
        }

        ModuleBuilder &WithConfig(const std::string &key, double value)
        {
          _config[key] = value;
          return *this;
        }

        ModuleBuilder &WithConfig(const std::string &key, bool value)
        {
          _config[key] = value;
          return *this;
        }

        ModuleBuilder &ConnectionType(lumyn::internal::ModuleInfo::ModuleConnectionType type)
        {
          _sensor.connectionType = type;
          return *this;
        }

        ConfigBuilder &EndModule()
        {
          if (!_config.empty())
          {
            _sensor.customConfig = _config;
          }
          _parent._sensors.emplace_back(std::move(_sensor));
          return _parent;
        }

      private:
        static lumyn::internal::ModuleInfo::ModuleConnectionType ParseConnectionType(
            const std::string &value)
        {
          std::string upper = value;
          std::transform(upper.begin(), upper.end(), upper.begin(), [](unsigned char c)
                         { return static_cast<char>(std::toupper(c)); });
          if (upper == "SPI")
          {
            return LUMYN_MODULE_CONNECTION_SPI;
          }
          if (upper == "UART")
          {
            return LUMYN_MODULE_CONNECTION_UART;
          }
          if (upper == "DIO")
          {
            return LUMYN_MODULE_CONNECTION_DIO;
          }
          if (upper == "AIO")
          {
            return LUMYN_MODULE_CONNECTION_AIO;
          }
          return LUMYN_MODULE_CONNECTION_I2C;
        }

        ConfigBuilder &_parent;
        lumyn::internal::Configuration::Module _sensor{};
        std::unordered_map<std::string, lumyn::internal::Configuration::ConfigValue> _config;
      };

      class GroupBuilder
      {
      public:
        GroupBuilder(ConfigBuilder &parent, std::string id) : _parent(parent), _id(std::move(id)) {}

        GroupBuilder &AddZone(const std::string &zoneId)
        {
          _zoneIds.push_back(zoneId);
          return *this;
        }

        ConfigBuilder &EndGroup()
        {
          lumyn::internal::Configuration::AnimationGroup group{};
          group.id = _id;
          group.zoneIds = std::move(_zoneIds);
          _parent._groups.emplace_back(std::move(group));
          return _parent;
        }

      private:
        ConfigBuilder &_parent;
        std::string _id;
        std::vector<std::string> _zoneIds;
      };

      ConfigBuilder() = default;

      ConfigBuilder &ForTeam(const std::string &team)
      {
        _teamNumber = team;
        return *this;
      }

      ConfigBuilder &SetNetworkType(lumyn::internal::Configuration::NetworkType type)
      {
        _network.type = type;
        return *this;
      }

      ConfigBuilder &SetBaudRate(uint32_t baud)
      {
        _network.uart.baud = baud;
        return *this;
      }

      ConfigBuilder &SetI2cAddress(uint8_t address)
      {
        _network.i2c.address = address;
        return *this;
      }

      /**
       * Add a channel with a specific channel number and id.
       * @param channelNum The channel number (e.g., 1, 2)
       * @param id The human-readable identifier for this channel
       * @param length Total LED length of the channel
       */
      ChannelBuilder AddChannel(int channelNum, const std::string &id, uint16_t length)
      {
        return ChannelBuilder(*this, std::to_string(channelNum), id, length);
      }

      SequenceBuilder AddSequence(const std::string &sequenceId)
      {
        return SequenceBuilder(*this, sequenceId);
      }

      BitmapBuilder AddBitmap(const std::string &bitmapId)
      {
        return BitmapBuilder(*this, bitmapId);
      }

      ModuleBuilder AddModule(const std::string &moduleId, const std::string &moduleType,
                              int pollingRateMs, const std::string &connectionType)
      {
        return ModuleBuilder(*this, moduleId, moduleType, pollingRateMs, connectionType);
      }

      GroupBuilder AddGroup(const std::string &groupId)
      {
        return GroupBuilder(*this, groupId);
      }

      lumyn::internal::Configuration::LumynConfiguration Build() const
      {
        lumyn::internal::Configuration::LumynConfiguration result{};
        result.md5.fill(0);
        result.teamNumber = _teamNumber;
        result.network = _network;
        if (!_channels.empty())
        {
          result.channels = _channels;
        }
        if (!_sequences.empty())
        {
          result.sequences = _sequences;
        }
        if (!_bitmaps.empty())
        {
          result.bitmaps = _bitmaps;
        }
        if (!_sensors.empty())
        {
          result.sensors = _sensors;
        }
        if (!_groups.empty())
        {
          result.animationGroups = _groups;
        }
        return result;
      }

    private:
      std::optional<std::string> _teamNumber;
      lumyn::internal::Configuration::Network _network{};
      std::vector<lumyn::internal::Configuration::Channel> _channels;
      std::vector<lumyn::internal::Configuration::AnimationSequence> _sequences;
      std::vector<lumyn::internal::Configuration::Bitmap> _bitmaps;
      std::vector<lumyn::internal::Configuration::Module> _sensors;
      std::vector<lumyn::internal::Configuration::AnimationGroup> _groups;
    };

  } // namespace config
} // namespace lumyn
