#include "lumyn/util/serial/TransmissionPool.h"

#include <mutex>

#include "lumyn/Constants.h"
#include "lumyn/util/logging/ConsoleLogger.h"

namespace lumyn::internal::Transmission {

TransmissionPool& TransmissionPool::instance() {
  static TransmissionPool pool;
  return pool;
}

TransmissionPool::TransmissionPool() {
  for (size_t i = 0; i < kSmallSlotCount; ++i) {
    _smallSlots[i].buffer = _smallBuffers[i];
    _smallSlots[i].capacity = kSmallSlotSize;
  }
  for (size_t i = 0; i < kLargeSlotCount; ++i) {
    _largeSlots[i].buffer = _largeBuffers[i];
    _largeSlots[i].capacity = kLargeSlotSize;
  }

#if TP_USE_FREERTOS
  _mutex = xSemaphoreCreateMutexStatic(&_mutexBuf);
  configASSERT(_mutex);
#endif
}

TransmissionSlot* TransmissionPool::acquire(size_t totalSize) {
#if TP_USE_FREERTOS
  xSemaphoreTake(_mutex, portMAX_DELAY);
#else
  _mutex.lock();
#endif

  if (totalSize > kMaxTransmissionSize) {
    ConsoleLogger::getInstance().logWarning("TransmissionPool", 
        "TransmissionPool: request too large: %u", totalSize);
#if TP_USE_FREERTOS
    xSemaphoreGive(_mutex);
#else
    _mutex.unlock();
#endif
    return nullptr;
  }

  // First try small pool
  if (totalSize <= kSmallSlotSize) {
    for (auto& s : _smallSlots) {
      if (!s.inUse) {
        s.inUse = true;
        s.refCount = 1;
        s.length = totalSize;
        s.isRxScratch = false;
#if TP_USE_FREERTOS
        xSemaphoreGive(_mutex);
#else
        _mutex.unlock();
#endif
        return &s;
      }
    }
  }

  // Fallback to large
  for (auto& s : _largeSlots) {
    if (!s.inUse) {
      s.inUse = true;
      s.refCount = 1;
      s.length = totalSize;
      s.isRxScratch = false;
#if TP_USE_FREERTOS
      xSemaphoreGive(_mutex);
#else
      _mutex.unlock();
#endif
      return &s;
    }
  }

  ConsoleLogger::getInstance().logWarning("TransmissionPool", "TransmissionPool exhausted");

#if TP_USE_FREERTOS
  xSemaphoreGive(_mutex);
#else
  _mutex.unlock();
#endif
  return nullptr;
}

void TransmissionPool::retain(TransmissionSlot* slot) {
  if (!slot) return;
#if TP_USE_FREERTOS
  xSemaphoreTake(_mutex, portMAX_DELAY);
  slot->refCount++;
  xSemaphoreGive(_mutex);
#else
  std::lock_guard<std::mutex> g(_mutex);
  slot->refCount++;
#endif
}

bool TransmissionPool::release(TransmissionSlot* slot) {
  if (!slot) return false;
  bool last = false;
  ConsoleLogger::getInstance().logVerbose("TransmissionPool",
      "Releasing slot, current refCount=%u", slot->refCount);

#if TP_USE_FREERTOS
  xSemaphoreTake(_mutex, portMAX_DELAY);
  slot->refCount--;
  if (slot->refCount == 0) {
    slot->inUse = false;
    slot->length = 0;
    slot->isRxScratch = false;
    last = true;
  }
  xSemaphoreGive(_mutex);
#else
  std::lock_guard<std::mutex> g(_mutex);
  slot->refCount--;
  if (slot->refCount == 0) {
    slot->inUse = false;
    slot->length = 0;
    slot->isRxScratch = false;
    last = true;
  }
#endif

  return last;
}

}  // namespace lumyn::internal::Transmission
