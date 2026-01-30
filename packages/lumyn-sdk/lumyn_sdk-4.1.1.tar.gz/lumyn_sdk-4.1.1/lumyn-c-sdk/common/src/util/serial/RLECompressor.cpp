#include "lumyn/util/serial/RLECompressor.h"

#include "lumyn/Constants.h"
#include "lumyn/util/logging/ConsoleLogger.h"
#include "lumyn/util/serial/TransmissionPool.h"

namespace lumyn::internal {

using namespace Transmission;

// Type alias to avoid ambiguity with namespace name on MSVC
using TransmissionClass = ::lumyn::internal::Transmission::Transmission;

// ============================================================================
// COMPRESS – POOL SAFE
// ============================================================================
TransmissionClass* RLECompressor::compress(
    TransmissionClass* tx) {
  if (!tx) return nullptr;

  const TransmissionHeader* h = tx->getHeader();
  if (!h || h->dataLength == 0) return tx;

  if (h->flags.compressed) return tx;

  const uint8_t* payload = tx->getBuffer() + sizeof(TransmissionHeader);
  size_t payloadLen = h->dataLength;

  if (!shouldCompress(payload, payloadLen)) {
    return tx;
  }

  // Output buffer temporary scratch on stack
  static constexpr size_t OUT_CAP = kLargeSlotSize;
  uint8_t outBuf[OUT_CAP];

  const size_t compressedLen =
      compressToBuffer(payload, payloadLen, outBuf, OUT_CAP);

  // If not smaller, skip
  if (compressedLen >= payloadLen) {
    return tx;
  }

  // Build new pooled Transmission::Transmission
  const size_t totalSize = sizeof(TransmissionHeader) + compressedLen;

  TransmissionSlot* slot = TransmissionPool::instance().acquire(totalSize);
  if (!slot) {
    ConsoleLogger::getInstance().logWarning("RLECompressor", 
        "No pool slot, skipping compression");
    return tx;
  }

  uint8_t* base = slot->buffer;

  auto* nh = reinterpret_cast<TransmissionHeader*>(base);
  *nh = *h;
  nh->dataLength = compressedLen;
  nh->flags.compressed = 1;

  memcpy(base + sizeof(TransmissionHeader), outBuf, compressedLen);

  TransmissionClass* newTx =
      TransmissionClass::adoptSlot(slot);

  tx->unref();  // replace original
  return newTx;
}

// ============================================================================
// DECOMPRESS – POOL SAFE
// ============================================================================
TransmissionClass* RLECompressor::decompress(
    TransmissionClass* tx) {
  if (!tx) return nullptr;

  const TransmissionHeader* h = tx->getHeader();
  if (!h || h->dataLength == 0) return tx;
  if (!h->flags.compressed) return tx;

  const uint8_t* in = tx->getBuffer() + sizeof(TransmissionHeader);
  size_t inLen = h->dataLength;

  static constexpr size_t OUT_CAP = kLargeSlotSize;
  uint8_t outBuf[OUT_CAP];

  const size_t outLen = decompressToBuffer(in, inLen, outBuf, OUT_CAP);

  // Build new pooled transmission
  const size_t total = sizeof(TransmissionHeader) + outLen;

  TransmissionSlot* slot = TransmissionPool::instance().acquire(total);
  if (!slot) {
    ConsoleLogger::getInstance().logError("RLECompressor", 
        "No pool slot for decompress");
    return tx;  // fallback
  }

  uint8_t* base = slot->buffer;

  auto* nh = reinterpret_cast<TransmissionHeader*>(base);
  *nh = *h;
  nh->dataLength = outLen;
  nh->flags.compressed = 0;

  memcpy(base + sizeof(TransmissionHeader), outBuf, outLen);

  TransmissionClass* outTx =
      TransmissionClass::adoptSlot(slot);

  tx->unref();
  return outTx;
}

// ============================================================================
// HEURISTIC
// ============================================================================
bool RLECompressor::shouldCompress(const uint8_t* d, size_t n) {
  if (n < 32) return false;

  constexpr size_t SAMP = 64;
  constexpr size_t STRD = 8;

  size_t rep = 0, sam = 0;
  for (size_t i = 0; i + 1 < n && sam < SAMP; i += STRD) {
    if (d[i] == d[i + 1]) rep++;
    sam++;
  }

  return (rep * 4 > sam);  // >25% repetition
}

// ============================================================================
// LOW LEVEL COMPRESS (NO HEAP)
// ============================================================================
size_t RLECompressor::compressToBuffer(const uint8_t* in, size_t len,
                                       uint8_t* out, size_t cap) {
  size_t wi = 0;
  size_t i = 0;

  while (i < len) {
    uint8_t v = in[i];

    // Count run
    size_t run = 1;
    while ((i + run < len) && (in[i + run] == v) && (run < RLE_MAX_RUN)) {
      run++;
    }

    // Encode run
    if (run >= RLE_MIN_RUN) {
      if (wi + 3 > cap) break;
      out[wi++] = RLE_RUN_MARKER;
      out[wi++] = uint8_t(run - RLE_MIN_RUN);
      out[wi++] = v;
      i += run;
      continue;
    }

    // Literal
    size_t litStart = i;
    size_t litCount = 1;
    i++;

    while (i < len && litCount < 125) {
      uint8_t next = in[i];

      // If next forms a run, stop literal
      if (i + RLE_MIN_RUN <= len) {
        size_t probe = 1;
        while (probe < RLE_MIN_RUN && (i + probe < len) &&
               in[i + probe] == next) {
          probe++;
        }
        if (probe >= RLE_MIN_RUN) break;
      }

      litCount++;
      i++;
    }

    // Encode literal
    if (litCount == 1 && in[litStart] < RLE_LITERAL_MARKER) {
      if (wi + 1 > cap) break;
      out[wi++] = in[litStart];
    } else {
      if (wi + 2 + litCount > cap) break;
      out[wi++] = RLE_LITERAL_MARKER;
      out[wi++] = uint8_t(litCount - 1);
      memcpy(out + wi, in + litStart, litCount);
      wi += litCount;
    }
  }

  return wi;
}

// ============================================================================
// LOW LEVEL DECOMPRESS (NO HEAP)
// ============================================================================
size_t RLECompressor::decompressToBuffer(const uint8_t* in, size_t len,
                                         uint8_t* out, size_t cap) {
  size_t wi = 0;
  size_t i = 0;

  while (i < len) {
    uint8_t m = in[i++];

    // Run
    if (m == RLE_RUN_MARKER && i + 1 < len) {
      uint8_t count = in[i++] + RLE_MIN_RUN;
      uint8_t value = in[i++];

      if (wi + count > cap) break;
      memset(out + wi, value, count);
      wi += count;
      continue;
    }

    // Literal seq
    if (m == RLE_LITERAL_MARKER && i < len) {
      uint8_t cnt = in[i++] + 1;
      if (i + cnt > len) cnt = (len - i);

      if (wi + cnt > cap) break;
      memcpy(out + wi, in + i, cnt);
      wi += cnt;
      i += cnt;
      continue;
    }

    // Single literal
    if (wi + 1 > cap) break;
    out[wi++] = m;
  }

  return wi;
}

}  // namespace lumyn::internal
