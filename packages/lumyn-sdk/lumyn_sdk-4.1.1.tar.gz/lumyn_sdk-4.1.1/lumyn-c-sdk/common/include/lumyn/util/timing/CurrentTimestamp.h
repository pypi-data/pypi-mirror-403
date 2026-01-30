#pragma once

#include <chrono>
#include <cinttypes>

namespace lumyn::internal::util::timing
{
  class CurrentTimestamp
  {
  public:
    static int64_t GetCurrentTimestampMs()
    {
      auto now = std::chrono::steady_clock::now();
      auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch());
      return ms.count();
    }
  };
} 