#include "lumyn/Constants.h"  // Required for BuiltInAnimations.h (included via ConnectorX.hpp -> BaseConnectorXVariant.hpp -> AnimationBuilder.hpp)
#include "lumyn/cpp/connectorXVariant/ConnectorX.hpp"
#include "lumyn/cpp/modules/ModuleDataDispatcher.hpp"

#include <lumyn/domain/event/EventType.h>
#include <lumyn/domain/event/Event.h>

namespace lumyn::device
{

  ConnectorX::ConnectorX()
      : BaseConnectorXVariant(),
        internal::BaseModuleDevice()
  {
    // Base class handles LED commander initialization
  }

  ConnectorX::~ConnectorX()
  {
    if (module_dispatcher_)
    {
      module_dispatcher_->Stop();
    }
    connection_callback_.reset();
    // Base class handles event polling cleanup
  }

  void ConnectorX::OnEvent(const internal::Eventing::Event &evt)
  {
    if (connection_callback_)
    {
      if (evt.header.type == internal::Eventing::EventType::Connected)
      {
        (*connection_callback_)(true);
      }
      else if (evt.header.type == internal::Eventing::EventType::Disconnected)
      {
        (*connection_callback_)(false);
      }
    }
  }

  void *ConnectorX::GetBasePtr()
  {
    return this;
  }

  const void *ConnectorX::GetBasePtr() const
  {
    return this;
  }

  internal::BaseLumynDevice *ConnectorX::GetModuleBasePtr()
  {
    return this;
  }

  const internal::BaseLumynDevice *ConnectorX::GetModuleBasePtr() const
  {
    return this;
  }

  void ConnectorX::OnDisconnect()
  {
    if (module_dispatcher_)
    {
      module_dispatcher_->Stop();
    }
  }

  ConnectorX &ConnectorX::SetAutoPollEvents(bool enabled)
  {
    BaseConnectorXVariant::SetAutoPollEvents(enabled);
    return *this;
  }

  void ConnectorX::RestartDevice(uint32_t delay_ms)
  {
    BaseLumynDevice::Restart(delay_ms);
  }

  lumyn::modules::ModuleDataDispatcher &ConnectorX::GetModuleDispatcher()
  {
    if (!module_dispatcher_)
    {
      module_dispatcher_ = std::make_unique<lumyn::modules::ModuleDataDispatcher>(*this, GetCBasePtr());
    }
    return *module_dispatcher_;
  }

  void ConnectorX::SetConnectionStateCallback(std::function<void(bool)> callback)
  {
    connection_callback_ = std::make_unique<std::function<void(bool)>>(std::move(callback));
    auto* c_ptr = GetCBasePtr();
    if (c_ptr)
    {
      lumyn_SetConnectionStateCallback(c_ptr, [](bool connected, void *user)
                                       {
      auto* fn = static_cast<std::function<void(bool)>*>(user);
      if (fn) (*fn)(connected); }, connection_callback_.get());
    }
  }

} // namespace lumyn::device
