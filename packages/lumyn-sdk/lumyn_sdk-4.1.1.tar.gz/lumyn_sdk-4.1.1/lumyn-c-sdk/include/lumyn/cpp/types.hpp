/**
 * @file types.hpp
 * @brief Convenience wrapper for all Lumyn C types
 * 
 * This header includes all the C type definitions from lumyn/types/
 * and provides C++ namespace aliases for convenience.
 * 
 * Usage:
 *   #include <lumyn/cpp/types.hpp>
 *   
 *   void handleStatus(lumyn::Status status) { ... }
 */
#pragma once

#include <lumyn/types/status.h>
#include <lumyn/types/events.h>
#include <lumyn/types/led_command.h>
#include <lumyn/types/animation.h>

#include <string>

namespace lumyn {

// Status types
using Status = lumyn_status_t;

/**
 * @brief Connection and enablement status
 */
struct ConnectionStatus {
  bool connected{false};
  bool enabled{false};
};

/**
 * @brief C++ RAII wrapper for lumyn_event_t
 * 
 * Safely manages the lifetime of the extra_message string.
 * Copyable and movable.
 */
class Event {
public:
  Event() = default;
  using Data = decltype(lumyn_event_t{}.data);

  // Construct from C struct (makes a deep copy of message)
  explicit Event(const lumyn_event_t& src) {
    event_ = src;
    event_.extra_message = nullptr; // We don't own the source string
    if (src.extra_message) {
      message_ = src.extra_message;
    }
  }

  // Copy constructor
  Event(const Event& other) : event_(other.event_), message_(other.message_) {
    event_.extra_message = nullptr;
  }

  // Move constructor
  Event(Event&& other) noexcept : event_(other.event_), message_(std::move(other.message_)) {
    event_.extra_message = nullptr;
    other.event_.extra_message = nullptr;
  }

  // Assignment
  Event& operator=(const Event& other) {
    if (this != &other) {
      event_ = other.event_;
      message_ = other.message_;
      event_.extra_message = nullptr;
    }
    return *this;
  }

  Event& operator=(Event&& other) noexcept {
    if (this != &other) {
      event_ = other.event_;
      message_ = std::move(other.message_);
      event_.extra_message = nullptr;
    }
    return *this;
  }

  // Accessors
  lumyn_event_type_t getType() const { return event_.type; }
  
  const char* getExtraMessage() const {
    return message_.empty() ? nullptr : message_.c_str();
  }

  // Expose raw data union safely
  const Data& getData() const { return event_.data; }

  // Check specific types
  bool isError() const { return event_.type == LUMYN_EVENT_ERROR; }
  bool isConnected() const { return event_.type == LUMYN_EVENT_CONNECTED; }
  bool isDisconnected() const { return event_.type == LUMYN_EVENT_DISCONNECTED; }

private:
  lumyn_event_t event_{};
  std::string message_;
};

// Event type aliases
using RawEvent = lumyn_event_t;
using EventType = lumyn_event_type_t;
using DisabledCause = lumyn_disabled_cause_t;
using ConnectionType = lumyn_connection_type_t;
using ErrorType = lumyn_error_type_t;
using FatalErrorType = lumyn_fatal_error_type_t;

// LED command types
using MatrixTextScrollDirection = lumyn_matrix_text_scroll_direction_t;
using MatrixTextFont = lumyn_matrix_text_font_t;
using MatrixTextAlign = lumyn_matrix_text_align_t;
using MatrixTextFlags = lumyn_matrix_text_flags_t;

// Animation types (aliases already provided in animation.h under lumyn::led)
// But we can expose the enum type directly in lumyn namespace too
using Animation = lumyn_animation_t;

} // namespace lumyn
