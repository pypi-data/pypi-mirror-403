#pragma once
#include <stdint.h>

#include <array>
#include <atomic>

template <size_t N>
class RxByteRing {
 public:
  RxByteRing() {
    static_assert((N & (N - 1)) == 0, "N must be power-of-two");
    _head.store(0);
    _tail.store(0);
  }

  inline bool push(uint8_t b) {
    uint32_t head = _head.load(std::memory_order_relaxed);
    uint32_t next = (head + 1) & (N - 1);
    if (next == _tail.load(std::memory_order_acquire)) {
      return false;  // full
    }
    _buf[head] = b;
    _head.store(next, std::memory_order_release);
    return true;
  }

  inline bool pop(uint8_t& out) {
    uint32_t tail = _tail.load(std::memory_order_relaxed);
    if (tail == _head.load(std::memory_order_acquire)) {
      return false;  // empty
    }
    out = _buf[tail];
    _tail.store((tail + 1) & (N - 1), std::memory_order_release);
    return true;
  }

  inline size_t available() const {
    return (_head.load() - _tail.load()) & (N - 1);
  }

 private:
  std::array<uint8_t, N> _buf;
  std::atomic<uint32_t> _head;
  std::atomic<uint32_t> _tail;
};
