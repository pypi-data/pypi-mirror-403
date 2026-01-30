#include "lumyn/Constants.h"
#include "lumyn/configuration/LumynConfigurationSerializer.h"

#if LUMYN_HAS_JSON_SERIALIZER

#include <algorithm>
#include <nlohmann/json.hpp>

namespace lumyn::config {

namespace {

using namespace lumyn::internal::Configuration;
using json = nlohmann::ordered_json;

std::string NetworkTypeToString(NetworkType type) {
  switch (type) {
    case NetworkType::I2C:
      return "I2C";
    case NetworkType::USB:
      return "USB";
    case NetworkType::CAN:
      return "CAN";
    case NetworkType::UART:
      return "UART";
    default:
      return "USB";
  }
}

json ToJson(const Zone& zone) {
  json j;
  j["id"] = zone.id;
  if (zone.brightness) {
    j["brightness"] = *zone.brightness;
  }

  if (zone.type == ZoneType::Strip) {
    j["type"] = "strip";
    j["length"] = zone.strip.length;
    j["reversed"] = zone.strip.reversed;
  } else {
    j["type"] = "matrix";
    j["rows"] = zone.matrix.rows;
    j["cols"] = zone.matrix.cols;
    const uint8_t orient = zone.matrix.orientation;
    json orientation = {
        {"cornerTopBottom", (orient & 0x01) ? "bottom" : "top"},
        {"cornerLeftRight", (orient & 0x02) ? "right" : "left"},
        {"axisLayout", (orient & 0x04) ? "cols" : "rows"},
        {"sequenceLayout", (orient & 0x08) ? "zigzag" : "progressive"},
    };
    j["orientation"] = std::move(orientation);
  }

  return j;
}

json ToJson(const Animation& animation) {
  json j;
  j["animationId"] = animation.id;
  if (animation.color) {
    j["color"] = {
        {"r", animation.color->r},
        {"g", animation.color->g},
        {"b", animation.color->b},
    };
  }
  j["delay"] = animation.delay;
  j["reversed"] = animation.reversed;
  if (animation.repeatCount) {
    j["repeat"] = *animation.repeatCount;
  }
  return j;
}

json ToJson(const Bitmap& bitmap) {
  json j;
  j["id"] = bitmap.id;
  j["type"] = (bitmap.type == BitmapType::Animated) ? "animated" : "static";
  if (bitmap.type == BitmapType::Animated) {
    if (bitmap.folder) {
      j["folder"] = *bitmap.folder;
    }
    if (bitmap.frameDelay) {
      j["delay"] = *bitmap.frameDelay;
    }
  } else if (bitmap.path) {
    j["path"] = *bitmap.path;
  }
  return j;
}

json ToJson(const Module& module) {
  json j;
  j["id"] = module.id;
  j["type"] = module.type;
  j["pollingRateMs"] = module.pollingRateMs;
  switch (module.connectionType) {
    case LUMYN_MODULE_CONNECTION_I2C:
      j["connection"] = "I2C";
      break;
    case LUMYN_MODULE_CONNECTION_SPI:
      j["connection"] = "SPI";
      break;
    case LUMYN_MODULE_CONNECTION_UART:
      j["connection"] = "UART";
      break;
    case LUMYN_MODULE_CONNECTION_DIO:
      j["connection"] = "DIO";
      break;
    case LUMYN_MODULE_CONNECTION_AIO:
      j["connection"] = "AIO";
      break;
    default:
      j["connection"] = "I2C";
      break;
  }

  if (module.customConfig) {
    json configJson = json::object();
    for (const auto& [key, value] : *module.customConfig) {
      std::visit([&](const auto& v) { configJson[key] = v; }, value);
    }
    j["config"] = std::move(configJson);
  }
  return j;
}

}  // namespace

std::string SerializeConfigToJson(
    const lumyn::internal::Configuration::LumynConfiguration& config) {
  json root = json::object();

  if (config.teamNumber) {
    root["team"] = *config.teamNumber;
  }

  json networkJson = json::object();
  networkJson["mode"] = NetworkTypeToString(config.network.type);
  if (config.network.type == NetworkType::I2C) {
    networkJson["address"] = config.network.i2c.address;
  } else if (config.network.type == NetworkType::UART) {
    networkJson["baudRate"] = config.network.uart.baud;
  }
  root["network"] = std::move(networkJson);

  if (config.channels && !config.channels->empty()) {
    json channelsJson = json::object();
    for (const auto& channel : *config.channels) {
      json ch;
      ch["id"] = channel.id;
      ch["length"] = channel.length;
      if (channel.brightness) {
        ch["brightness"] = *channel.brightness;
      }
      json zones = json::array();
      for (const auto& zone : channel.zones) {
        zones.push_back(ToJson(zone));
      }
      ch["zones"] = std::move(zones);
      const std::string key = channel.key.empty() ? channel.id : channel.key;
      channelsJson[key] = std::move(ch);
    }
    root["channels"] = std::move(channelsJson);
  }

  if (config.sequences && !config.sequences->empty()) {
    json seqArr = json::array();
    for (const auto& seq : *config.sequences) {
      json seqJson;
      seqJson["id"] = seq.id;
      json steps = json::array();
      for (const auto& step : seq.steps) {
        steps.push_back(ToJson(step));
      }
      seqJson["steps"] = std::move(steps);
      seqArr.push_back(std::move(seqJson));
    }
    root["sequences"] = std::move(seqArr);
  }

  if (config.bitmaps && !config.bitmaps->empty()) {
    json bmpArr = json::array();
    for (const auto& bmp : *config.bitmaps) {
      bmpArr.push_back(ToJson(bmp));
    }
    root["bitmaps"] = std::move(bmpArr);
  }

  if (config.sensors && !config.sensors->empty()) {
    json sensors = json::array();
    for (const auto& sensor : *config.sensors) {
      sensors.push_back(ToJson(sensor));
    }
    root["sensors"] = std::move(sensors);
  }

  if (config.animationGroups && !config.animationGroups->empty()) {
    json groupsArr = json::array();
    for (const auto& group : *config.animationGroups) {
      json groupJson;
      groupJson["id"] = group.id;
      groupJson["zoneIds"] = group.zoneIds;
      groupsArr.push_back(std::move(groupJson));
    }
    root["groups"] = std::move(groupsArr);
  }

  return root.dump();
}

}  // namespace lumyn::config

#endif  // LUMYN_HAS_JSON_SERIALIZER
