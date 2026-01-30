// DirectLEDBuffer - Low-level LED buffer with delta compression
// Stores the buffer state for delta comparisons
// Does automatic padding, handles delta compression, returns command bytes
// The caller should pass the command bytes directly to TransmissionPortListener

#pragma once

#include <cstdint>
#include <string_view>
#include <vector>

namespace lumyn::internal
{

  /**
   * Manages direct LED buffer updates with automatic delta compression.
   *
   * This class tracks the current LED buffer state and generates commands
   * with delta-compressed updates. Handles 4-byte padding requirements
   * for the firmware.
   *
   * Usage:
   *   DirectLEDBuffer buffer("zone1", 150);  // 50 LEDs * 3 bytes
   *   auto cmd = buffer.update(rgbData, true);  // delta compressed
   *   transmissionPort.send(cmd.data(), cmd.size());
   */
  class DirectLEDBuffer
  {
  public:
    /**
     * Construct a DirectLEDBuffer for a specific zone
     * @param zoneId Zone identifier string (will be hashed to uint16_t)
     * @param length Expected buffer length in bytes (e.g., numLEDs * 3 for RGB)
     */
    DirectLEDBuffer(std::string_view zoneId, size_t length);

    /**
     * Construct a DirectLEDBuffer with a pre-computed zone ID
     * @param zoneId Zone identifier (already hashed)
     * @param length Expected buffer length in bytes
     */
    DirectLEDBuffer(uint16_t zoneId, size_t length);

    /**
     * Update the LED buffer and generate command bytes.
     *
     * Handles:
     * - Length validation against expected size
     * - 4-byte padding (firmware requirement)
     * - Delta compression (XOR-based) when enabled and previous buffer exists
     * - Full buffer transmission when delta not applicable
     *
     * @param data Raw RGB bytes (3 bytes per LED: R, G, B)
     * @param length Number of bytes in data
     * @param useDelta If true, attempt delta compression; if false, send full buffer
     * @return Command bytes ready to send through protocol stack (empty if length mismatch)
     */
    std::vector<uint8_t> update(const uint8_t *data, size_t length, bool useDelta = true);

    /**
     * Update with std::vector input
     */
    std::vector<uint8_t> update(const std::vector<uint8_t> &data, bool useDelta = true);

    /**
     * Force a full buffer update (no delta compression).
     * Useful for periodic full refreshes to prevent error accumulation.
     *
     * @param data Raw RGB bytes
     * @param length Number of bytes
     * @return Command bytes ready to send
     */
    std::vector<uint8_t> forceFullUpdate(const uint8_t *data, size_t length);

    /**
     * Reset the buffer state, forcing next update to be a full buffer.
     */
    void reset();

    /**
     * Get the zone ID (hashed)
     */
    uint16_t zoneId() const { return _zoneId; }

    /**
     * Get the expected buffer length
     */
    size_t bufferLength() const { return _bufferLength; }

    /**
     * Get the padded buffer length (4-byte aligned)
     */
    size_t paddedLength() const { return _paddedLength; }

    /**
     * Check if we have a previous buffer stored
     */
    bool hasPreviousBuffer() const { return !_previousBuffer.empty(); }

    /**
     * Get the size of the previous buffer (0 if none)
     */
    size_t previousBufferSize() const { return _previousBuffer.size(); }

  private:
    uint16_t _zoneId;
    size_t _bufferLength;
    size_t _paddedLength;
    std::vector<uint8_t> _previousBuffer;

    static size_t calculatePaddedLength(size_t length);
  };

} // namespace lumyn::internal
