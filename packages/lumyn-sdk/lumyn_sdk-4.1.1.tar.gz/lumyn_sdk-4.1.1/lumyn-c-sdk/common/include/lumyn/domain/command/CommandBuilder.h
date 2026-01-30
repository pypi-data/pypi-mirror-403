#pragma once

#include "Command.h"
#include "led/LEDCommand.h"
#include "system/SystemCommand.h"
#include <vector>
#include <cstdint>
#include <cstddef>
#include <string>

namespace lumyn::internal::Command
{
  class CommandBuilder
  {
  public:
    // Build a command buffer: CommandHeader + body struct
    static std::vector<uint8_t> build(const CommandHeader &header, const void *bodyStruct = nullptr, size_t bodySize = 0);

    // === LED Commands ===
    static std::vector<uint8_t> buildSetAnimation(uint16_t zoneId, uint16_t animationId,
                                                  LED::AnimationColor color, uint16_t delay, bool reversed, bool oneShot);

    static std::vector<uint8_t> buildSetAnimationGroup(uint16_t groupId, uint16_t animationId,
                                                       LED::AnimationColor color, uint16_t delay, bool reversed, bool oneShot);

    static std::vector<uint8_t> buildSetColor(uint16_t zoneId, LED::AnimationColor color);
    static std::vector<uint8_t> buildSetColorGroup(uint16_t groupId, LED::AnimationColor color);

    static std::vector<uint8_t> buildSetAnimationSequence(uint16_t zoneId, uint16_t sequenceId);
    static std::vector<uint8_t> buildSetAnimationSequenceGroup(uint16_t groupId, uint16_t sequenceId);

    static std::vector<uint8_t> buildSetBitmap(uint16_t zoneId, uint16_t bitmapId,
                                               LED::AnimationColor color, bool setColor, bool oneShot);
    static std::vector<uint8_t> buildSetBitmapGroup(uint16_t groupId, uint16_t bitmapId,
                                                    LED::AnimationColor color, bool setColor, bool oneShot);

    static std::vector<uint8_t> buildSetMatrixText(uint16_t zoneId, const std::string &text,
                                                   LED::AnimationColor color, LED::MatrixTextScrollDirection dir, uint16_t delay, bool oneShot,
                                                   LED::AnimationColor bgColor = {0, 0, 0},
                                                   LED::MatrixTextFont font = LED::MatrixTextFont::BUILTIN,
                                                   LED::MatrixTextAlign align = LED::MatrixTextAlign::LEFT,
                                                   LED::MatrixTextFlags flags = LED::MatrixTextFlags{},
                                                   int8_t yOffset = 0);
    static std::vector<uint8_t> buildSetMatrixTextGroup(uint16_t groupId, const std::string &text,
                                                        LED::AnimationColor color, LED::MatrixTextScrollDirection dir, uint16_t delay, bool oneShot,
                                                        LED::AnimationColor bgColor = {0, 0, 0},
                                                        LED::MatrixTextFont font = LED::MatrixTextFont::BUILTIN,
                                                        LED::MatrixTextAlign align = LED::MatrixTextAlign::LEFT,
                                                        LED::MatrixTextFlags flags = LED::MatrixTextFlags{},
                                                        int8_t yOffset = 0);

    static std::vector<uint8_t> buildSetDirectBuffer(uint16_t zoneId, const uint8_t *data,
                                                     uint16_t length, bool isDelta);

    // === System Commands ===
    static std::vector<uint8_t> buildClearStatusFlag(uint32_t flags);
    static std::vector<uint8_t> buildSetAssignedId(const std::string &assignedId);
    static std::vector<uint8_t> buildRestartDevice();
  };
} // namespace lumyn::internal::Command
