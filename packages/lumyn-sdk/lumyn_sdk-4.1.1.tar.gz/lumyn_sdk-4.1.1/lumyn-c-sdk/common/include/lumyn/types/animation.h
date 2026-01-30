/**
 * @file animation.h
 * @brief C-compatible animation type definitions
 * 
 * This header defines animation types that work in both C and C++.
 * C++ code can use the lumyn::led namespace aliases for convenience.
 */
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Animation types for LED strips and matrices
 */
typedef enum lumyn_animation {
  LUMYN_ANIMATION_NONE = 0,
  LUMYN_ANIMATION_FILL = 1,
  LUMYN_ANIMATION_BLINK = 2,
  LUMYN_ANIMATION_BREATHE = 3,
  LUMYN_ANIMATION_RAINBOW_ROLL = 4,
  LUMYN_ANIMATION_SINE_ROLL = 5,
  LUMYN_ANIMATION_CHASE = 6,
  LUMYN_ANIMATION_FADE_IN = 7,
  LUMYN_ANIMATION_FADE_OUT = 8,
  LUMYN_ANIMATION_RAINBOW_CYCLE = 9,
  LUMYN_ANIMATION_ALTERNATE_BREATHE = 10,
  LUMYN_ANIMATION_GROWING_BREATHE = 11,
  LUMYN_ANIMATION_COMET = 12,
  LUMYN_ANIMATION_SPARKLE = 13,
  LUMYN_ANIMATION_FIRE = 14,
  LUMYN_ANIMATION_SCANNER = 15,
  LUMYN_ANIMATION_THEATER_CHASE = 16,
  LUMYN_ANIMATION_TWINKLE = 17,
  LUMYN_ANIMATION_METEOR = 18,
  LUMYN_ANIMATION_WAVE = 19,
  LUMYN_ANIMATION_PULSE = 20,
  LUMYN_ANIMATION_LARSON = 21,
  LUMYN_ANIMATION_RIPPLE = 22,
  LUMYN_ANIMATION_CONFETTI = 23,
  LUMYN_ANIMATION_LAVA = 24,
  LUMYN_ANIMATION_PLASMA = 25,
  LUMYN_ANIMATION_HEARTBEAT = 26,
} lumyn_animation_t;

#ifdef __cplusplus
} // extern "C"

// C++ convenience aliases
namespace lumyn::led {

using Animation = lumyn_animation_t;

// Scoped constants for C++ users who prefer Animation::None style
namespace AnimationType {
  inline constexpr Animation None = LUMYN_ANIMATION_NONE;
  inline constexpr Animation Fill = LUMYN_ANIMATION_FILL;
  inline constexpr Animation Blink = LUMYN_ANIMATION_BLINK;
  inline constexpr Animation Breathe = LUMYN_ANIMATION_BREATHE;
  inline constexpr Animation RainbowRoll = LUMYN_ANIMATION_RAINBOW_ROLL;
  inline constexpr Animation SineRoll = LUMYN_ANIMATION_SINE_ROLL;
  inline constexpr Animation Chase = LUMYN_ANIMATION_CHASE;
  inline constexpr Animation FadeIn = LUMYN_ANIMATION_FADE_IN;
  inline constexpr Animation FadeOut = LUMYN_ANIMATION_FADE_OUT;
  inline constexpr Animation RainbowCycle = LUMYN_ANIMATION_RAINBOW_CYCLE;
  inline constexpr Animation AlternateBreathe = LUMYN_ANIMATION_ALTERNATE_BREATHE;
  inline constexpr Animation GrowingBreathe = LUMYN_ANIMATION_GROWING_BREATHE;
  inline constexpr Animation Comet = LUMYN_ANIMATION_COMET;
  inline constexpr Animation Sparkle = LUMYN_ANIMATION_SPARKLE;
  inline constexpr Animation Fire = LUMYN_ANIMATION_FIRE;
  inline constexpr Animation Scanner = LUMYN_ANIMATION_SCANNER;
  inline constexpr Animation TheaterChase = LUMYN_ANIMATION_THEATER_CHASE;
  inline constexpr Animation Twinkle = LUMYN_ANIMATION_TWINKLE;
  inline constexpr Animation Meteor = LUMYN_ANIMATION_METEOR;
  inline constexpr Animation Wave = LUMYN_ANIMATION_WAVE;
  inline constexpr Animation Pulse = LUMYN_ANIMATION_PULSE;
  inline constexpr Animation Larson = LUMYN_ANIMATION_LARSON;
  inline constexpr Animation Ripple = LUMYN_ANIMATION_RIPPLE;
  inline constexpr Animation Confetti = LUMYN_ANIMATION_CONFETTI;
  inline constexpr Animation Lava = LUMYN_ANIMATION_LAVA;
  inline constexpr Animation Plasma = LUMYN_ANIMATION_PLASMA;
  inline constexpr Animation Heartbeat = LUMYN_ANIMATION_HEARTBEAT;
}

} // namespace lumyn::led

#endif // __cplusplus

