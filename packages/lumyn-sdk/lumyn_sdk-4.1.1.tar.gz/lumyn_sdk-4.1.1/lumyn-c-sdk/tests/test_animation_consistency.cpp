#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_animation_consistency.cpp
 * @brief Tests to verify AnimationBuilder defaults match BuiltInAnimations.h
 *
 * This test ensures that AnimationBuilder queries BuiltInAnimations correctly
 * and that SDK animation defaults match firmware defaults.
 */

#include <gtest/gtest.h>
#include <lumyn/cpp/device/builder/AnimationBuilder.hpp>
#include <lumyn/led/BuiltInAnimations.h>
#include <lumyn/led/Animation.h>
#include <chrono>

class AnimationConsistencyTest : public ::testing::Test
{
protected:
  void SetUp() override
  {
  }

  void TearDown() override
  {
  }
};

// Test that AnimationBuilder defaultDelay matches BuiltInAnimations
TEST_F(AnimationConsistencyTest, DefaultDelayMatchesBuiltInAnimations)
{
  using namespace lumyn::led;
  using namespace lumyn::device;

  // Test specific animations that were previously mismatched
  auto chaseDelay = AnimationBuilder::defaultDelay(LUMYN_ANIMATION_CHASE);
  auto cometDelay = AnimationBuilder::defaultDelay(LUMYN_ANIMATION_COMET);
  auto scannerDelay = AnimationBuilder::defaultDelay(LUMYN_ANIMATION_SCANNER);
  auto breatheDelay = AnimationBuilder::defaultDelay(LUMYN_ANIMATION_BREATHE);

  // Get expected values from BuiltInAnimations
  const auto* chaseInstance = GetAnimationInstance(LUMYN_ANIMATION_CHASE);
  const auto* cometInstance = GetAnimationInstance(LUMYN_ANIMATION_COMET);
  const auto* scannerInstance = GetAnimationInstance(LUMYN_ANIMATION_SCANNER);
  const auto* breatheInstance = GetAnimationInstance(LUMYN_ANIMATION_BREATHE);

  ASSERT_NE(chaseInstance, nullptr);
  ASSERT_NE(cometInstance, nullptr);
  ASSERT_NE(scannerInstance, nullptr);
  ASSERT_NE(breatheInstance, nullptr);

  // Verify delays match (these were previously mismatched)
  EXPECT_EQ(chaseDelay.count(), chaseInstance->defaultDelay) 
      << "Chase delay mismatch: SDK=" << chaseDelay.count() 
      << "ms, Firmware=" << chaseInstance->defaultDelay << "ms";
  
  EXPECT_EQ(cometDelay.count(), cometInstance->defaultDelay)
      << "Comet delay mismatch: SDK=" << cometDelay.count() 
      << "ms, Firmware=" << cometInstance->defaultDelay << "ms";
  
  EXPECT_EQ(scannerDelay.count(), scannerInstance->defaultDelay)
      << "Scanner delay mismatch: SDK=" << scannerDelay.count() 
      << "ms, Firmware=" << scannerInstance->defaultDelay << "ms";
  
  EXPECT_EQ(breatheDelay.count(), breatheInstance->defaultDelay)
      << "Breathe delay mismatch: SDK=" << breatheDelay.count() 
      << "ms, Firmware=" << breatheInstance->defaultDelay << "ms";
}

// Test that AnimationBuilder defaultColor matches BuiltInAnimations
TEST_F(AnimationConsistencyTest, DefaultColorMatchesBuiltInAnimations)
{
  using namespace lumyn::led;
  using namespace lumyn::device;

  // Test Sparkle which was previously mismatched (White vs Orange)
  auto sparkleColor = AnimationBuilder::defaultColor(LUMYN_ANIMATION_SPARKLE);
  const auto* sparkleInstance = GetAnimationInstance(LUMYN_ANIMATION_SPARKLE);

  ASSERT_NE(sparkleInstance, nullptr);

  EXPECT_EQ(sparkleColor.r, sparkleInstance->defaultColor.r)
      << "Sparkle color R mismatch: SDK=" << static_cast<int>(sparkleColor.r) 
      << ", Firmware=" << static_cast<int>(sparkleInstance->defaultColor.r);
  
  EXPECT_EQ(sparkleColor.g, sparkleInstance->defaultColor.g)
      << "Sparkle color G mismatch: SDK=" << static_cast<int>(sparkleColor.g) 
      << ", Firmware=" << static_cast<int>(sparkleInstance->defaultColor.g);
  
  EXPECT_EQ(sparkleColor.b, sparkleInstance->defaultColor.b)
      << "Sparkle color B mismatch: SDK=" << static_cast<int>(sparkleColor.b) 
      << ", Firmware=" << static_cast<int>(sparkleInstance->defaultColor.b);

  // Verify Sparkle is White (255, 255, 255) as defined in BuiltInAnimations
  EXPECT_EQ(sparkleColor.r, 255);
  EXPECT_EQ(sparkleColor.g, 255);
  EXPECT_EQ(sparkleColor.b, 255);

  // Test other animations for consistency
  auto cometColor = AnimationBuilder::defaultColor(LUMYN_ANIMATION_COMET);
  auto fireColor = AnimationBuilder::defaultColor(LUMYN_ANIMATION_FIRE);
  auto scannerColor = AnimationBuilder::defaultColor(LUMYN_ANIMATION_SCANNER);

  const auto* cometInstance = GetAnimationInstance(LUMYN_ANIMATION_COMET);
  const auto* fireInstance = GetAnimationInstance(LUMYN_ANIMATION_FIRE);
  const auto* scannerInstance = GetAnimationInstance(LUMYN_ANIMATION_SCANNER);

  ASSERT_NE(cometInstance, nullptr);
  ASSERT_NE(fireInstance, nullptr);
  ASSERT_NE(scannerInstance, nullptr);

  EXPECT_EQ(cometColor.r, cometInstance->defaultColor.r);
  EXPECT_EQ(cometColor.g, cometInstance->defaultColor.g);
  EXPECT_EQ(cometColor.b, cometInstance->defaultColor.b);

  EXPECT_EQ(fireColor.r, fireInstance->defaultColor.r);
  EXPECT_EQ(fireColor.g, fireInstance->defaultColor.g);
  EXPECT_EQ(fireColor.b, fireInstance->defaultColor.b);

  EXPECT_EQ(scannerColor.r, scannerInstance->defaultColor.r);
  EXPECT_EQ(scannerColor.g, scannerInstance->defaultColor.g);
  EXPECT_EQ(scannerColor.b, scannerInstance->defaultColor.b);
}

// Test that all animations in kAnimationMap have corresponding instances
TEST_F(AnimationConsistencyTest, AllAnimationsHaveInstances)
{
  using namespace lumyn::led;

  // Verify that GetAnimationInstance works for all animations in the map
  for (const auto& [anim, name] : kAnimationMap)
  {
    const auto* instance = GetAnimationInstance(anim);
    EXPECT_NE(instance, nullptr) 
        << "Animation " << name << " (enum=" << static_cast<int>(anim) 
        << ") has no corresponding instance in BuiltInAnimations";
    
    if (instance)
    {
      EXPECT_EQ(instance->id, name)
          << "Animation instance ID mismatch for " << name;
    }
  }
}

// Test fallback behavior for invalid animation
TEST_F(AnimationConsistencyTest, FallbackBehavior)
{
  using namespace lumyn::led;
  using namespace lumyn::device;

  // Test with an invalid animation enum value (beyond the known range)
  // This should return fallback values
  lumyn_animation_t invalidAnim = static_cast<lumyn_animation_t>(9999);
  
  auto delay = AnimationBuilder::defaultDelay(invalidAnim);
  auto color = AnimationBuilder::defaultColor(invalidAnim);

  // Should return fallback values from Constants::LED constants
  EXPECT_EQ(delay.count(), lumyn::internal::Constants::LED::kDefaultAnimationDelay);
  const auto& expectedColor = lumyn::internal::Constants::LED::kDefaultAnimationColor;
  EXPECT_EQ(color.r, expectedColor.r);
  EXPECT_EQ(color.g, expectedColor.g);
  EXPECT_EQ(color.b, expectedColor.b);
}
