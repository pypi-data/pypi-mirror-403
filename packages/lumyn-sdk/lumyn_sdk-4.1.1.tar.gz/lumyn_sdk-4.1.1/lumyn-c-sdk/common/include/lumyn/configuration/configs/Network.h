#pragma once

#include <cstdint>

namespace lumyn::internal::Configuration
{

  enum class NetworkType
  {
    I2C = 0,
    USB = 1,
    CAN = 2,
    UART = 3
  };

  struct I2CNetwork
  {
    uint8_t address = 0;
    constexpr I2CNetwork() noexcept = default;
  };

  struct UARTNetwork
  {
    uint32_t baud = lumyn::internal::Constants::Serial::kDefaultBaudRate;
    constexpr UARTNetwork() noexcept = default;
  };

  struct Network
  {
    NetworkType type = NetworkType::USB;
    union
    {
      I2CNetwork i2c;
      UARTNetwork uart;
    };

    Network() noexcept : type(NetworkType::USB), i2c{} {}
  };

} // namespace lumyn::internal::Configuration
