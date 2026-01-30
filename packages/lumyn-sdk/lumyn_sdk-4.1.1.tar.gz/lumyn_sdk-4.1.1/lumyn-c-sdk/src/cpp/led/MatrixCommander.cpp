#include "lumyn/cpp/led/MatrixCommander.hpp"
#include "lumyn/domain/command/led/LEDCommand.h"
#include <lumyn/util/hashing/IDCreator.h>
#include <lumyn/Constants.h>
#include <cstring>
#include <stdexcept>

using namespace lumyn::internal;
using namespace lumyn::internal::Command::LED;

LEDCommand MatrixCommander::SetBitmap(std::string_view zoneID, std::string_view bitmapID, AnimationColor color,
                                      bool setColor, bool oneShot) const
{
  auto id = lumyn::internal::IDCreator::createId(zoneID);
  auto bmpId = lumyn::internal::IDCreator::createId(bitmapID);

  LEDCommand cmd = {};
  cmd.type = LEDCommandType::SetBitmap;
  cmd.data.setBitmap.zoneId = id;
  cmd.data.setBitmap.bitmapId = bmpId;
  cmd.data.setBitmap.color = color;
  cmd.data.setBitmap.setColor = (uint8_t)(setColor ? 1 : 0);
  cmd.data.setBitmap.oneShot = (uint8_t)(oneShot ? 1 : 0);

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand MatrixCommander::SetGroupBitmap(std::string_view groupID, std::string_view bitmapID, AnimationColor color,
                                           bool setColor, bool oneShot) const
{
  auto id = lumyn::internal::IDCreator::createId(groupID);
  auto bmpId = lumyn::internal::IDCreator::createId(bitmapID);

  LEDCommand cmd = {};
  cmd.type = LEDCommandType::SetBitmapGroup;
  cmd.data.setBitmapGroup.groupId = id;
  cmd.data.setBitmapGroup.bitmapId = bmpId;
  cmd.data.setBitmapGroup.color = color;
  cmd.data.setBitmapGroup.setColor = (uint8_t)(setColor ? 1 : 0);
  cmd.data.setBitmapGroup.oneShot = (uint8_t)(oneShot ? 1 : 0);

  _cmdHandler(cmd);

  return cmd;
}

LEDCommand MatrixCommander::SetText(std::string_view zoneID, std::string_view text, AnimationColor color,
                                    MatrixTextScrollDirection direction,
                                    std::chrono::milliseconds delayMs, bool oneShot) const
{
  return SetText(zoneID, text, color, direction, delayMs, oneShot,
                 AnimationColor{0, 0, 0}, MatrixTextFont::BUILTIN,
                 MatrixTextAlign::LEFT, MatrixTextFlags{}, 0);
}

LEDCommand MatrixCommander::SetText(std::string_view zoneID, std::string_view text, AnimationColor color,
                                    MatrixTextScrollDirection direction,
                                    std::chrono::milliseconds delayMs, bool oneShot,
                                    AnimationColor bgColor, MatrixTextFont font,
                                    MatrixTextAlign align, MatrixTextFlags flags,
                                    int8_t yOffset) const
{
  if (text.size() > lumyn::internal::Constants::LED::kMaxMatrixTextLength)
  {
    throw std::length_error("Matrix text exceeds maximum length of " + 
                            std::to_string(lumyn::internal::Constants::LED::kMaxMatrixTextLength) + 
                            " characters");
  }

  auto id = lumyn::internal::IDCreator::createId(zoneID);

  LEDCommand cmd = {};
  cmd.type = LEDCommandType::SetMatrixText;
  cmd.data.setMatrixText.zoneId = id;
  cmd.data.setMatrixText.oneShot = (uint8_t)(oneShot ? 1 : 0);
  cmd.data.setMatrixText.color = color;
  cmd.data.setMatrixText.dir = direction;
  cmd.data.setMatrixText.length = static_cast<uint8_t>(text.size());
  cmd.data.setMatrixText.delay = static_cast<uint16_t>(delayMs.count());
  cmd.data.setMatrixText.bgColor = bgColor;
  cmd.data.setMatrixText.font = font;
  cmd.data.setMatrixText.align = align;
  cmd.data.setMatrixText.flags = flags;
  cmd.data.setMatrixText.yOffset = yOffset;

  memcpy(cmd.data.setMatrixText.text, text.data(), text.size());
  _cmdHandler(cmd);

  return cmd;
}

LEDCommand MatrixCommander::SetGroupText(std::string_view groupID, std::string_view text, AnimationColor color,
                                         MatrixTextScrollDirection direction,
                                         std::chrono::milliseconds delayMs, bool oneShot) const
{
  return SetGroupText(groupID, text, color, direction, delayMs, oneShot,
                      AnimationColor{0, 0, 0}, MatrixTextFont::BUILTIN,
                      MatrixTextAlign::LEFT, MatrixTextFlags{}, 0);
}

LEDCommand MatrixCommander::SetGroupText(std::string_view groupID, std::string_view text, AnimationColor color,
                                         MatrixTextScrollDirection direction,
                                         std::chrono::milliseconds delayMs, bool oneShot,
                                         AnimationColor bgColor, MatrixTextFont font,
                                         MatrixTextAlign align, MatrixTextFlags flags,
                                         int8_t yOffset) const
{
  if (text.size() > lumyn::internal::Constants::LED::kMaxMatrixTextLength)
  {
    throw std::length_error("Matrix text exceeds maximum length of " + 
                            std::to_string(lumyn::internal::Constants::LED::kMaxMatrixTextLength) + 
                            " characters");
  }

  auto id = lumyn::internal::IDCreator::createId(groupID);

  LEDCommand cmd = {};
  cmd.type = LEDCommandType::SetMatrixTextGroup;
  cmd.data.setMatrixTextGroup.groupId = id;
  cmd.data.setMatrixTextGroup.oneShot = (uint8_t)(oneShot ? 1 : 0);
  cmd.data.setMatrixTextGroup.color = color;
  cmd.data.setMatrixTextGroup.dir = direction;
  cmd.data.setMatrixTextGroup.length = static_cast<uint8_t>(text.size());
  cmd.data.setMatrixTextGroup.delay = static_cast<uint16_t>(delayMs.count());
  cmd.data.setMatrixTextGroup.bgColor = bgColor;
  cmd.data.setMatrixTextGroup.font = font;
  cmd.data.setMatrixTextGroup.align = align;
  cmd.data.setMatrixTextGroup.flags = flags;
  cmd.data.setMatrixTextGroup.yOffset = yOffset;

  memcpy(cmd.data.setMatrixTextGroup.text, text.data(), text.size());
  _cmdHandler(cmd);

  return cmd;
}
