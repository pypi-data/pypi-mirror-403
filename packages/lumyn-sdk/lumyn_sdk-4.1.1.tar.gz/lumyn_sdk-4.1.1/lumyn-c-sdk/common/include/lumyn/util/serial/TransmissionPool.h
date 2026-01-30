#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

#if defined(FREERTOS) || defined(ARDUINO_ARCH_RP2040)
#define TP_USE_FREERTOS 1
#else
#define TP_USE_FREERTOS 0
#endif

#if TP_USE_FREERTOS
#include <FreeRTOS.h>
#include <semphr.h>
#else
#include <mutex>
#endif

namespace lumyn::internal::Transmission {

// === CONFIGURABLE POOL LAYOUT ===
// These can be overridden externally via compiler defines (e.g.,
// -DTRANSMISSION_POOL_SMALL_SLOT_COUNT=32) Projects using this library should
// set these in their build system if different values are needed.

#ifndef TRANSMISSION_POOL_SMALL_SLOT_SIZE
#define TRANSMISSION_POOL_SMALL_SLOT_SIZE 512
#endif

#ifndef TRANSMISSION_POOL_SMALL_SLOT_COUNT
#define TRANSMISSION_POOL_SMALL_SLOT_COUNT 32
#endif

#ifndef TRANSMISSION_POOL_LARGE_SLOT_SIZE
#define TRANSMISSION_POOL_LARGE_SLOT_SIZE 4096
#endif

#ifndef TRANSMISSION_POOL_LARGE_SLOT_COUNT
#define TRANSMISSION_POOL_LARGE_SLOT_COUNT 8
#endif

constexpr size_t kSmallSlotSize = TRANSMISSION_POOL_SMALL_SLOT_SIZE;
constexpr size_t kSmallSlotCount = TRANSMISSION_POOL_SMALL_SLOT_COUNT;

constexpr size_t kLargeSlotSize = TRANSMISSION_POOL_LARGE_SLOT_SIZE;
constexpr size_t kLargeSlotCount = TRANSMISSION_POOL_LARGE_SLOT_COUNT;

constexpr size_t kMaxTransmissionSize = kLargeSlotSize;

// === POOL SLOT ===
struct TransmissionSlot {
  uint8_t* buffer = nullptr;
  size_t capacity = 0;
  size_t length = 0;
  uint16_t refCount = 0;
  bool inUse = false;
  bool isRxScratch = false;
};

// === POOL ===
class TransmissionPool {
 public:
  static TransmissionPool& instance();

  TransmissionSlot* acquire(size_t totalSize);
  void retain(TransmissionSlot* slot);
  bool release(TransmissionSlot* slot);

 private:
  TransmissionPool();
  TransmissionPool(const TransmissionPool&) = delete;
  TransmissionPool& operator=(const TransmissionPool&) = delete;

 private:
  alignas(4) uint8_t _smallBuffers[kSmallSlotCount][kSmallSlotSize];
  alignas(4) uint8_t _largeBuffers[kLargeSlotCount][kLargeSlotSize];

  std::array<TransmissionSlot, kSmallSlotCount> _smallSlots;
  std::array<TransmissionSlot, kLargeSlotCount> _largeSlots;

#if TP_USE_FREERTOS
  StaticSemaphore_t _mutexBuf;
  SemaphoreHandle_t _mutex;
#else
  // std::mutex for host builds
  std::mutex _mutex;
#endif
};

}  // namespace lumyn::internal::Transmission
