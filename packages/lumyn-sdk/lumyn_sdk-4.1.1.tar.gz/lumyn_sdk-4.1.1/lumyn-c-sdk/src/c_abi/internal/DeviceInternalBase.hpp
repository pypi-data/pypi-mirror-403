#pragma once

#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/cpp/types.hpp>
#include <lumyn/domain/event/Event.h>
#include <lumyn/eventing/EventHandler.h>
#include <functional>
#include <vector>
#include <mutex>
#include <optional>
#include <memory>

namespace lumyn_c_sdk::internal {

/**
 * @brief Common base interface for ConnectorXInternal and ConnectorXAnimateInternal
 * 
 * This interface provides the common methods needed by the C ABI layer
 * for event handling and device management.
 */
class DeviceInternalBase {
public:
    virtual ~DeviceInternalBase() = default;
    
    // Event dispatch function type
    using DispatchFn = std::function<void(const lumyn::internal::Eventing::Event&, const std::vector<std::pair<lumyn_event_callback_t, void*>>&)>;

    virtual void SetDispatchFunction(DispatchFn fn) = 0;
    virtual void AddEventHandler(lumyn_event_callback_t cb, void* user) = 0;
    virtual void AddInternalEventHandler(std::shared_ptr<lumyn::internal::Eventing::EventHandler> handler) = 0;
    virtual bool IsConnected() const = 0;
    virtual void Disconnect() = 0;
    virtual void NotifyConnectionState(bool connected) = 0;
    virtual std::optional<lumyn::Event> GetLatestEvent() = 0;
    virtual void GetDeviceHealth(lumyn_status_t* out) = 0;
    virtual void GetConnectionStatus(bool* connected, bool* enabled) = 0;
    virtual void SendConfigurationInternal(const uint8_t* data, uint32_t length) = 0;
    virtual void SetConnectionStateCallback(void (*cb)(bool, void*), void* user) = 0;
};

} // namespace lumyn_c_sdk::internal
