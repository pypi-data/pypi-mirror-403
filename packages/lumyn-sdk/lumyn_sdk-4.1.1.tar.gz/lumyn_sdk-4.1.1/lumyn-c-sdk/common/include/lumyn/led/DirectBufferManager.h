// DirectBufferManager - Higher-level manager for DirectLEDBuffer
// Provides automatic periodic full refreshes to prevent delta error accumulation
// Wraps DirectLEDBuffer with frame counting and automatic refresh logic

#pragma once

#include "lumyn/led/DirectLEDBuffer.h"

#include <cstdint>
#include <string_view>
#include <vector>

namespace lumyn::internal
{

  /**
   * Higher-level manager that wraps DirectLEDBuffer with automatic
   * periodic full refreshes to prevent delta error accumulation.
   *
   * Usage:
   *   DirectBufferManager manager("zone1", 150, 100);  // 50 LEDs, refresh every 100 frames
   *   auto cmd = manager.update(rgbData);
   *   transmissionPort.send(cmd.data(), cmd.size());
   */
  class DirectBufferManager
  {
  public:
    /**
     * Construct a manager for a zone
     * @param zoneId Zone identifier string
     * @param length Expected buffer length in bytes (e.g., numLEDs * 3 for RGB)
     * @param fullRefreshInterval Send full buffer every N frames (default: 100, 0 to disable)
     */
    DirectBufferManager(std::string_view zoneId, size_t length, int fullRefreshInterval = 100);

    /**
     * Construct with pre-computed zone ID
     * @param zoneId Zone identifier (already hashed)
     * @param length Expected buffer length in bytes
     * @param fullRefreshInterval Send full buffer every N frames (default: 100, 0 to disable)
     */
    DirectBufferManager(uint16_t zoneId, size_t length, int fullRefreshInterval = 100);

    /**
     * Update LED buffer, automatically using delta or full based on frame count.
     *
     * @param data Raw RGB bytes
     * @param length Number of bytes
     * @return Command bytes ready to send (empty if length mismatch)
     */
    std::vector<uint8_t> update(const uint8_t *data, size_t length);

    /**
     * Update with std::vector input
     */
    std::vector<uint8_t> update(const std::vector<uint8_t> &data);

    /**
     * Force a full buffer update and reset frame counter.
     */
    std::vector<uint8_t> forceFullUpdate(const uint8_t *data, size_t length);

    /**
     * Reset state, forcing next update to be full.
     */
    void reset();

    /**
     * Get the underlying buffer
     */
    DirectLEDBuffer &buffer() { return _buffer; }
    const DirectLEDBuffer &buffer() const { return _buffer; }

    /**
     * Get the expected buffer length
     */
    size_t bufferLength() const { return _buffer.bufferLength(); }

    /**
     * Get/set the full refresh interval
     */
    int fullRefreshInterval() const { return _fullRefreshInterval; }
    void setFullRefreshInterval(int interval) { _fullRefreshInterval = interval; }

    /**
     * Get current frame count since last full refresh
     */
    int frameCount() const { return _frameCount; }

  private:
    DirectLEDBuffer _buffer;
    int _fullRefreshInterval;
    int _frameCount;
  };

} // namespace lumyn::internal