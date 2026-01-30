#include "lumyn/domain/command/CommandBuilder.h"
#include <cstring>
#include <algorithm>

namespace lumyn::internal::Command
{
  std::vector<uint8_t> CommandBuilder::build(const CommandHeader &header, const void *bodyStruct, size_t bodySize)
  {
    std::vector<uint8_t> buffer;
    buffer.reserve(sizeof(CommandHeader) + bodySize);
    buffer.assign(reinterpret_cast<const uint8_t *>(&header),
                  reinterpret_cast<const uint8_t *>(&header) + sizeof(CommandHeader));

    if (bodyStruct && bodySize > 0)
    {
      buffer.insert(buffer.end(),
                    reinterpret_cast<const uint8_t *>(bodyStruct),
                    reinterpret_cast<const uint8_t *>(bodyStruct) + bodySize);
    }

    return buffer;
  }

  // === LED Commands ===

  std::vector<uint8_t> CommandBuilder::buildSetAnimation(uint16_t zoneId, uint16_t animationId,
                                                         LED::AnimationColor color, uint16_t delay, bool reversed, bool oneShot)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetAnimation;

    LED::SetAnimationData data{};
    data.zoneId = zoneId;
    data.animationId = animationId;
    data.delay = delay;
    data.color = color;
    data.reversed = reversed ? 1 : 0;
    data.oneShot = oneShot ? 1 : 0;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetAnimationGroup(uint16_t groupId, uint16_t animationId,
                                                              LED::AnimationColor color, uint16_t delay, bool reversed, bool oneShot)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetAnimationGroup;

    LED::SetAnimationGroupData data{};
    data.groupId = groupId;
    data.animationId = animationId;
    data.delay = delay;
    data.color = color;
    data.reversed = reversed ? 1 : 0;
    data.oneShot = oneShot ? 1 : 0;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetColor(uint16_t zoneId, LED::AnimationColor color)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetColor;

    LED::SetColorData data{};
    data.zoneId = zoneId;
    data.color = color;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetColorGroup(uint16_t groupId, LED::AnimationColor color)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetColorGroup;

    LED::SetColorGroupData data{};
    data.groupId = groupId;
    data.color = color;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetAnimationSequence(uint16_t zoneId, uint16_t sequenceId)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetAnimationSequence;

    LED::SetAnimationSequenceData data{};
    data.zoneId = zoneId;
    data.sequenceId = sequenceId;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetAnimationSequenceGroup(uint16_t groupId, uint16_t sequenceId)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetAnimationSequenceGroup;

    LED::SetAnimationSequenceGroupData data{};
    data.groupId = groupId;
    data.sequenceId = sequenceId;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetBitmap(uint16_t zoneId, uint16_t bitmapId,
                                                      LED::AnimationColor color, bool setColor, bool oneShot)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetBitmap;

    LED::SetBitmapData data{};
    data.zoneId = zoneId;
    data.bitmapId = bitmapId;
    data.color = color;
    data.setColor = setColor ? 1 : 0;
    data.oneShot = oneShot ? 1 : 0;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetBitmapGroup(uint16_t groupId, uint16_t bitmapId,
                                                           LED::AnimationColor color, bool setColor, bool oneShot)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetBitmapGroup;

    LED::SetBitmapGroupData data{};
    data.groupId = groupId;
    data.bitmapId = bitmapId;
    data.color = color;
    data.setColor = setColor ? 1 : 0;
    data.oneShot = oneShot ? 1 : 0;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetMatrixText(uint16_t zoneId, const std::string &text,
                                                          LED::AnimationColor color, LED::MatrixTextScrollDirection dir, uint16_t delay, bool oneShot,
                                                          LED::AnimationColor bgColor, LED::MatrixTextFont font, LED::MatrixTextAlign align,
                                                          LED::MatrixTextFlags flags, int8_t yOffset)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetMatrixText;

    LED::SetMatrixTextData data{};
    data.zoneId = zoneId;
    data.oneShot = oneShot ? 1 : 0;
    data.color = color;
    data.dir = dir;
    data.delay = delay;
    data.bgColor = bgColor;
    data.font = font;
    data.align = align;
    data.flags = flags;
    data.yOffset = yOffset;

    // Copy text with length limit
    size_t copyLen = std::min(text.size(), sizeof(data.text) - 1);
    std::memcpy(data.text, text.c_str(), copyLen);
    data.text[copyLen] = '\0';
    data.length = static_cast<uint8_t>(copyLen);

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetMatrixTextGroup(uint16_t groupId, const std::string &text,
                                                               LED::AnimationColor color, LED::MatrixTextScrollDirection dir, uint16_t delay, bool oneShot,
                                                               LED::AnimationColor bgColor, LED::MatrixTextFont font, LED::MatrixTextAlign align,
                                                               LED::MatrixTextFlags flags, int8_t yOffset)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetMatrixTextGroup;

    LED::SetMatrixTextGroupData data{};
    data.groupId = groupId;
    data.oneShot = oneShot ? 1 : 0;
    data.color = color;
    data.dir = dir;
    data.delay = delay;
    data.bgColor = bgColor;
    data.font = font;
    data.align = align;
    data.flags = flags;
    data.yOffset = yOffset;

    // Copy text with length limit
    size_t copyLen = std::min(text.size(), sizeof(data.text) - 1);
    std::memcpy(data.text, text.c_str(), copyLen);
    data.text[copyLen] = '\0';
    data.length = static_cast<uint8_t>(copyLen);

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetDirectBuffer(uint16_t zoneId, const uint8_t *data,
                                                            uint16_t length, bool isDelta)
  {
    CommandHeader header;
    header.type = CommandType::LED;
    header.ledType = LED::LEDCommandType::SetDirectBuffer;

    LED::SetDirectBufferData bufData{};
    bufData.zoneId = zoneId;
    bufData.bufferLength = length;
    bufData.flags.delta = isDelta ? 1 : 0;
    bufData.flags.reserved = 0;

    // Build with header struct first, then append variable-length pixel data
    std::vector<uint8_t> buffer = build(header, &bufData, sizeof(bufData));
    if (data && length > 0)
    {
      buffer.insert(buffer.end(), data, data + length);
    }

    return buffer;
  }

  // === System Commands ===

  std::vector<uint8_t> CommandBuilder::buildClearStatusFlag(uint32_t flags)
  {
    CommandHeader header;
    header.type = CommandType::System;
    header.systemType = System::SystemCommandType::ClearStatusFlag;

    System::ClearStatusFlagData data{};
    data.mask = flags;

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildSetAssignedId(const std::string &assignedId)
  {
    CommandHeader header;
    header.type = CommandType::System;
    header.systemType = System::SystemCommandType::SetAssignedId;

    System::SetAssignedIdData data{};
    size_t copyLen = std::min(assignedId.size(), sizeof(data.id) - 1);
    std::memcpy(data.id, assignedId.c_str(), copyLen);
    data.id[copyLen] = '\0';

    return build(header, &data, sizeof(data));
  }

  std::vector<uint8_t> CommandBuilder::buildRestartDevice()
  {
    CommandHeader header;
    header.type = CommandType::System;
    header.systemType = System::SystemCommandType::RestartDevice;

    System::RestartDeviceData data{};
    data.delayMs = 0;

    return build(header, &data, sizeof(data));
  }
} // namespace lumyn::internal::Command
