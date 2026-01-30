#pragma once

#include "lumyn/domain/Color.h"

namespace lumyn::internal::Animation
{

  /**
   * @brief Fill an array with a rainbow color pattern
   *
   * @param strip Pointer to Color array to fill
   * @param count Number of LEDs to fill
   * @param initialHue Starting hue value (0-255)
   * @param reversed Whether to reverse the rainbow direction
   */
  inline void fill_rainbow_circular(lumyn::internal::domain::Color *strip, int count, uint8_t initialHue, bool reversed = false)
  {
    if (count == 0)
      return; // avoid div/0

    // Calculate precise hue change for each LED
    const uint16_t hueChange = 65535 / (uint16_t)count; // same precision as FastLED
    uint16_t hueOffset = 0;

    uint8_t hue = initialHue;

    for (int i = 0; i < count; ++i)
    {
      // Create color using HSV with full saturation and value
      strip[i] = lumyn::internal::domain::Color::FromHSV(hue, 240, 255);

      // Update hue with precision
      if (reversed)
      {
        hueOffset -= hueChange;
      }
      else
      {
        hueOffset += hueChange;
      }
      hue = initialHue + (uint8_t)(hueOffset >> 8);
    }
  }

  /**
   * @brief Simplified version used by existing animations
   */
  inline void fill_rainbow_circular(lumyn::internal::domain::Color *strip, uint16_t count, uint8_t initialHue)
  {
    fill_rainbow_circular(strip, count, initialHue, false);
  }

} // namespace lumyn::internal::Animation