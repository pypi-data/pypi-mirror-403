#pragma once

#include <map>
#include "../domain/event/EventType.h"
#include "../domain/command/Command.h"
#include "../util/hashing/IDCreator.h"

namespace lumyn::internal::SystemStatus
{
  static const std::map<Eventing::EventType, Eventing::Status> kEventStatuses = {
      {Eventing::EventType::BeginInitialization, Eventing::Status::Booting},
      {Eventing::EventType::Error, Eventing::Status::Error},
      {Eventing::EventType::FatalError, Eventing::Status::Fatal}};

  static std::map<Eventing::Status, Command::LED::LEDCommand>
      kStatusLedAnimations = {
          {Eventing::Status::Booting,
           {.type = Command::LED::LEDCommandType::SetAnimation,
            .data = {.setAnimation = {.zoneId = 0,
                             .animationId =
                                 IDCreator::createId(std::string("Blink")),
                             .delay = 250,
                             .color = {.r = 0, .g = 255, .b = 50},
                             .reversed = false,
                             .oneShot = false}}}},
          {Eventing::Status::Active,
           {.type = Command::LED::LEDCommandType::SetAnimation,
            .data = {.setAnimation = {.zoneId = 0,
                             .animationId =
                                 IDCreator::createId(std::string("Breathe")),
                             .delay = 10,
                             .color = {.r = 0, .g = 20, .b = 200},
                             .reversed = false,
                             .oneShot = false}}}},
          {Eventing::Status::Error,
           {.type = Command::LED::LEDCommandType::SetAnimation,
            .data = {.setAnimation = {.zoneId = 0,
                             .animationId =
                                 IDCreator::createId(std::string("Blink")),
                             .delay = 500,
                             .color = {.r = 120, .g = 30, .b = 5},
                             .reversed = false,
                             .oneShot = false}}}},
          {Eventing::Status::Fatal,
           {.type = Command::LED::LEDCommandType::SetAnimation,
            .data = {.setAnimation = {
                .zoneId = 0,
                .animationId = IDCreator::createId(std::string("Blink")),
                .delay = 250,
                .color = {.r = 255, .g = 0, .b = 0},
                .reversed = false,
                .oneShot = false}}}}};
}