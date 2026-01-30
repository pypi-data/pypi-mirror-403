#include <lumyn/Constants.h>  // Required for ILogger.h (included via ConsoleLogger.h)
#include "lumyn/cpp/led/LEDCommander.hpp"
#include "lumyn/domain/command/led/LEDCommand.h"
#include "lumyn/led/Animation.h"
#include "lumyn/util/hashing/IDCreator.h"
#include "lumyn/util/logging/ConsoleLogger.h"

using namespace lumyn::internal;
using namespace lumyn::internal::Command::LED;

LEDCommand LEDCommander::SetColor(std::string_view zoneID, Command::LED::AnimationColor color) const
{
  auto id = IDCreator::createId(zoneID);

  LEDCommand cmd = {
      .type = LEDCommandType::SetColor,
      .data = {.setColor = {
          .zoneId = id,
          .color = color}}};

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand LEDCommander::SetGroupColor(std::string_view groupID, Command::LED::AnimationColor color) const
{
  auto id = IDCreator::createId(groupID);

  LEDCommand cmd = {
      .type = LEDCommandType::SetColorGroup,
      .data = {.setColorGroup = {
          .groupId = id,
          .color = color}}};

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand LEDCommander::SetAnimation(std::string_view name, lumyn::led::Animation animation,
                                      Command::LED::AnimationColor color, std::chrono::milliseconds delay,
                                      bool reversed, bool oneShot) const
{
  auto id = IDCreator::createId(name);
  auto animName = lumyn::led::kAnimationMap.count(animation) ? lumyn::led::kAnimationMap.at(animation) : "None";

  std::string msg = "SetAnimation: name=" + std::string(name) +
      ", animation=" + std::string(animName) +
      ", color=(" + std::to_string(color.r) + "," + std::to_string(color.g) + "," + std::to_string(color.b) + ")" +
      ", delay=" +  std::to_string(delay.count()) +
      ", reversed=" + (reversed ? "true" : "false") +
      ", oneShot=" + (oneShot ? "true" : "false") +
      ", id=" + std::to_string(id);

  // CONSOLE_LOG(msg);

  auto animationId = IDCreator::createId(animName);

  LEDCommand cmd = {
      .type = LEDCommandType::SetAnimation,
      .data = {.setAnimation = {
          .zoneId = id,
          .animationId = animationId,
          .delay = static_cast<uint16_t>(delay.count()),
          .color = color,
          .reversed = (uint8_t)(reversed ? 1 : 0),
          .oneShot = (uint8_t)(oneShot ? 1 : 0)}}};

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand LEDCommander::SetGroupAnimation(std::string_view groupID, led::Animation animation,
                                           Command::LED::AnimationColor color, std::chrono::milliseconds delay,
                                           bool reversed, bool oneShot) const
{
  auto id = IDCreator::createId(groupID);
  auto animName = lumyn::led::kAnimationMap.count(animation) ? lumyn::led::kAnimationMap.at(animation) : "None";

  std::string msg = "SetGroupAnimation: name=" + std::string(groupID) +
      ", animation=" + std::string(animName) +
      ", color=(" + std::to_string(color.r) + "," + std::to_string(color.g) + "," + std::to_string(color.b) + ")" +
      ", delay=" +  std::to_string(delay.count()) +
      ", reversed=" + (reversed ? "true" : "false") +
      ", oneShot=" + (oneShot ? "true" : "false") +
      ", id=" + std::to_string(id);

  // CONSOLE_LOG(msg);

  auto animationId = IDCreator::createId(animName);

  LEDCommand cmd = {
      .type = LEDCommandType::SetAnimationGroup,
      .data = {.setAnimationGroup = {
          .groupId = id,
          .animationId = animationId,
          .delay = static_cast<uint16_t>(delay.count()),
          .color = color,
          .reversed = (uint8_t)(reversed ? 1 : 0),
          .oneShot = (uint8_t)(oneShot ? 1 : 0)}}};

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand LEDCommander::SetAnimationSequence(std::string_view zoneID, std::string_view sequenceID) const
{
  auto id = IDCreator::createId(zoneID);
  auto sequence = IDCreator::createId(sequenceID);

  LEDCommand cmd = {
      .type = LEDCommandType::SetAnimationSequence,
      .data = {.setAnimationSequence = {
          .zoneId = id,
          .sequenceId = sequence}}};

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand LEDCommander::SetGroupAnimationSequence(std::string_view groupID, std::string_view sequenceID) const
{
  auto id = IDCreator::createId(groupID);
  auto sequence = IDCreator::createId(sequenceID);

  LEDCommand cmd = {
      .type = LEDCommandType::SetAnimationSequenceGroup,
      .data = {.setAnimationSequenceGroup = {
          .groupId = id,
          .sequenceId = sequence}}};

  _cmdHandler(cmd);

  return cmd;
}
