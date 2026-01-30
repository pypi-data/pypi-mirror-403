#pragma once

#include <algorithm>
#include <cmath>
#include <vector>

// Define M_PI for MSVC
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#include "ColorUtils.h"
#include "lumyn/definitions/led/AnimationInstance.h"
#include "lumyn/led/Animation.h"

namespace lumyn::internal::Animation {

// Helper functions
inline uint8_t random8() { return rand() % 256; }

inline uint8_t random8(uint8_t lim) { return rand() % lim; }

inline uint8_t random8(uint8_t min, uint8_t max) {
  return min + (rand() % (max - min));
}

inline uint16_t random16(uint16_t lim) { return rand() % lim; }

inline uint8_t qsub8(uint8_t i, uint8_t j) {
  int16_t t = i - j;
  if (t < 0) t = 0;
  return t;
}

inline uint8_t qadd8(uint8_t i, uint8_t j) {
  uint16_t t = i + j;
  if (t > 255) t = 255;
  return t;
}

inline uint8_t scale8(uint8_t i, uint8_t scale) {
  return ((uint16_t)i * (uint16_t)scale) >> 8;
}

inline uint8_t sin8(uint8_t theta) {
  static const uint8_t b_m16_interleave[] = {0, 49, 49, 41, 90, 27, 117, 10};
  uint8_t offset = theta;
  if (theta & 0x40) {
    offset = 255 - offset;
  }
  offset &= 0x3F;

  uint8_t secoffset = offset & 0x0F;
  if (theta & 0x40) secoffset++;

  uint8_t section = offset >> 4;
  uint8_t s2 = section * 2;
  const uint8_t *p = b_m16_interleave;
  p += s2;
  uint8_t b = *p;
  p++;
  uint8_t m16 = *p;

  uint8_t mx = (m16 * secoffset) >> 4;

  int8_t y = mx + b;
  if (theta & 0x80) y = -y;

  y += 128;

  return y;
}

inline uint8_t constrain8(uint8_t x, uint8_t a, uint8_t b) {
  if (x < a) return a;
  if (x > b) return b;
  return x;
}

static AnimationInstance Fill = {
    .id = "Fill",
    .stateMode = StateMode::Constant,
    .stateCount = 1,
    .defaultDelay = 20000,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (size_t i = 0; i < count; i++) {
        strip[i] = color;
      }

      return true;
    }};

static AnimationInstance Blink = {
    .id = "Blink",
    .stateMode = StateMode::Constant,
    .stateCount = 2,
    .defaultDelay = 1000,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      switch (state) {
        case 0:
          for (size_t i = 0; i < count; i++) {
            strip[i] = color;
          }
          return true;

        case 1:
          for (size_t i = 0; i < count; i++) {
            strip[i] = lumyn::internal::domain::Color::Black();
          }
          return true;

        default:
          return false;
      }
    }};

static AnimationInstance Breathe = {
    .id = "Breathe",
    .stateMode = StateMode::Constant,
    .stateCount = 512,
    .defaultDelay = 5,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      if (state > 255) {
        state = 511 - state;
      }
      for (size_t i = 0; i < count; i++) {
        strip[i] = color.scale8(state & 0xff);
      }

      return true;
    }};

static AnimationInstance RainbowRoll = {
    .id = "RainbowRoll",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 10,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      fill_rainbow_circular(strip, count, state);

      return true;
    }};

static AnimationInstance SineRoll = {
    .id = "SineRoll",
    .stateMode = StateMode::Constant,
    .stateCount = 60,
    .defaultDelay = 5,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (uint16_t index = 0; index < count; index++) {
        double t1 = (2 * M_PI / 60) * (60 - state);
        double t2 = (2 * M_PI / 60.0) * index;
        double brightness = sin(t2 + t1) + 1;
        uint8_t quantizedBrightness = 255 * (brightness / 2);
        strip[index] = color.scale8(quantizedBrightness);
      }

      return true;
    }};

static AnimationInstance Chase = {
    .id = "Chase",
    .stateMode = StateMode::LedCount,
    .stateCount = 5,
    .defaultDelay = 25,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      uint16_t startState = 5;
      uint16_t endState = (count + 5) - 1;
      uint16_t startIndex = state;
      uint16_t endIndex = (state + 5) - 1;

      for (uint16_t index = startState; index <= endState; index++) {
        if (index >= startIndex && index <= endIndex) {
          strip[index - startState] = color;
        } else {
          strip[index - startState] = 0;
        }
      }

      return true;
    }};

static AnimationInstance FadeIn = {
    .id = "FadeIn",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 5,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (size_t i = 0; i < count; i++) {
        strip[i] = color;
        strip[i].fadeLightBy(255 - state);
      }
      return true;
    }};

static AnimationInstance FadeOut = {
    .id = "FadeOut",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 5,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (size_t i = 0; i < count; i++) {
        strip[i] = color;
        strip[i].fadeLightBy(state);
      }
      return true;
    }};

static AnimationInstance RainbowCycle = {
    .id = "RainbowCycle",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 10,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      lumyn::internal::domain::Color hueColor =
          lumyn::internal::domain::Color::FromHSV(state & 0xff, 255, 255);

      for (size_t i = 0; i < count; i++) {
        strip[i] = hueColor;
      }

      return true;
    }};

static AnimationInstance AlternateBreathe = {
    .id = "AlternateBreathe",
    .stateMode = StateMode::Constant,
    .stateCount = 1024,
    .defaultDelay = 10,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (size_t i = 0; i < count; i++) {
        bool evenOdd = false;
        auto stateCpy = state;

        if (stateCpy > 511) {
          evenOdd = true;
          stateCpy = state - 512;
        }

        if (stateCpy > 255) {
          stateCpy = 511 - stateCpy;
        }

        if (i % 2 == 0 && !evenOdd) {
          strip[i] = color;
          strip[i].fadeLightBy(256 - state);
        } else if (i % 2 == 1 && evenOdd) {
          strip[i] = color;
          strip[i].fadeLightBy(256 - state);
        } else {
          strip[i] = lumyn::internal::domain::Color{0, 0, 0};
        }
      }

      return true;
    }};

static AnimationInstance GrowingBreathe = {
    .id = "GrowingBreathe",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 10,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      float ratio = state / 256.0;
      uint16_t maxIndex = std::round(ratio * count);

      for (size_t i = 0; i < maxIndex; i++) {
        strip[i] = color;
        strip[i].fadeLightBy(256 - state);
      }

      for (size_t i = maxIndex; i < count; i++) {
        strip[i] = lumyn::internal::domain::Color::Black();
      }

      return true;
    }};

static AnimationInstance Comet = {
    .id = "Comet",
    .stateMode = StateMode::LedCount,
    .stateCount = 1,
    .defaultDelay = 75,
    .defaultColor = lumyn::internal::domain::Color(138, 43, 226),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const uint8_t tailLength =
          std::min<uint16_t>(8, std::max<uint16_t>(1, count - 1));

      for (uint16_t i = 0; i < count; i++) {
        strip[i] = lumyn::internal::domain::Color::Black();
      }

      strip[state % count] = color;

      for (uint8_t t = 1; t <= tailLength; t++) {
        int16_t tailPos = (state - t);
        if (tailPos < 0) tailPos += count;

        uint8_t brightness =
            static_cast<uint8_t>(std::round(255 * pow(0.7, t)));
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, brightness);
        dimColor.g = scale8(dimColor.g, brightness);
        dimColor.b = scale8(dimColor.b, brightness);
        strip[tailPos % count] = dimColor;
      }

      return true;
    }};

static AnimationInstance Sparkle = {
    .id = "Sparkle",
    .stateMode = StateMode::Constant,
    .stateCount = 100,
    .defaultDelay = 150,
    .defaultColor = lumyn::internal::domain::Color::White(),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (size_t i = 0; i < count; i++) {
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, 51);  // 20% background
        dimColor.g = scale8(dimColor.g, 51);
        dimColor.b = scale8(dimColor.b, 51);
        strip[i] = dimColor;

        if (random8() < 8)  // ~3% chance
        {
          const float sparkleIntensity = 0.6f + (random8() / 255.0f) * 0.4f;
          const uint8_t brightness =
              static_cast<uint8_t>(std::round(sparkleIntensity * 255.0f));
          dimColor.r = scale8(color.r, brightness);
          dimColor.g = scale8(color.g, brightness);
          dimColor.b = scale8(color.b, brightness);
          strip[i] = dimColor;
        }
      }

      return true;
    }};

static AnimationInstance Fire = {
    .id = "Fire",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 40,
    .defaultColor = lumyn::internal::domain::Color(255, 35, 0),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t /*state*/,
             uint16_t count) {
      if (count == 0) return true;

      static std::vector<uint8_t> heat;
      if (heat.size() != count) {
        heat.assign(count, 0);
      }

      for (uint16_t i = 0; i < count; i++) {
        const uint8_t cooling =
            static_cast<uint8_t>(random8(((55 * 10) / count) + 2));
        heat[i] = qsub8(heat[i], cooling);
      }

      if (count >= 3) {
        for (uint16_t k = count - 1; k >= 2; k--) {
          heat[k] = static_cast<uint8_t>(
              (heat[k - 1] + heat[k - 2] + heat[k - 2]) / 3);
        }
      }

      if (random8() < 120) {
        const uint16_t sparkRange = std::min<uint16_t>(7, count);
        if (sparkRange > 0) {
          const uint16_t y = random8(sparkRange);
          heat[y] = qadd8(heat[y], static_cast<uint8_t>(160 + random8(95)));
        }
      }

      for (uint16_t j = 0; j < count; j++) {
        const uint8_t t192 =
            static_cast<uint8_t>((static_cast<uint16_t>(heat[j]) * 191) / 255);
        uint8_t heatramp = t192 & 0x3F;
        heatramp <<= 2;

        uint8_t fr = 0, fg = 0, fb = 0;
        if (t192 & 0x80) {
          fr = 255;
          fg = 255;
          fb = heatramp;
        } else if (t192 & 0x40) {
          fr = 255;
          fg = heatramp;
          fb = 0;
        } else {
          fr = heatramp;
          fg = 0;
          fb = 0;
        }

        strip[j] = lumyn::internal::domain::Color(
            static_cast<uint8_t>((fr + color.r) / 2),
            static_cast<uint8_t>((fg + color.g) / 2),
            static_cast<uint8_t>((fb + color.b) / 2));
      }

      return true;
    }};

static AnimationInstance Scanner = {
    .id = "Scanner",
    .stateMode = StateMode::LedCount,
    .stateCount = 2,
    .defaultDelay = 60,
    .defaultColor = lumyn::internal::domain::Color(255, 0, 0),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      if (count == 0) return true;

      const uint16_t desiredTotal =
          (count > 1) ? static_cast<uint16_t>((count - 1) * 2) : 1;
      const uint16_t providedTotal =
          static_cast<uint16_t>(count + Scanner.stateCount);
      const uint16_t effectiveState =
          static_cast<uint16_t>((static_cast<uint32_t>(state % providedTotal) *
                                 desiredTotal) /
                                (providedTotal == 0 ? 1 : providedTotal));

      uint16_t pos = effectiveState % desiredTotal;
      if (pos >= count) {
        pos = desiredTotal - pos;
      }

      for (uint16_t i = 0; i < count; i++) {
        const float distance = std::abs(static_cast<int16_t>(i) -
                                        static_cast<int16_t>(pos));
        const float brightness = std::exp((-distance * distance) / 8.0f);
        const uint8_t brightness8 =
            static_cast<uint8_t>(std::round(brightness * 255.0f));
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, brightness8);
        dimColor.g = scale8(dimColor.g, brightness8);
        dimColor.b = scale8(dimColor.b, brightness8);
        strip[i] = dimColor;
      }

      return true;
    }};

static AnimationInstance TheaterChase = {
    .id = "TheaterChase",
    .stateMode = StateMode::Constant,
    .stateCount = 3,
    .defaultDelay = 150,
    .defaultColor = lumyn::internal::domain::Color(255, 0, 255),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (uint16_t i = 0; i < count; i++) {
        if ((i + state) % 3 == 0) {
          strip[i] = color;
        } else {
          strip[i] = lumyn::internal::domain::Color::Black();
        }
      }

      return true;
    }};

static AnimationInstance Twinkle = {
    .id = "Twinkle",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 20,
    .defaultColor = lumyn::internal::domain::Color(255, 255, 0),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t /*state*/,
             uint16_t count) {
      static std::vector<uint8_t> brightness;
      static std::vector<uint8_t> direction;

      if (brightness.size() != count) {
        brightness.assign(count, 0);
        direction.assign(count, 0);
      }

      for (uint16_t i = 0; i < count; i++) {
        if (random8() < 5) {
          brightness[i] = 255;
          direction[i] = 1;
        }

        if (direction[i] == 1) {
          brightness[i] = qsub8(brightness[i], 8);
          if (brightness[i] < 20) {
            brightness[i] = 0;
            direction[i] = 0;
          }
        }

        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, brightness[i]);
        dimColor.g = scale8(dimColor.g, brightness[i]);
        dimColor.b = scale8(dimColor.b, brightness[i]);
        strip[i] = dimColor;
      }

      return true;
    }};

static AnimationInstance Meteor = {
    .id = "Meteor",
    .stateMode = StateMode::LedCount,
    .stateCount = 1,
    .defaultDelay = 30,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const uint8_t meteorSize = 5;
      const uint8_t meteorTrailDecay = 64;

      for (uint16_t i = 0; i < count; i++) {
        if (random8() > 128) {
          strip[i].fadeLightBy(meteorTrailDecay);
        }
      }

      for (uint8_t j = 0; j < meteorSize; j++) {
        int16_t pos = state - j;
        if (pos >= 0 && pos < count) {
          strip[pos] = color;
        }
      }

      return true;
    }};

static AnimationInstance Wave = {
    .id = "Wave",
    .stateMode = StateMode::Constant,
    .stateCount = 360,
    .defaultDelay = 10,
    .defaultColor = lumyn::internal::domain::Color(0, 100, 255),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const float waveCount = 2.0;

      for (uint16_t i = 0; i < count; i++) {
        float angle =
            (state * M_PI / 180.0) + (i * waveCount * 2 * M_PI / count);
        float brightness = (sin(angle) + 1.0) / 2.0;

        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, brightness * 255);
        dimColor.g = scale8(dimColor.g, brightness * 255);
        dimColor.b = scale8(dimColor.b, brightness * 255);
        strip[i] = dimColor;
      }

      return true;
    }};

static AnimationInstance Pulse = {
    .id = "Pulse",
    .stateMode = StateMode::Constant,
    .stateCount = 256,
    .defaultDelay = 8,
    .defaultColor = lumyn::internal::domain::Color(255, 20, 147),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      if (count == 0) return true;

      const uint16_t center = count / 2;
      const uint16_t maxDistance = std::max<uint16_t>(1, center);

      for (uint16_t i = 0; i < count; i++) {
        uint16_t distance = abs((int16_t)i - (int16_t)center);

        int16_t ringPos = state - (distance * 256 / maxDistance);
        if (ringPos < 0) ringPos += 256;

        const float brightness =
            (std::sin((ringPos * M_PI) / 128.0f) + 1.0f) / 2.0f;
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r =
            scale8(dimColor.r,
                   static_cast<uint8_t>(std::round(brightness * 255.0f)));
        dimColor.g =
            scale8(dimColor.g,
                   static_cast<uint8_t>(std::round(brightness * 255.0f)));
        dimColor.b =
            scale8(dimColor.b,
                   static_cast<uint8_t>(std::round(brightness * 255.0f)));
        strip[i] = dimColor;
      }

      return true;
    }};

static AnimationInstance Larson = {
    .id = "Larson",
    .stateMode = StateMode::LedCount,
    .stateCount = 2,
    .defaultDelay = 20,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const uint16_t totalStates = (count - 1) * 2;
      uint16_t pos = state % totalStates;

      if (pos >= count) {
        pos = totalStates - pos;
      }

      for (uint16_t i = 0; i < count; i++) {
        const float distance = abs((int16_t)i - (int16_t)pos);
        const float brightness = exp(-distance * distance / 8.0);
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, brightness * 255);
        dimColor.g = scale8(dimColor.g, brightness * 255);
        dimColor.b = scale8(dimColor.b, brightness * 255);
        strip[i] = dimColor;
      }

      return true;
    }};

static AnimationInstance Ripple = {
    .id = "Ripple",
    .stateMode = StateMode::Constant,
    .stateCount = 360,
    .defaultDelay = 75,
    .defaultColor = lumyn::internal::domain::Color(0, 206, 209),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      if (count == 0) return true;

      const uint16_t center = count / 2;

      for (uint16_t i = 0; i < count; i++) {
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, static_cast<uint8_t>(0.1f * 255));
        dimColor.g = scale8(dimColor.g, static_cast<uint8_t>(0.1f * 255));
        dimColor.b = scale8(dimColor.b, static_cast<uint8_t>(0.1f * 255));
        strip[i] = dimColor;
      }

      const uint8_t ringWidth = 3;
      const uint8_t ringSpeed = 2;

      for (uint8_t ring = 0; ring < 2; ring++) {
        const uint16_t ringPos =
            static_cast<uint16_t>(((state + ring * 180) * ringSpeed) %
                                  (count * 2));
        const float ringCenter = ringPos / 2.0f;

        for (uint16_t i = 0; i < count; i++) {
          const float distance =
              std::abs(static_cast<int16_t>(i) - static_cast<int16_t>(center));

          if (std::abs(distance - ringCenter) < ringWidth) {
            const float falloff =
                1.0f - std::abs(distance - ringCenter) / ringWidth;
            const float currentBrightness =
                (color.r > 0) ? (strip[i].r / static_cast<float>(color.r)) : 0.0f;
            const float newBrightness =
                std::min(1.0f, std::max(currentBrightness, falloff));

            lumyn::internal::domain::Color dimColor = color;
            const uint8_t brightness8 =
                static_cast<uint8_t>(std::round(newBrightness * 255.0f));
            dimColor.r = scale8(dimColor.r, brightness8);
            dimColor.g = scale8(dimColor.g, brightness8);
            dimColor.b = scale8(dimColor.b, brightness8);
            strip[i] = dimColor;
          }
        }
      }

      return true;
    }};

static AnimationInstance Confetti = {
    .id = "Confetti",
    .stateMode = StateMode::Constant,
    .stateCount = 200,
    .defaultDelay = 30,
    .defaultColor = lumyn::internal::domain::Color(255, 215, 0),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color /*color*/, uint16_t /*state*/,
             uint16_t count) {
      struct ConfettiParticle {
        uint16_t pos;
        float hue;
      };

      static std::vector<ConfettiParticle> confettiState;

      const uint16_t confettiCount =
          std::min<uint16_t>(static_cast<uint16_t>(count / 3), 20);

      if (confettiState.size() != confettiCount) {
        confettiState.clear();
        confettiState.reserve(confettiCount);
        for (uint16_t i = 0; i < confettiCount; i++) {
          confettiState.push_back(
              {.pos = static_cast<uint16_t>(random16(count)),
               .hue = (random8() / 255.0f) * 360.0f,
              });
        }
      }

      for (uint16_t i = 0; i < count; i++) {
        strip[i].fadeLightBy(20);  // ~8% fade per frame
      }

      for (auto &conf : confettiState) {
        if (random8() < 77) {  // ~30% chance to drift
          const int8_t direction = (random8() < 128) ? -1 : 1;
          conf.pos = static_cast<uint16_t>((conf.pos + count + direction) % count);
        }

        if (random8() < 13) {  // ~5% chance to change hue
          conf.hue = (random8() / 255.0f) * 360.0f;
        }

        const float brightness = 0.7f + (random8() / 255.0f) * 0.3f;
        const float hueWrapped = std::fmod(conf.hue, 360.0f);
        const uint8_t hue8 =
            static_cast<uint8_t>(std::round((hueWrapped / 360.0f) * 255.0f));
        const uint8_t value8 =
            static_cast<uint8_t>(std::round(brightness * 255.0f));

        strip[conf.pos] =
            lumyn::internal::domain::Color::FromHSV(hue8, 255, value8);
      }

      return true;
    }};

static AnimationInstance Lava = {
    .id = "Lava",
    .stateMode = StateMode::Constant,
    .stateCount = 360,
    .defaultDelay = 50,
    .defaultColor = lumyn::internal::domain::Color(255, 80, 0),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      for (uint16_t i = 0; i < count; i++) {
        const float wave1 = sin(((state * 2 + i * 15) * M_PI) / 180.0);
        const float wave2 = sin(((state * 3 + i * 10) * M_PI) / 180.0);
        const float wave3 = sin(((state * 1.5 + i * 20) * M_PI) / 180.0);

        const float combined = (wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2);
        const float brightness = (combined + 1.0) / 2.0;

        const float finalBrightness = pow(brightness, 0.7);
        const float warmth = 0.7 + finalBrightness * 0.3;

        strip[i] = lumyn::internal::domain::Color(
            color.r * warmth * finalBrightness, color.g * finalBrightness * 0.6,
            color.b * finalBrightness * 0.3);
      }

      return true;
    }};

static AnimationInstance Plasma = {
    .id = "Plasma",
    .stateMode = StateMode::Constant,
    .stateCount = 360,
    .defaultDelay = 20,
    .defaultColor = lumyn::internal::domain::Color(75, 0, 130),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const float r = color.r / 255.0f;
      const float g = color.g / 255.0f;
      const float b = color.b / 255.0f;

      const float maxVal = std::max({r, g, b});
      const float minVal = std::min({r, g, b});
      const float delta = maxVal - minVal;

      float baseHue = 0.0f;
      if (delta != 0.0f) {
        if (maxVal == r) {
          baseHue = 60.0f * std::fmod(((g - b) / delta), 6.0f);
        } else if (maxVal == g) {
          baseHue = 60.0f * (((b - r) / delta) + 2.0f);
        } else {
          baseHue = 60.0f * (((r - g) / delta) + 4.0f);
        }
      }
      if (baseHue < 0.0f) baseHue += 360.0f;

      const float baseSaturation =
          (maxVal == 0.0f) ? 0.0f : (delta / maxVal) * 100.0f;

      for (uint16_t i = 0; i < count; i++) {
        const float t = state * 0.04f;
        const float x = (count == 0) ? 0.0f : (static_cast<float>(i) / count);

        const float plasma =
            std::sin(x * 4.0f + t) + std::sin(x * 7.0f - t * 1.3f) +
            std::sin(x * 11.0f + t * 0.7f);

        const float hueShift = ((plasma + 3.0f) / 6.0f) * 180.0f - 90.0f;
        const float hue =
            std::fmod(baseHue + hueShift + 360.0f, 360.0f);

        const float saturation =
            std::clamp(baseSaturation + plasma * 8.0f, 50.0f, 100.0f);

        const float value =
            (55.0f + (std::sin(plasma * 1.5f) + 1.0f) * 22.5f) / 100.0f;

        const uint8_t hue8 =
            static_cast<uint8_t>(std::round((hue / 360.0f) * 255.0f));
        const uint8_t sat8 =
            static_cast<uint8_t>(std::round((saturation / 100.0f) * 255.0f));
        const uint8_t val8 =
            static_cast<uint8_t>(std::round(std::clamp(value, 0.0f, 1.0f) *
                                            255.0f));

        strip[i] = lumyn::internal::domain::Color::FromHSV(hue8, sat8, val8);
      }

      return true;
    }};

static AnimationInstance Heartbeat = {
    .id = "Heartbeat",
    .stateMode = StateMode::Constant,
    .stateCount = 60,
    .defaultDelay = 30,
    .defaultColor = lumyn::internal::domain::Color(255, 0, 0),
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const uint8_t cycle = state % 60;
      float brightness = 0;

      if (cycle < 8) {
        brightness = sin((cycle / 8.0) * M_PI);
      } else if (cycle >= 12 && cycle < 18) {
        brightness = sin(((cycle - 12) / 6.0) * M_PI) * 0.8;
      }

      for (uint16_t i = 0; i < count; i++) {
        lumyn::internal::domain::Color dimColor = color;
        dimColor.r = scale8(dimColor.r, brightness * 255);
        dimColor.g = scale8(dimColor.g, brightness * 255);
        dimColor.b = scale8(dimColor.b, brightness * 255);
        strip[i] = dimColor;
      }

      return true;
    }};

static AnimationInstance Stripes = {
    .id = "Stripes",
    .stateMode = StateMode::Constant,
    .stateCount = 200,
    .defaultDelay = 30,
    .defaultColor =
        lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor,
    .cb = [](lumyn::internal::domain::Color *strip,
             lumyn::internal::domain::Color color, uint16_t state,
             uint16_t count) {
      const uint8_t stripeLength = 3;
      // Calculate offset based on state to create moving effect
      // Cycle through a full pattern (stripeLength * 2 for color + black)
      const uint16_t patternLength = stripeLength * 2;
      const uint16_t offset = (state * stripeLength) % patternLength;

      for (uint16_t i = 0; i < count; i++) {
        // Calculate position in the pattern
        const uint16_t patternPos = (i + offset) % patternLength;
        
        if (patternPos < stripeLength) {
          // Show color stripe
          strip[i] = color;
        } else {
          // Show black stripe
          strip[i] = lumyn::internal::domain::Color::Black();
        }
      }

      return true;
    }};

static std::vector<AnimationInstance> BuiltInAnimations = {
    None,   Fill,    Blink,    Breathe,      RainbowRoll,      SineRoll,
    Chase,  FadeIn,  FadeOut,  RainbowCycle, AlternateBreathe, GrowingBreathe,
    Comet,  Sparkle, Fire,     Scanner,      TheaterChase,     Twinkle,
    Meteor, Wave,    Pulse,    Larson,       Ripple,           Confetti,
    Lava,   Plasma,  Heartbeat, Stripes};

}  // namespace lumyn::internal::Animation

namespace lumyn::led {
  // Helper function to look up animation instance by enum
  inline const lumyn::internal::Animation::AnimationInstance* GetAnimationInstance(Animation anim) {
    using namespace lumyn::internal::Animation;
    auto animNameIt = kAnimationMap.find(anim);
    if (animNameIt == kAnimationMap.end()) {
      return nullptr;
    }
    std::string_view animName = animNameIt->second;
    for (const auto& instance : BuiltInAnimations) {
      if (instance.id == animName) {
        return &instance;
      }
    }
    return nullptr;
  }
} // namespace lumyn::led
