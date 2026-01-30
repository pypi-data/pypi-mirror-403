#pragma once

#include <lumyn/cpp/export.hpp>

namespace lumyn::internal
{
  class LEDCommander;
  class MatrixCommander;
}

namespace lumyn
{
  namespace internal
  {

    /**
     * @brief Interface for devices with LED support
     *
     * Provides access to LEDCommander and MatrixCommander instances.
     * These commanders already provide all the LED control operations.
     */
    class LUMYN_SDK_CPP_API ILEDDevice
    {
    public:
      virtual ~ILEDDevice() = default;

      /**
       * @brief Get the LED commander for controlling LEDs
       * @return Reference to the LED commander
       */
      virtual LEDCommander &GetLEDCommander() = 0;
      virtual const LEDCommander &GetLEDCommander() const = 0;

      /**
       * @brief Get the matrix commander for controlling LED matrices
       * @return Reference to the matrix commander
       */
      virtual MatrixCommander &GetMatrixCommander() = 0;
      virtual const MatrixCommander &GetMatrixCommander() const = 0;
    };

  } // namespace internal
} // namespace lumyn
