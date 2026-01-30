#pragma once

#include "lumyn/cpp/export.hpp"
#include "lumyn/cpp/connectorXVariant/BaseConnectorXVariant.hpp"

namespace lumyn::device {

/**
 * @brief ConnectorXAnimate device with LED support (no modules)
 *
 * Inherits all shared functionality from BaseConnectorXVariant.
 * This is a thin wrapper that only needs to implement pure virtual methods.
 */
class LUMYN_SDK_CPP_API ConnectorXAnimate 
  : public BaseConnectorXVariant {
public:
  ConnectorXAnimate();
  ~ConnectorXAnimate() override;

  ConnectorXAnimate(const ConnectorXAnimate&) = delete;
  ConnectorXAnimate& operator=(const ConnectorXAnimate&) = delete;
  ConnectorXAnimate(ConnectorXAnimate&&) = delete;
  ConnectorXAnimate& operator=(ConnectorXAnimate&&) = delete;

  // SetAutoPollEvents - return *this for chaining
  ConnectorXAnimate& SetAutoPollEvents(bool enabled);

  // Base class pure virtual implementations
  void* GetBasePtr() override;
  const void* GetBasePtr() const override;
  void OnEvent(const internal::Eventing::Event &) override;
};

} // namespace lumyn::device
