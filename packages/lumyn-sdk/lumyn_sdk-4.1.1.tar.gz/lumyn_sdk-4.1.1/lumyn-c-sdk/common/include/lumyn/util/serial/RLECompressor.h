#pragma once

#include <cstddef>
#include <cstdint>

#include "lumyn/domain/transmission/Transmission.h"

namespace lumyn::internal {

// Forward declare to avoid ambiguity on MSVC
using TransmissionClass = ::lumyn::internal::Transmission::Transmission;

class RLECompressor {
 public:
  static TransmissionClass* compress(TransmissionClass* tx);
  static TransmissionClass* decompress(TransmissionClass* tx);

 private:
  static constexpr uint8_t RLE_RUN_MARKER = 0xFF;
  static constexpr uint8_t RLE_LITERAL_MARKER = 0xFE;
  static constexpr uint8_t RLE_MIN_RUN = 4;
  static constexpr uint8_t RLE_MAX_RUN = 130;

  static bool shouldCompress(const uint8_t* data, size_t len);

  // No std::vector – work on caller-provided buffers
  static size_t compressToBuffer(const uint8_t* in, size_t len, uint8_t* out,
                                 size_t outCap);

  static size_t decompressToBuffer(const uint8_t* in, size_t len, uint8_t* out,
                                   size_t outCap);
};

}  // namespace lumyn::internal
