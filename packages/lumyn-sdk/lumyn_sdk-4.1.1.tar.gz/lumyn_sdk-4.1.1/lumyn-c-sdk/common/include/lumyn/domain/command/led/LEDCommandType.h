#pragma once

#include <cinttypes>

namespace lumyn::internal::Command
{
  namespace LED
  {
    enum class LEDCommandType : uint8_t
    {
      SetAnimation,
      SetAnimationGroup,
      SetColor,
      SetColorGroup,
      SetAnimationSequence,
      SetAnimationSequenceGroup,
      SetBitmap,
      SetBitmapGroup,
      SetMatrixText,
      SetMatrixTextGroup,
      SetDirectBuffer,    // Send raw LED buffer data as a delta
    };
  }
} // namespace Command 