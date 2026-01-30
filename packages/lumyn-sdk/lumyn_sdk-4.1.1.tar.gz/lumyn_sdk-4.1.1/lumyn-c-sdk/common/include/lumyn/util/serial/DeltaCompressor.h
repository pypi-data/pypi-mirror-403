#pragma once

#include <cstdint>
#include <cstring>
#include <vector>

namespace lumyn::internal {

/**
 * Simple XOR-based delta compression
 * Stores only the differences between consecutive frames
 */
class DeltaCompressor {
 public:
  /**
   * Encode: XOR current buffer against previous to produce delta
   * @param current Current data buffer
   * @param previous Previous data buffer (null if first frame)
   * @param size Size in bytes
   * @param outDelta Output delta buffer (will be resized to size)
   */
  static void encode(const uint8_t* current, const uint8_t* previous,
                     size_t size, std::vector<uint8_t>& outDelta);

  /**
   * Decode: Apply XOR delta to previous buffer to reconstruct current
   * @param delta Delta buffer
   * @param previous Previous data buffer
   * @param size Size in bytes
   * @param outCurrent Output reconstructed buffer (will be resized to size)
   */
  static void decode(const uint8_t* delta, const uint8_t* previous, size_t size,
                     std::vector<uint8_t>& outCurrent);

  /**
   * In-place decode: Apply delta directly to buffer
   * @param delta Delta buffer
   * @param inOutBuffer Buffer to modify (contains previous, will contain
   * current)
   * @param size Size in bytes
   */
  static void decodeInPlace(const uint8_t* delta, uint8_t* inOutBuffer,
                            size_t size);

  /**
   * Encode for typed arrays (e.g., CRGB[], uint32_t[])
   */
  template <typename T>
  static void encode(const T* current, const T* previous, size_t count,
                     std::vector<uint8_t>& outDelta) {
    encode(reinterpret_cast<const uint8_t*>(current),
           reinterpret_cast<const uint8_t*>(previous), count * sizeof(T),
           outDelta);
  }

  /**
   * Decode for typed arrays
   */
  template <typename T>
  static void decode(const uint8_t* delta, const T* previous, size_t count,
                     std::vector<T>& outCurrent) {
    std::vector<uint8_t> temp;
    decode(delta, reinterpret_cast<const uint8_t*>(previous), count * sizeof(T),
           temp);

    outCurrent.resize(count);
    std::memcpy(outCurrent.data(), temp.data(), count * sizeof(T));
  }

  /**
   * In-place decode for typed arrays
   */
  template <typename T>
  static void decodeInPlace(const uint8_t* delta, T* inOutBuffer,
                            size_t count) {
    decodeInPlace(delta, reinterpret_cast<uint8_t*>(inOutBuffer),
                  count * sizeof(T));
  }
};

}  // namespace lumyn::internal