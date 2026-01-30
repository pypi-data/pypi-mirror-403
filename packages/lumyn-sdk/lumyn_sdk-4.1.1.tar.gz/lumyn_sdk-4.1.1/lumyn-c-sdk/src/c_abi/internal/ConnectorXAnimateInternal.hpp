#pragma once

#include "ConnectorXInternalBase.hpp"

#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/c/serial_io.h>

namespace lumyn_c_sdk::internal {

class ConnectorXAnimateInternal : public ConnectorXInternalBase<::lumyn::device::ConnectorXAnimate> {
public:
    explicit ConnectorXAnimateInternal(cx_base_t* base_ptr)
        : ConnectorXInternalBase(base_ptr)
    {
    }
};

} // namespace lumyn_c_sdk::internal
