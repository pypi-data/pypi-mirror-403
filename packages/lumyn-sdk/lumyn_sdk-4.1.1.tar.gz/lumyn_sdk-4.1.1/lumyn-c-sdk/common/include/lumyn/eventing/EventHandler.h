#pragma once

#include <lumyn/domain/event/Event.h>

#include <functional>

namespace lumyn {
namespace internal {
namespace Eventing {

/**
 * @brief Event handler wrapper for internal event processing
 * 
 * EventHandler provides a simple wrapper around event handling functions
 * for processing internal Lumyn events. This is useful for SDKs and firmware
 * that use the common library and need to handle events.
 * 
 * Example usage:
 * @code
 * auto handler = std::make_shared<EventHandler>([](const Event& evt) {
 *     if (evt.header.type == EventType::HeartBeat) {
 *         // Process heartbeat
 *     }
 * });
 * 
 * // Add to device (if device supports internal event handlers)
 * device->AddInternalEventHandler(handler);
 * @endcode
 */
class EventHandler
{
public:
  EventHandler(std::function<void(const Event &evt)> handler) : _handler{handler} {}
  
  void Handle(const Event &evt)
  {
    if (_handler) {
      _handler(evt);
    }
  }

private:
  std::function<void(const Event &evt)> _handler;
};

} // namespace Eventing
} // namespace internal
} // namespace lumyn