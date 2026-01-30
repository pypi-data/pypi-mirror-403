#pragma once

#include "DeviceInternalBase.hpp"

#include <lumyn/cpp/device/BaseLumynDevice.hpp>
#include <lumyn/domain/event/Event.h>
#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/c/serial_io.h>
#include <lumyn/util/serial/ISerialIO.h>

#include <memory>
#include <mutex>
#include <optional>
#include <vector>
#include <utility>

namespace lumyn_c_sdk::internal
{

  template <typename DeviceParent>
  class ConnectorXInternalBase : public DeviceParent, public DeviceInternalBase
  {
  public:
    using DispatchFn = typename DeviceInternalBase::DispatchFn;

    explicit ConnectorXInternalBase(cx_base_t *base_ptr)
    {
      this->SetCBasePtr(base_ptr);
    }

    virtual ~ConnectorXInternalBase()
    {
      if (IsConnected())
      {
        Disconnect();
      }
    }

    // Return the C API base pointer for use with EventManager/ConfigManager
    void *GetBasePtr() override { return this->GetCBasePtr(); }
    const void *GetBasePtr() const override { return this->GetCBasePtr(); }

    DeviceParent *device() { return this; }
    const DeviceParent *device() const { return this; }

    void SetDispatchFunction(DispatchFn fn) override
    {
      std::lock_guard<std::mutex> lock(event_mutex_);
      dispatch_fn_ = std::move(fn);
    }

    void AddEventHandler(lumyn_event_callback_t cb, void *user) override
    {
      std::lock_guard<std::mutex> lock(event_mutex_);
      event_handlers_.push_back({cb, user});
    }

    void AddInternalEventHandler(std::shared_ptr<lumyn::internal::Eventing::EventHandler> handler) override
    {
      if (!handler)
        return;
      std::lock_guard<std::mutex> lock(event_mutex_);
      internal_event_handlers_.push_back(std::move(handler));
    }

    bool IsConnected() const override
    {
      return DeviceParent::IsConnected();
    }

    void Disconnect() override
    {
      DeviceParent::Disconnect();
    }

    void NotifyConnectionState(bool connected) override
    {
      NotifyConnectionStateImpl(connected);
    }

    std::optional<::lumyn::Event> GetLatestEvent() override
    {
      // DeviceParent (ConnectorX or ConnectorXAnimate via BaseConnectorXVariant)
      // already returns std::optional<lumyn::Event>
      return DeviceParent::GetLatestEvent();
    }

    void GetDeviceHealth(lumyn_status_t *out) override
    {
      if (!out)
        return;
      // Get status from the latest heartbeat via the base device
      // Call BaseLumynDevice::GetCurrentStatus() directly to get Eventing::Status
      // (BaseConnectorXVariant::GetCurrentStatus() returns lumyn::ConnectionStatus which shadows it)
      auto status = static_cast<lumyn::internal::BaseLumynDevice *>(this)->GetCurrentStatus();
      *out = static_cast<lumyn_status_t>(status);
    }

    void GetConnectionStatus(bool *connected, bool *enabled) override
    {
      if (!connected || !enabled)
        return;

      *connected = IsConnected();
      *enabled = false;

      // Get the enabled flag from the latest heartbeat
      // GetLatestEvent() returns std::optional<lumyn::Event> (wrapper type)
      auto latest = this->GetLatestEvent();
      if (latest && latest->getType() == LUMYN_EVENT_HEARTBEAT)
      {
        *enabled = latest->getData().heartbeat.enabled != 0;
      }
    }

    void SendConfigurationInternal(const uint8_t *data, uint32_t length) override
    {
      this->SendConfiguration(data, length);
    }

    void SetConnectionStateCallback(void (*cb)(bool, void *), void *user) override
    {
      std::lock_guard<std::mutex> lock(connection_mutex_);
      connection_cb_ = cb;
      connection_user_ = user;
    }

    bool ConnectWithAdapter(std::unique_ptr<::lumyn::internal::ISerialIO> adapter)
    {
      if (IsConnected())
      {
        Disconnect();
      }
      return ::lumyn::internal::BaseLumynDevice::Connect(adapter.release());
    }

    void OnEvent(const ::lumyn::internal::Eventing::Event &evt) override
    {
      DeviceParent::OnEvent(evt);

      if (evt.header.type == ::lumyn::internal::Eventing::EventType::Connected)
      {
        NotifyConnectionState(true);
      }
      else if (evt.header.type == ::lumyn::internal::Eventing::EventType::Disconnected)
      {
        NotifyConnectionState(false);
      }

      // Dispatch to internal EventHandler instances first
      std::vector<std::shared_ptr<lumyn::internal::Eventing::EventHandler>> internal_handlers_copy;
      std::vector<std::pair<lumyn_event_callback_t, void *>> handlers_copy;
      {
        std::lock_guard<std::mutex> lock(event_mutex_);
        internal_handlers_copy = internal_event_handlers_;
        handlers_copy = event_handlers_;
      }

      // Call internal EventHandler::Handle() for each handler
      for (auto &handler : internal_handlers_copy)
      {
        if (handler)
        {
          handler->Handle(evt);
        }
      }

      // Call the dispatch function for C API event handlers
      if (dispatch_fn_)
      {
        dispatch_fn_(evt, handlers_copy);
      }
    }

  protected:
    void NotifyConnectionStateImpl(bool connected)
    {
      std::lock_guard<std::mutex> lock(connection_mutex_);
      if (connection_cb_)
      {
        connection_cb_(connected, connection_user_);
      }
    }

  private:
    std::mutex event_mutex_;
    std::vector<std::pair<lumyn_event_callback_t, void *>> event_handlers_;
    std::vector<std::shared_ptr<lumyn::internal::Eventing::EventHandler>> internal_event_handlers_;
    DispatchFn dispatch_fn_;
    std::mutex connection_mutex_;
    void (*connection_cb_)(bool, void *){nullptr};
    void *connection_user_{nullptr};
  };

} // namespace lumyn_c_sdk::internal
