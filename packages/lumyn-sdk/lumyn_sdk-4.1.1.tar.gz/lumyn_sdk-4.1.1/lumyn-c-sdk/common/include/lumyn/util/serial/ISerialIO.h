#pragma once

#include <cstdint>
#include <functional>

namespace lumyn::internal
{
  class ISerialIO
  {
  public:
    virtual ~ISerialIO() = default;
    
    virtual void writeBytes(const uint8_t* data, size_t length) = 0;
    
    virtual void setReadCallback(std::function<void(const uint8_t*, size_t)> callback) = 0;
  };
}