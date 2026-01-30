#pragma once

#include <cinttypes>
#include <mutex>

namespace lumyn::internal {

template <typename T>
class CircularBuffer
{
public:
  CircularBuffer(uint32_t capacity) : _readPos{0}, _writePos{0}, _inUse{0}, _capacity{capacity}
  {
    _buf = new T[capacity];
  }

  [[nodiscard]] constexpr uint32_t size() noexcept
  {
    std::lock_guard lock(_mtx);
    return _inUse;
  }

  [[nodiscard]] constexpr uint32_t capacity() noexcept
  {
    return _capacity;
  }

  void push(T const &t) noexcept
  {
    std::lock_guard<std::mutex> lock(_mtx);
    if (_inUse >= _capacity)
    {
      pop();
    }
    new (&_buf[_writePos]) T(t);
    increment_write_pos();
  }

  // Add overload for move semantics
  void push(T &&t) noexcept
  {
    std::lock_guard<std::mutex> lock(_mtx);
    if (_inUse >= _capacity)
    {
      pop();
    }
    new (&_buf[_writePos]) T(std::move(t));
    increment_write_pos();
  }

  [[nodiscard]] T front()
  {
    std::lock_guard<std::mutex> lock(_mtx);
    return _buf[_readPos];
  }

  void pop() noexcept
  {
    std::lock_guard<std::mutex> lock(_mtx);
    if (!_inUse)
      return;

    _buf[_readPos].~T();
    increment_read_pos();
  }

  ~CircularBuffer()
  {
    std::lock_guard<std::mutex> lock(_mtx);

    while (_inUse)
    {
      pop();
    }

    delete[] _buf;
  }

private:
  inline void increment_write_pos() noexcept
  {
    _writePos = (_writePos + 1) & (_capacity - 1); // Faster than modulo for power-of-2
    ++_inUse;
  }

  inline void increment_read_pos() noexcept
  {
    _readPos = (_readPos + 1) & (_capacity - 1); // Faster than modulo for power-of-2
    --_inUse;
  }

  T *_buf;
  uint32_t _readPos;
  uint32_t _writePos;
  uint32_t _inUse;
  const uint32_t _capacity;
  std::mutex _mtx;
};

} // namespace lumyn::internal