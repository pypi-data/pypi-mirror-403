#pragma once

// Cross-platform DLL export macro for config functions
#ifdef _WIN32
#define LUMYN_CONFIG_EXPORT __declspec(dllexport)
#else
#define LUMYN_CONFIG_EXPORT __attribute__((visibility("default")))
#endif

#if __has_include(<nlohmann/json.hpp>)
#define LUMYN_HAS_JSON_PARSER 1

#include <nlohmann/json.hpp>
#include <optional>
#include <string>

#include "lumyn/configuration/Configuration.h"

namespace lumyn::config
{

  LUMYN_CONFIG_EXPORT std::optional<lumyn::internal::Configuration::LumynConfiguration> ParseConfig(
      const std::string &jsonText);
  LUMYN_CONFIG_EXPORT std::optional<lumyn::internal::Configuration::LumynConfiguration> ParseConfig(
      const nlohmann::json &root);

} // namespace lumyn::config

#else
#define LUMYN_HAS_JSON_PARSER 0
#endif
