#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <functional>
#include <memory>
#include <vector>

#include "lumyn/cpp/export.hpp"
#include "lumyn/c/lumyn_sdk.h"

namespace lumyn::internal {
  class DirectBufferManager;
}

namespace lumyn::device
{

  /**
   * @brief DirectLED provides efficient, low-level LED control with delta compression.
   *
   * This class accepts arrays of lumyn_color_t and sends the data directly to
   * ConnectorX hardware with automatic delta compression for optimal bandwidth usage.
   *
   * Use this when you need per-pixel control while still benefiting from
   * ConnectorX's efficient protocol.
   *
   * Example usage:
   * @code
   * // Create DirectLED for a zone
   * auto directLed = device.CreateDirectLED("zone1", 60);
   *
   * // Create a color buffer
   * std::vector<lumyn_color_t> colors(60);
   *
   * // In your periodic method:
   * for (int i = 0; i < 60; i++) {
   *   colors[i] = {static_cast<uint8_t>(i * 4), 0, static_cast<uint8_t>(255 - i * 4)};
   * }
   * directLed.Update(colors);
   * @endcode
   */
  class LUMYN_SDK_CPP_API DirectLED
  {
  public:
    /** Bytes per LED (RGB = 3 bytes: red, green, blue) */
    static constexpr size_t kBytesPerLed = 3;

    /**
     * @brief Creates a DirectLED controller for a zone.
     *
     * @param instance The device instance (cx_base_t*)
     * @param zone_id The zone ID to control
     * @param num_leds Number of LEDs in the zone
     * @param full_refresh_interval How often to force a full refresh (default 100, 0 to disable)
     */
    DirectLED(cx_base_t *instance,
              std::string_view zone_id,
              size_t num_leds,
              int full_refresh_interval = 100);

    /**
     * @brief Creates a DirectLED controller that uses a direct-send callback.
     *
     * This is used for pure C++ usage where no cx_base_t is available.
     */
    DirectLED(std::function<lumyn_error_t(uint16_t, const uint8_t*, size_t, bool)> sender,
              std::string_view zone_id,
              size_t num_leds,
              int full_refresh_interval = 100);

    ~DirectLED();

    // Non-copyable
    DirectLED(const DirectLED &) = delete;
    DirectLED &operator=(const DirectLED &) = delete;

    // Movable
    DirectLED(DirectLED &&other) noexcept;
    DirectLED &operator=(DirectLED &&other) noexcept;

    /**
     * @brief Update the LEDs with an array of colors.
     * Uses delta compression to only send changed pixels.
     *
     * @param colors Pointer to array of lumyn_color_t values
     * @param count Number of colors in the array
     * @return true if the update was successful
     */
    bool Update(const lumyn_color_t *colors, size_t count);

    /**
     * @brief Update the LEDs with a vector of colors.
     * Uses delta compression to only send changed pixels.
     *
     * @param colors Vector of lumyn_color_t values
     * @return true if the update was successful
     */
    bool Update(const std::vector<lumyn_color_t> &colors);

    /**
     * @brief Update the LEDs with raw RGB data.
     * Uses delta compression to only send changed pixels.
     *
     * @param rgb_data Raw RGB bytes (3 bytes per LED: R, G, B)
     * @param length Number of bytes in the array
     * @return true if the update was successful
     */
    bool UpdateRaw(const uint8_t *rgb_data, size_t length);

    /**
     * @brief Force a full update of the LEDs (no delta compression).
     * Use this after significant changes or to ensure synchronization.
     *
     * @param colors Pointer to array of lumyn_color_t values
     * @param count Number of colors in the array
     * @return true if the update was successful
     */
    bool ForceFullUpdate(const lumyn_color_t *colors, size_t count);

    /**
     * @brief Force a full update with a vector of colors.
     *
     * @param colors Vector of lumyn_color_t values
     * @return true if the update was successful
     */
    bool ForceFullUpdate(const std::vector<lumyn_color_t> &colors);

    /**
     * @brief Force a full update with raw RGB data.
     *
     * @param rgb_data Raw RGB bytes (3 bytes per LED: R, G, B)
     * @param length Number of bytes in the array
     * @return true if the update was successful
     */
    bool ForceFullUpdateRaw(const uint8_t *rgb_data, size_t length);

    /**
     * @brief Reset the internal buffer state.
     * Forces the next update to be a full update.
     */
    void Reset();

    /**
     * @brief Set the full refresh interval.
     *
     * @param interval Number of updates between full refreshes (0 to disable)
     */
    void SetFullRefreshInterval(int interval);

    /**
     * @brief Get the number of LEDs this DirectLED controls.
     *
     * @return The number of LEDs
     */
    size_t GetLength() const;

    /**
     * @brief Get the expected buffer length in bytes.
     *
     * @return The expected number of bytes (num_leds * 3)
     */
    size_t GetExpectedBufferLength() const;

    /**
     * @brief Check if the DirectLED was successfully initialized.
     *
     * @return true if initialized
     */
    bool IsInitialized() const;

    /**
     * @brief Get the zone ID this DirectLED controls.
     *
     * @return The zone ID
     */
    const char *GetZoneId() const;

  private:
    lumyn_direct_led_t *handle_{nullptr};
    size_t num_leds_{0};
    std::string zone_id_;
    std::unique_ptr<lumyn::internal::DirectBufferManager> buffer_manager_;
    std::vector<uint8_t> rgb_buffer_;
    std::function<lumyn_error_t(uint16_t, const uint8_t*, size_t, bool)> send_direct_;
  };

} // namespace lumyn::device
