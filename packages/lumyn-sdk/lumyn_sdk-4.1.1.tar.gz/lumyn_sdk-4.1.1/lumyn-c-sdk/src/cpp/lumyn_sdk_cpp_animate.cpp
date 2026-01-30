#include "lumyn/Constants.h"  // Required for BuiltInAnimations.h (included via ConnectorXAnimate.hpp -> BaseConnectorXVariant.hpp -> AnimationBuilder.hpp)
#include "lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp"

namespace lumyn::device
{

  ConnectorXAnimate::ConnectorXAnimate()
      : BaseConnectorXVariant()
  {
    // Base class handles LED commander initialization
  }

  ConnectorXAnimate::~ConnectorXAnimate()
  {
    // Base class handles cleanup
  }

  void ConnectorXAnimate::OnEvent(const internal::Eventing::Event &evt)
  {
    // BaseLumynDevice already buffers and dispatches events; no extra handling needed.
    (void)evt;
  }

  void *ConnectorXAnimate::GetBasePtr()
  {
    return this;
  }

  const void *ConnectorXAnimate::GetBasePtr() const
  {
    return this;
  }

  ConnectorXAnimate& ConnectorXAnimate::SetAutoPollEvents(bool enabled)
  {
    BaseConnectorXVariant::SetAutoPollEvents(enabled);
    return *this;
  }

} // namespace lumyn::device
