#pragma once

#include <lumyn/cpp/export.hpp>
#include "lumyn/cpp/device/ILEDDevice.hpp"
#include "lumyn/cpp/led/LEDCommander.hpp"
#include "lumyn/cpp/led/MatrixCommander.hpp"
#include <memory>
#include <functional>

namespace lumyn::internal
{
  /**
   * @brief Base class for devices with LED support
   *
   * Owns and provides access to LEDCommander and MatrixCommander instances.
   * Subclasses provide a callback for sending LED commands.
   */
  class LUMYN_SDK_CPP_API BaseLEDDevice : public ILEDDevice
  {
  public:
    BaseLEDDevice() = default;
    virtual ~BaseLEDDevice() = default;

    /**
     * @brief Send a raw LED command
     * Subclasses must implement this to send data to the device
     */
    virtual void SendLEDCommand(const void *data, uint32_t length) = 0;

    /**
     * @brief Get the LED commander for this device
     */
    LEDCommander &GetLEDCommander() override { return *_leds; }
    const LEDCommander &GetLEDCommander() const override { return *_leds; }

    /**
     * @brief Get the matrix commander for this device
     */
    MatrixCommander &GetMatrixCommander() override { return *_matrix; }
    const MatrixCommander &GetMatrixCommander() const override { return *_matrix; }

  protected:
    /**
     * @brief Initialize the LED and matrix commanders with the send callback
     * @param sendCallback Function to call when sending LED commands
     */
    void InitializeLEDCommanders(std::function<void(Command::LED::LEDCommand &)> sendCallback)
    {
      _leds = std::make_unique<LEDCommander>(sendCallback);
      _matrix = std::make_unique<MatrixCommander>(sendCallback);
    }

  private:
    std::unique_ptr<LEDCommander> _leds;
    std::unique_ptr<MatrixCommander> _matrix;
  };
}
