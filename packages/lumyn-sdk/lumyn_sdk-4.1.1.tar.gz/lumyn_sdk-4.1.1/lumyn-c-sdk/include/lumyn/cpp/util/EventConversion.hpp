#pragma once

#include "lumyn/types/events.h"
#include "lumyn/cpp/types.hpp"

namespace lumyn::internal {

/**
 * @brief Convert a C API lumyn_event_t to a C++ lumyn::Event
 * @param c_evt The C event structure
 * @return A C++ Event object wrapping the C event data
 */
inline lumyn::Event from_c_event(const lumyn_event_t& c_evt) {
  return lumyn::Event(c_evt);
}

} // namespace lumyn::internal
