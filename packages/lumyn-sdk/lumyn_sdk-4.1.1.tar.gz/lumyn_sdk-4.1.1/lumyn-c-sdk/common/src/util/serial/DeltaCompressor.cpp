#include "lumyn/util/serial/DeltaCompressor.h"

#include <cstring>

namespace lumyn::internal {

void DeltaCompressor::encode(const uint8_t* current, const uint8_t* previous,
                             size_t size, std::vector<uint8_t>& outDelta) {
  outDelta.resize(size);

  if (!current || size == 0) {
    return;
  }

  // First frame - no previous data, just copy
  if (!previous) {
    std::memcpy(outDelta.data(), current, size);
    return;
  }

  // XOR current against previous
  size_t i = 0;

#if defined(__ARM_ARCH) || defined(__x86_64__) || defined(_M_X64)
  // Check if all pointers are 4-byte aligned
  const bool isAligned =
      (reinterpret_cast<uintptr_t>(current) % 4 == 0) &&
      (reinterpret_cast<uintptr_t>(previous) % 4 == 0) &&
      (reinterpret_cast<uintptr_t>(outDelta.data()) % 4 == 0);

  if (isAligned) {
    const size_t alignedSize = size & ~3;
    for (; i < alignedSize; i += 4) {
      uint32_t curr = *reinterpret_cast<const uint32_t*>(current + i);
      uint32_t prev = *reinterpret_cast<const uint32_t*>(previous + i);
      *reinterpret_cast<uint32_t*>(outDelta.data() + i) = curr ^ prev;
    }
  }
#endif

  // Handle remaining bytes
  for (; i < size; ++i) {
    outDelta[i] = current[i] ^ previous[i];
  }
}

void DeltaCompressor::decode(const uint8_t* delta, const uint8_t* previous,
                             size_t size, std::vector<uint8_t>& outCurrent) {
  outCurrent.resize(size);

  if (!delta || size == 0) {
    return;
  }

  // No previous frame - delta is the actual data
  if (!previous) {
    std::memcpy(outCurrent.data(), delta, size);
    return;
  }

  // XOR delta against previous to reconstruct current
  size_t i = 0;

#if defined(__ARM_ARCH) || defined(__x86_64__) || defined(_M_X64)
  const bool isAligned =
      (reinterpret_cast<uintptr_t>(delta) % 4 == 0) &&
      (reinterpret_cast<uintptr_t>(previous) % 4 == 0) &&
      (reinterpret_cast<uintptr_t>(outCurrent.data()) % 4 == 0);

  if (isAligned) {
    const size_t alignedSize = size & ~3;
    for (; i < alignedSize; i += 4) {
      uint32_t prev = *reinterpret_cast<const uint32_t*>(previous + i);
      uint32_t deltaVal = *reinterpret_cast<const uint32_t*>(delta + i);
      *reinterpret_cast<uint32_t*>(outCurrent.data() + i) = prev ^ deltaVal;
    }
  }
#endif

  for (; i < size; ++i) {
    outCurrent[i] = previous[i] ^ delta[i];
  }
}

void DeltaCompressor::decodeInPlace(const uint8_t* delta, uint8_t* inOutBuffer,
                                    size_t size) {
  if (!delta || !inOutBuffer || size == 0) {
    return;
  }

  // XOR delta directly into buffer
  size_t i = 0;

#if defined(__ARM_ARCH) || defined(__x86_64__) || defined(_M_X64)
  const bool isAligned = (reinterpret_cast<uintptr_t>(inOutBuffer) % 4 == 0) &&
                         (reinterpret_cast<uintptr_t>(delta) % 4 == 0);

  if (isAligned) {
    const size_t alignedSize = size & ~3;
    for (; i < alignedSize; i += 4) {
      *reinterpret_cast<uint32_t*>(inOutBuffer + i) ^=
          *reinterpret_cast<const uint32_t*>(delta + i);
    }
  }
#endif

  for (; i < size; ++i) {
    inOutBuffer[i] ^= delta[i];
  }
}

}  // namespace lumyn::internal