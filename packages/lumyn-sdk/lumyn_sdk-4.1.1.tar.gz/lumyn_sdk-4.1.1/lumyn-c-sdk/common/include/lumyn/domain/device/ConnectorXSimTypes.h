#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

#include "lumyn/domain/command/led/LEDCommand.h"
#include "lumyn/domain/event/Event.h"
#include "lumyn/domain/module/ModulePayloadDescriptor.h"
#include "lumyn/domain/event/EventType.h"

namespace lumyn::internal::connectorx::sim {

enum class SimProductSku : uint16_t {
  kUnknown = 0,
  kConnectorX = 1,
  kConnectorXAnimate = 2,
};

struct ModuleFieldDescriptor;

struct ConfiguredModule {
  std::string id;
  std::string type;
  std::vector<lumyn::internal::module::ModuleFieldDescriptor> fields;
};

struct ZoneState {
  Command::LED::SetAnimationData applied{};
  Command::LED::LEDCommandType lastCommand{Command::LED::LEDCommandType::SetColor};
  Command::LED::AnimationColor lastColor{0, 0, 0};
  uint16_t lastSequenceId{0};
  Command::LED::SetBitmapData lastBitmap{};
  Command::LED::SetMatrixTextData lastMatrixText{};
  bool running{false};
  float timeMs{0.0f};
  std::vector<Command::LED::AnimationColor> ledColors;  // Per-pixel colors for DirectLED
};

struct StatusOption {
  Eventing::Status status;
  const char* label;
};

struct EventHistoryEntry {
  Eventing::Event event;
  double timestampSec;
};

inline constexpr std::array<StatusOption, 5> kStatusOptions{{
    {Eventing::Status::Unknown, "Unknown"},
    {Eventing::Status::Booting, "Booting"},
    {Eventing::Status::Active, "Active"},
    {Eventing::Status::Error, "Error"},
    {Eventing::Status::Fatal, "Fatal"},
}};

}  // namespace lumyn::internal::connectorx::sim
