#pragma once

#include <cinttypes>
#include <vector>

class IEncoder
{
public:
  virtual ~IEncoder() = default;

  virtual size_t encode(uint8_t *buf, size_t size, uint8_t *encodedBuffer) = 0;

  virtual size_t decode(uint8_t *encodedBuffer, size_t size, uint8_t *decodedBuffer) = 0;

  virtual size_t getEncodedBufferSize(size_t unencodedBufferSize) = 0;
};