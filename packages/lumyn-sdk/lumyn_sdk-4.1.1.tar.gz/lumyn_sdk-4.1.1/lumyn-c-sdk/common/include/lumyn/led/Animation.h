#pragma once

#include <map>
#include <string_view>

#include "lumyn/types/animation.h"

namespace lumyn::led
{
  // Animation type is now defined in lumyn/types/animation.h as lumyn_animation_t
  // The C++ alias Animation = lumyn_animation_t is provided there.
  
  // String lookup map for animation names
  const std::map<Animation, std::string_view> kAnimationMap =
      {
          {LUMYN_ANIMATION_FILL, "Fill"},
          {LUMYN_ANIMATION_BLINK, "Blink"},
          {LUMYN_ANIMATION_BREATHE, "Breathe"},
          {LUMYN_ANIMATION_RAINBOW_ROLL, "RainbowRoll"},
          {LUMYN_ANIMATION_SINE_ROLL, "SineRoll"},
          {LUMYN_ANIMATION_CHASE, "Chase"},
          {LUMYN_ANIMATION_FADE_IN, "FadeIn"},
          {LUMYN_ANIMATION_FADE_OUT, "FadeOut"},
          {LUMYN_ANIMATION_RAINBOW_CYCLE, "RainbowCycle"},
          {LUMYN_ANIMATION_ALTERNATE_BREATHE, "AlternateBreathe"},
          {LUMYN_ANIMATION_GROWING_BREATHE, "GrowingBreathe"},
          {LUMYN_ANIMATION_COMET, "Comet"},
          {LUMYN_ANIMATION_SPARKLE, "Sparkle"},
          {LUMYN_ANIMATION_FIRE, "Fire"},
          {LUMYN_ANIMATION_SCANNER, "Scanner"},
          {LUMYN_ANIMATION_THEATER_CHASE, "TheaterChase"},
          {LUMYN_ANIMATION_TWINKLE, "Twinkle"},
          {LUMYN_ANIMATION_METEOR, "Meteor"},
          {LUMYN_ANIMATION_WAVE, "Wave"},
          {LUMYN_ANIMATION_PULSE, "Pulse"},
          {LUMYN_ANIMATION_LARSON, "Larson"},
          {LUMYN_ANIMATION_RIPPLE, "Ripple"},
          {LUMYN_ANIMATION_CONFETTI, "Confetti"},
          {LUMYN_ANIMATION_LAVA, "Lava"},
          {LUMYN_ANIMATION_PLASMA, "Plasma"},
          {LUMYN_ANIMATION_HEARTBEAT, "Heartbeat"},
  };
} // namespace lumyn::led
