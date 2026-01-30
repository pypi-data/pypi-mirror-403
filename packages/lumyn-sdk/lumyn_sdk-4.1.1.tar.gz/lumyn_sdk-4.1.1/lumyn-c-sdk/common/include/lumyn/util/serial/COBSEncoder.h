#pragma once

#include <iostream>

#include "lumyn/util/serial/IEncoder.h"

namespace lumyn::internal
{

  class COBSEncoder : public IEncoder
  {
  public:
    size_t encode(uint8_t *buf, size_t size, uint8_t *encodedBuffer) override;

    size_t decode(uint8_t *encodedBuffer, size_t size, uint8_t *decodedBuffer) override;

    size_t getEncodedBufferSize(size_t unencodedBufferSize) override;
  };
} // namespace lumyn::internal