#pragma once

// Cross-platform DLL export macro for config functions
#ifdef _WIN32
#define LUMYN_CONFIG_EXPORT __declspec(dllexport)
#else
#define LUMYN_CONFIG_EXPORT __attribute__((visibility("default")))
#endif

#if __has_include(<nlohmann/json.hpp>)
#define LUMYN_HAS_JSON_SERIALIZER 1

#include <string>

#include "lumyn/configuration/Configuration.h"

namespace lumyn::config
{

  LUMYN_CONFIG_EXPORT std::string SerializeConfigToJson(
      const lumyn::internal::Configuration::LumynConfiguration &config);

} // namespace lumyn::config

#else
#define LUMYN_HAS_JSON_SERIALIZER 0
#endif
