#include "lumyn/Constants.h"
#include "lumyn/configuration/LumynConfigurationParser.h"

#if LUMYN_HAS_JSON_PARSER

#include <algorithm>
#include <string>
#include <unordered_map>

#include "lumyn/util/logging/ConsoleLogger.h"

namespace lumyn::config {

namespace {

using namespace lumyn::internal::Configuration;

uint8_t ClampByte(int value) {
  return static_cast<uint8_t>(std::max(0, std::min(255, value)));
}

Network ParseNetwork(const nlohmann::json& root) {
  Network result;
  if (root.contains("network") && root["network"].is_object()) {
    auto net = root["network"];
    if (net.contains("mode") && net["mode"].is_string()) {
      std::string mode = net["mode"].get<std::string>();
      if (mode == "I2C" || mode == "i2c") {
        result.type = NetworkType::I2C;
        if (net.contains("address") && net["address"].is_number_integer()) {
          result.i2c.address = static_cast<uint8_t>(net["address"].get<int>());
        }
      } else if (mode == "CAN" || mode == "can") {
        result.type = NetworkType::CAN;
      } else {
        result.type = NetworkType::USB;
      }
    }
  }
  return result;
}

std::optional<Zone> ParseZone(const nlohmann::json& zoneNode) {
  if (!zoneNode.is_object()) {
    return std::nullopt;
  }
  Zone zone{};
  if (zoneNode.contains("id") && zoneNode["id"].is_string()) {
    zone.id = zoneNode["id"].get<std::string>();
  } else {
    return std::nullopt;
  }

  if (zoneNode.contains("brightness") &&
      zoneNode["brightness"].is_number_integer()) {
    zone.brightness = ClampByte(zoneNode["brightness"].get<int>());
  }

  if (zoneNode.contains("type") && zoneNode["type"].is_string()) {
    std::string type = zoneNode["type"].get<std::string>();
    if (type == "strip" || type == "Strip") {
      zone.type = ZoneType::Strip;
      zone.strip.length =
          static_cast<uint16_t>(std::max(0, zoneNode.value("length", 0)));
      zone.strip.reversed = zoneNode.value("reversed", false);
    } else if (type == "matrix" || type == "Matrix") {
      zone.type = ZoneType::Matrix;
      zone.matrix.rows =
          static_cast<uint16_t>(std::max(0, zoneNode.value("rows", 0)));
      zone.matrix.cols =
          static_cast<uint16_t>(std::max(0, zoneNode.value("cols", 0)));
      auto orientation = zoneNode.contains("orientation") &&
                                 zoneNode["orientation"].is_object()
                             ? zoneNode["orientation"]
                             : nlohmann::json::object();
      uint8_t orient = 0;
      if (orientation.contains("cornerTopBottom") &&
          orientation["cornerTopBottom"].is_string() &&
          orientation["cornerTopBottom"].get<std::string>() == "bottom") {
        orient |= 0x01;
      }
      if (orientation.contains("cornerLeftRight") &&
          orientation["cornerLeftRight"].is_string() &&
          orientation["cornerLeftRight"].get<std::string>() == "right") {
        orient |= 0x02;
      }
      if (orientation.contains("axisLayout") &&
          orientation["axisLayout"].is_string() &&
          orientation["axisLayout"].get<std::string>() == "cols") {
        orient |= 0x04;
      }
      if (orientation.contains("sequenceLayout") &&
          orientation["sequenceLayout"].is_string() &&
          orientation["sequenceLayout"].get<std::string>() == "zigzag") {
        orient |= 0x08;
      }
      zone.matrix.orientation = orient;
    } else {
      return std::nullopt;
    }
  } else {
    return std::nullopt;
  }

  return zone;
}

std::optional<Animation> ParseAnimation(const nlohmann::json& stepNode) {
  if (!stepNode.is_object()) {
    return std::nullopt;
  }
  Animation step{};
  if (stepNode.contains("animationId") && stepNode["animationId"].is_string()) {
    step.id = stepNode["animationId"].get<std::string>();
  } else {
    return std::nullopt;
  }

  step.delay = static_cast<uint16_t>(std::max(0, stepNode.value("delay", 0)));
  step.reversed = stepNode.value("reversed", false);

  if (stepNode.contains("color") && stepNode["color"].is_object()) {
    auto color = stepNode["color"];
    if (color.contains("r") && color.contains("g") && color.contains("b")) {
      step.color = lumyn::internal::domain::Color{
          static_cast<uint8_t>(
              std::max(0, std::min(255, color["r"].get<int>()))),
          static_cast<uint8_t>(
              std::max(0, std::min(255, color["g"].get<int>()))),
          static_cast<uint8_t>(
              std::max(0, std::min(255, color["b"].get<int>())))};
    }
  }

  if (stepNode.contains("repeat") && stepNode["repeat"].is_number_integer()) {
    step.repeatCount = static_cast<uint8_t>(
        std::max(0, std::min(255, stepNode["repeat"].get<int>())));
  }

  return step;
}

std::optional<AnimationSequence> ParseSequence(const nlohmann::json& seqNode) {
  if (!seqNode.is_object()) {
    return std::nullopt;
  }

  AnimationSequence sequence;
  if (seqNode.contains("id") && seqNode["id"].is_string()) {
    sequence.id = seqNode["id"].get<std::string>();
  } else {
    return std::nullopt;
  }

  if (seqNode.contains("steps") && seqNode["steps"].is_array()) {
    for (const auto& stepNode : seqNode["steps"]) {
      auto step = ParseAnimation(stepNode);
      if (step) {
        sequence.steps.emplace_back(*step);
      }
    }
  }

  return sequence;
}

std::optional<Bitmap> ParseBitmap(const nlohmann::json& bmpNode) {
  if (!bmpNode.is_object() || !bmpNode.contains("id") ||
      !bmpNode["id"].is_string()) {
    return std::nullopt;
  }

  Bitmap bitmap;
  bitmap.id = bmpNode["id"].get<std::string>();
  std::string type = bmpNode.value("type", "static");
  if (type == "animated" || type == "Animated") {
    bitmap.type = BitmapType::Animated;
    if (bmpNode.contains("folder") && bmpNode["folder"].is_string()) {
      bitmap.folder = bmpNode["folder"].get<std::string>();
    }
    if (bmpNode.contains("delay") && bmpNode["delay"].is_number_integer()) {
      bitmap.frameDelay =
          static_cast<uint16_t>(std::max(0, bmpNode["delay"].get<int>()));
    }
  } else {
    bitmap.type = BitmapType::Static;
    if (bmpNode.contains("path") && bmpNode["path"].is_string()) {
      bitmap.path = bmpNode["path"].get<std::string>();
    }
  }
  return bitmap;
}

std::optional<Module> ParseModule(const nlohmann::json& modNode) {
  if (!modNode.is_object()) {
    return std::nullopt;
  }
  Module module;
  if (modNode.contains("id") && modNode["id"].is_string()) {
    module.id = modNode["id"].get<std::string>();
  } else {
    return std::nullopt;
  }
  if (modNode.contains("type") && modNode["type"].is_string()) {
    module.type = modNode["type"].get<std::string>();
  } else {
    return std::nullopt;
  }
  module.pollingRateMs =
      static_cast<uint16_t>(std::max(0, modNode.value("pollingRateMs", 0)));
  if (modNode.contains("connection") && modNode["connection"].is_string()) {
    std::string type = modNode["connection"].get<std::string>();
    if (type == "SPI") {
          module.connectionType = LUMYN_MODULE_CONNECTION_SPI;
    } else if (type == "UART") {
          module.connectionType = LUMYN_MODULE_CONNECTION_UART;
    } else if (type == "DIO") {
          module.connectionType = LUMYN_MODULE_CONNECTION_DIO;
    } else if (type == "AIO") {
          module.connectionType = LUMYN_MODULE_CONNECTION_AIO;
    } else {
          module.connectionType = LUMYN_MODULE_CONNECTION_I2C;
    }
  }

  if (modNode.contains("config") && modNode["config"].is_object()) {
    std::unordered_map<std::string, ConfigValue> config;
    for (auto it = modNode["config"].begin(); it != modNode["config"].end();
         ++it) {
      if (it.value().is_string()) {
        config[it.key()] = it.value().get<std::string>();
      } else if (it.value().is_boolean()) {
        config[it.key()] = it.value().get<bool>();
      } else if (it.value().is_number_integer()) {
        config[it.key()] = static_cast<uint64_t>(it.value().get<uint64_t>());
      } else if (it.value().is_number_float()) {
        config[it.key()] = static_cast<double>(it.value().get<double>());
      }
    }
    if (!config.empty()) {
      module.customConfig = std::move(config);
    }
  }

  return module;
}

std::optional<AnimationGroup> ParseGroup(const nlohmann::json& groupNode) {
  if (!groupNode.is_object()) {
    return std::nullopt;
  }
  AnimationGroup group;
  if (groupNode.contains("id") && groupNode["id"].is_string()) {
    group.id = groupNode["id"].get<std::string>();
  } else {
    return std::nullopt;
  }

  if (groupNode.contains("zoneIds") && groupNode["zoneIds"].is_array()) {
    for (const auto& zoneId : groupNode["zoneIds"]) {
      if (zoneId.is_string()) {
        group.zoneIds.emplace_back(zoneId.get<std::string>());
      }
    }
  }
  return group;
}

}  // namespace

std::optional<LumynConfiguration> ParseConfig(const nlohmann::json& root) {
  LumynConfiguration config;
  config.network = ParseNetwork(root);

  if (root.contains("team") && root["team"].is_string()) {
    config.teamNumber = root["team"].get<std::string>();
  }

  if (root.contains("channels") && root["channels"].is_object()) {
    std::vector<Channel> channels;
    for (auto it = root["channels"].begin(); it != root["channels"].end();
         ++it) {
      const auto& chNode = it.value();
      if (!chNode.is_object()) {
        continue;
      }
      Channel channel;
      channel.key = it.key();
      channel.id = chNode.contains("id") && chNode["id"].is_string()
                       ? chNode["id"].get<std::string>()
                       : channel.key;
      channel.length =
          static_cast<uint16_t>(std::max(0, chNode.value("length", 0)));
      if (channel.id.empty() || channel.length == 0) {
        continue;
      }
      if (chNode.contains("brightness") &&
          chNode["brightness"].is_number_integer()) {
        channel.brightness = ClampByte(chNode["brightness"].get<int>());
      }
      if (chNode.contains("zones") && chNode["zones"].is_array()) {
        for (const auto& zoneNode : chNode["zones"]) {
          auto zone = ParseZone(zoneNode);
          if (zone) {
            channel.zones.emplace_back(std::move(*zone));
          }
        }
      }
      channels.emplace_back(std::move(channel));
    }
    if (!channels.empty()) {
      config.channels = std::move(channels);
    }
  }

  if (root.contains("sequences") && root["sequences"].is_array()) {
    std::vector<AnimationSequence> sequences;
    for (const auto& seqNode : root["sequences"]) {
      auto seq = ParseSequence(seqNode);
      if (seq) {
        sequences.emplace_back(std::move(*seq));
      }
    }
    if (!sequences.empty()) {
      config.sequences = std::move(sequences);
    }
  }

  if (root.contains("bitmaps") && root["bitmaps"].is_array()) {
    std::vector<Bitmap> bitmaps;
    for (const auto& bmpNode : root["bitmaps"]) {
      auto bmp = ParseBitmap(bmpNode);
      if (bmp) {
        bitmaps.emplace_back(std::move(*bmp));
      }
    }
    if (!bitmaps.empty()) {
      config.bitmaps = std::move(bitmaps);
    }
  }

  if (root.contains("sensors") && root["sensors"].is_array()) {
    std::vector<Module> modules;
    for (const auto& modNode : root["sensors"]) {
      auto sensor = ParseModule(modNode);
      if (sensor) {
        modules.emplace_back(std::move(*sensor));
      }
    }
    if (!modules.empty()) {
      config.sensors = std::move(modules);
    }
  }

  if (root.contains("groups") && root["groups"].is_array()) {
    std::vector<AnimationGroup> groups;
    for (const auto& groupNode : root["groups"]) {
      auto group = ParseGroup(groupNode);
      if (group) {
        groups.emplace_back(std::move(*group));
      }
    }
    if (!groups.empty()) {
      config.animationGroups = std::move(groups);
    }
  }

  return config;
}

std::optional<LumynConfiguration> ParseConfig(const std::string& jsonText) {
  if (!nlohmann::json::accept(jsonText)) {
    lumyn::internal::ConsoleLogger::getInstance().logError(
        "LumynConfigurationParser", "Invalid JSON text provided");
    return std::nullopt;
  }

  const auto json = nlohmann::json::parse(jsonText);
  return ParseConfig(json);
}

}  // namespace lumyn::config

#endif  // LUMYN_HAS_JSON_PARSER
