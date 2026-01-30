#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <variant>

#include "lumyn/domain/module/ModuleInfo.h"

namespace lumyn::internal::Configuration {

// Generic configuration value type that can hold different types
using ConfigValue = std::variant<std::string, uint64_t, double, bool>;

struct Module {
  std::string id;
  std::string type;
  uint16_t pollingRateMs;
  lumyn::internal::ModuleInfo::ModuleConnectionType connectionType;
  std::optional<std::unordered_map<std::string, ConfigValue>> customConfig;
};

}  // namespace lumyn::internal::Configuration
