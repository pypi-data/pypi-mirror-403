#pragma once

#include "LEDCommandType.h"
#include "lumyn/packed.h"
#include "lumyn/types/color.h"
#include "lumyn/types/led_command.h"

namespace lumyn::internal::Command
{
  namespace LED
  {
    // AnimationColor is now defined in lumyn/types/color.h as lumyn_animation_color_t
    // Keep struct for binary compatibility with existing protocol
    PACK(struct AnimationColor {
      uint8_t r;
      uint8_t g;
      uint8_t b;
    });

    PACK(struct SetAnimationData {
      uint16_t zoneId;
      uint16_t animationId;
      uint16_t delay;
      AnimationColor color;
      uint8_t reversed : 1;
      uint8_t oneShot : 1;
    });

    PACK(struct SetAnimationGroupData {
      uint16_t groupId;
      uint16_t animationId;
      uint16_t delay;
      AnimationColor color;
      uint8_t reversed : 1;
      uint8_t oneShot : 1;
    });

    PACK(struct SetColorData {
      uint16_t zoneId;
      AnimationColor color;
    });

    PACK(struct SetColorGroupData {
      uint16_t groupId;
      AnimationColor color;
    });

    PACK(struct SetAnimationSequenceData {
      uint16_t zoneId;
      uint16_t sequenceId;
    });

    PACK(struct SetAnimationSequenceGroupData {
      uint16_t groupId;
      uint16_t sequenceId;
    });

    PACK(struct SetBitmapData {
      uint16_t zoneId;
      uint16_t bitmapId;
      AnimationColor color;
      uint8_t setColor : 1;
      uint8_t oneShot : 1;
    });

    PACK(struct SetBitmapGroupData {
      uint16_t groupId;
      uint16_t bitmapId;
      AnimationColor color;
      uint8_t setColor : 1;
      uint8_t oneShot : 1;
    });

    PACK(struct SetMatrixTextData {
      uint16_t zoneId;
      uint8_t oneShot;
      AnimationColor color;
      MatrixTextScrollDirection dir;
      char text[24];
      uint8_t length;
      uint16_t delay;

      AnimationColor bgColor; // Background color
      MatrixTextFont font;    // Font selection
      MatrixTextAlign align;  // Alignment when noScroll=1
      MatrixTextFlags flags;  // Scroll/display options
      int8_t yOffset;         // Vertical offset (signed, for fine positioning)
    });

    PACK(struct SetMatrixTextGroupData {
      uint16_t groupId;
      uint8_t oneShot;
      AnimationColor color;
      MatrixTextScrollDirection dir;
      char text[24];
      uint8_t length;
      uint16_t delay;

      AnimationColor bgColor; // Background color
      MatrixTextFont font;    // Font selection
      MatrixTextAlign align;  // Alignment when noScroll=1
      MatrixTextFlags flags;  // Scroll/display options
      int8_t yOffset;         // Vertical offset (signed, for fine positioning)
    });

    PACK(struct SetDirectBufferFlags {
      uint8_t reserved : 7;
      uint8_t delta : 1; // Indicates that the buffer contains delta data;
                         // otherwise, is a full buffer
    });

    PACK(struct SetDirectBufferData {
      uint16_t zoneId;
      uint16_t bufferLength;
      SetDirectBufferFlags flags;
    });

    PACK(union LEDCommandData {
      SetAnimationData setAnimation;
      SetAnimationGroupData setAnimationGroup;
      SetColorData setColor;
      SetColorGroupData setColorGroup;
      SetAnimationSequenceData setAnimationSequence;
      SetAnimationSequenceGroupData setAnimationSequenceGroup;
      SetBitmapData setBitmap;
      SetBitmapGroupData setBitmapGroup;
      SetMatrixTextData setMatrixText;
      SetMatrixTextGroupData setMatrixTextGroup;
      SetDirectBufferData setDirectBuffer;
    });

    PACK(struct LEDCommand {
      LEDCommandType type;
      LEDCommandData data;
    });
  } // namespace LED
} // namespace lumyn::internal::Command