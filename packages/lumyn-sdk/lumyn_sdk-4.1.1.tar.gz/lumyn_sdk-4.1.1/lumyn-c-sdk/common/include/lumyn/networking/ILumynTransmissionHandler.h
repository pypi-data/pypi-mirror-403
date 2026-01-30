#pragma once

#include <functional>
#include "lumyn/domain/event/Event.h"
#include "lumyn/domain/response/Response.h"
#include "lumyn/domain/module/ModuleData.h"
#include "lumyn/domain/transmission/Transmission.h"

namespace lumyn::internal
{
  // Forward declare to avoid ambiguity on MSVC
  using TransmissionClass = ::lumyn::internal::Transmission::Transmission;

  class ILumynTransmissionHandler
  {
  public:
    virtual ~ILumynTransmissionHandler() {}

    virtual void HandleEvent(const Eventing::Event &) = 0;
    virtual void HandleTransmission(const TransmissionClass &) = 0;
  };
}
