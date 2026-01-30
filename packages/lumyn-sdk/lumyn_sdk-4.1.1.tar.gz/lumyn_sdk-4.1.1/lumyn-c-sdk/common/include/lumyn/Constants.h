#pragma once

#include <cstdint>
#include <string_view>

#include "lumyn/domain/Color.h"

namespace lumyn::internal::Constants
{
  namespace File
  {
    const std::string_view kConfigFileName = "config.json";
  } // namespace File

  namespace CAN
  {
    constexpr uint8_t LUMYN_LABS_MANUFACTURER_ID = 19;
    constexpr uint8_t CONNECTORX_DEVICE_TYPE = 11;
  } // namespace CAN

  namespace LumynTP
  {
    // Minimum size (in bytes) for when transmission data will be compressed
    constexpr uint32_t kMinCompressionSize = 256;
  }

  namespace Logging
  {
    /**
     * @brief Levels of logging
     *
     */
    enum class Level
    {
      VERBOSE = 0,
      INFO,
      WARNING,
      ERROR,
      FATAL
    };
    /**
     * @brief Will not log messages that fall below this level
     *
     */
    constexpr auto kMinLogLevel = Level::WARNING;

    /**
     * @brief Logging prefix
     */
    constexpr auto kLogPrefix = "[  Lumyn   ] ";
  } // namespace Logging

  namespace ColorConstants
  {
    static const lumyn::internal::domain::Color kDefaultAnimationColor = {0, 0,
                                                                          240};
  } // namespace ColorConstants

  namespace Validation
  {
    constexpr int kMinTeamNumber = 0;
    constexpr int kMaxTeamNumber = 99999;
    constexpr int kMinBrightness = 0;
    constexpr int kMaxBrightness = 255;
    constexpr int kMinColorValue = 0;
    constexpr int kMaxColorValue = 255;
    constexpr int kMinCANId = 0;
    constexpr int kMaxCANId = 127;
    constexpr int kMinI2CAddress = 2;
    constexpr int kMaxI2CAddress = 126;
    constexpr int kMinDelay = 0;
    constexpr int kMinBaudRate = 9600;
    constexpr int kMaxBaudRate = 921600;
  } // namespace Validation

  namespace Serial
  {
    constexpr int kDefaultBaudRate = 115200;
  } // namespace Serial

  namespace LED
  {
    constexpr size_t kBytesPerLed = 3; // RGB
    constexpr size_t kMaxMatrixTextLength = 24;
    // Default fallback values for animations when instance is not found
    constexpr uint16_t kDefaultAnimationDelay = 250; // milliseconds
    // Default animation color: {0, 0, 240}
    constexpr lumyn::internal::domain::Color kDefaultAnimationColor = {0, 0, 240};
  } // namespace LED
} // namespace lumyn::internal::Constants
