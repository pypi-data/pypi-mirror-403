#pragma once

#include <cstdint>

namespace lumyn::internal::Transmission
{
  enum class TransmissionType : uint8_t
  {
    Request = 0,
    Response,
    Event,
    Command,
    File,
    ModuleData
  };
} // namespace lumyn::internal::Transmission