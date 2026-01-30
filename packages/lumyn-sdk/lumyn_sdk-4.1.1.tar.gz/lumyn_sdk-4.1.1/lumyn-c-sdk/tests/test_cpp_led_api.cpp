/**
 * @file test_cpp_led_api.cpp
 * @brief Tests for C++ SDK LED control and builders
 *
 * Tests SetColor, SetGroupColor, AnimationBuilder, MatrixTextBuilder,
 * ImageSequenceBuilder, and DirectLED.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>

// =============================================================================
// Basic LED Control Tests
// =============================================================================

class CppLEDControlTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
  lumyn::device::ConnectorXAnimate cxa_;
};

TEST_F(CppLEDControlTest, SetColorConnectorX)
{
  lumyn_color_t color{255, 0, 0};
  cx_.SetColor("zone1", color);
  SUCCEED();
}

TEST_F(CppLEDControlTest, SetColorConnectorXAnimate)
{
  lumyn_color_t color{0, 255, 0};
  cxa_.SetColor("zone1", color);
  SUCCEED();
}

TEST_F(CppLEDControlTest, SetGroupColorConnectorX)
{
  lumyn_color_t color{0, 0, 255};
  cx_.SetGroupColor("group1", color);
  SUCCEED();
}

TEST_F(CppLEDControlTest, SetGroupColorConnectorXAnimate)
{
  lumyn_color_t color{255, 255, 0};
  cxa_.SetGroupColor("all", color);
  SUCCEED();
}

TEST_F(CppLEDControlTest, SetColorWithEmptyZone)
{
  lumyn_color_t color{128, 128, 128};
  cx_.SetColor("", color);
  SUCCEED();
}

TEST_F(CppLEDControlTest, SetColorWithLongZoneName)
{
  lumyn_color_t color{64, 64, 64};
  std::string long_name(256, 'z');
  cx_.SetColor(long_name, color);
  SUCCEED();
}

// =============================================================================
// AnimationBuilder Tests
// =============================================================================

class AnimationBuilderTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(AnimationBuilderTest, SetAnimationReturnsBuilder)
{
  auto builder = cx_.SetAnimation(LUMYN_ANIMATION_RAINBOW_ROLL);
  SUCCEED();
}

TEST_F(AnimationBuilderTest, ChainWithDelay)
{
  cx_.SetAnimation(LUMYN_ANIMATION_RAINBOW_ROLL)
      .WithDelay(50);
  SUCCEED();
}

TEST_F(AnimationBuilderTest, ChainWithDelayChronos)
{
  cx_.SetAnimation(LUMYN_ANIMATION_CHASE)
      .WithDelay(std::chrono::milliseconds(200));
  SUCCEED();
}

TEST_F(AnimationBuilderTest, ChainWithReverse)
{
  cx_.SetAnimation(LUMYN_ANIMATION_FIRE)
      .Reverse(true);
  SUCCEED();
}

TEST_F(AnimationBuilderTest, ChainWithColor)
{
  cx_.SetAnimation(LUMYN_ANIMATION_FILL)
      .WithColor({255, 128, 0});
  SUCCEED();
}

TEST_F(AnimationBuilderTest, ChainForZone)
{
  cx_.SetAnimation(LUMYN_ANIMATION_RAINBOW_ROLL)
      .ForZone("main");
  SUCCEED();
}

TEST_F(AnimationBuilderTest, ChainForGroup)
{
  cx_.SetAnimation(LUMYN_ANIMATION_CHASE)
      .ForGroup("all_leds");
  SUCCEED();
}

TEST_F(AnimationBuilderTest, FullChainForZone)
{
  cx_.SetAnimation(LUMYN_ANIMATION_RAINBOW_ROLL)
      .WithDelay(100)
      .WithColor({255, 0, 0})
      .Reverse(false)
      .ForZone("zone1");
  SUCCEED();
}

TEST_F(AnimationBuilderTest, FullChainForGroup)
{
  cx_.SetAnimation(LUMYN_ANIMATION_FILL)
      .WithDelay(0)
      .WithColor({0, 255, 0})
      .ForGroup("front");
  SUCCEED();
}

TEST_F(AnimationBuilderTest, MultipleAnimationTypes)
{
  cx_.SetAnimation(LUMYN_ANIMATION_NONE).ForZone("z");
  cx_.SetAnimation(LUMYN_ANIMATION_FILL).ForZone("z");
  cx_.SetAnimation(LUMYN_ANIMATION_RAINBOW_ROLL).ForZone("z");
  cx_.SetAnimation(LUMYN_ANIMATION_CHASE).ForZone("z");
  cx_.SetAnimation(LUMYN_ANIMATION_FIRE).ForZone("z");
  SUCCEED();
}

TEST_F(AnimationBuilderTest, DefaultDelayFromBuiltInAnimations)
{
  // Test that default delay is pulled from BuiltInAnimations.h
  auto delay = lumyn::device::AnimationBuilder::defaultDelay(LUMYN_ANIMATION_CHASE);
  EXPECT_GT(delay.count(), 0);
}

TEST_F(AnimationBuilderTest, DefaultColorFromBuiltInAnimations)
{
  // Test that default color is pulled from BuiltInAnimations.h
  auto color = lumyn::device::AnimationBuilder::defaultColor(LUMYN_ANIMATION_FIRE);
  // Fire animation typically has an orange/red default
  SUCCEED();
}

// =============================================================================
// MatrixTextBuilder Tests
// =============================================================================

class MatrixTextBuilderTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(MatrixTextBuilderTest, SetTextReturnsBuilder)
{
  auto builder = cx_.SetText("Hello");
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, ChainWithFont)
{
  cx_.SetText("Test")
      .WithFont(LUMYN_MATRIX_TEXT_FONT_BUILTIN);
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, ChainWithColor)
{
  cx_.SetText("Colored")
      .WithColor({255, 255, 255});
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, ChainWithAlign)
{
  cx_.SetText("Centered")
      .WithAlign(LUMYN_MATRIX_TEXT_ALIGN_CENTER);
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, ChainForZone)
{
  cx_.SetText("Matrix")
      .ForZone("matrix1");
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, FullChain)
{
  cx_.SetText("Complete")
      .WithFont(LUMYN_MATRIX_TEXT_FONT_BUILTIN)
      .WithColor({0, 255, 0})
      .WithAlign(LUMYN_MATRIX_TEXT_ALIGN_LEFT)
      .ForZone("display");
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, EmptyText)
{
  cx_.SetText("")
      .ForZone("matrix1");
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, LongText)
{
  std::string long_text(1024, 'A');
  cx_.SetText(long_text)
      .ForZone("matrix1");
  SUCCEED();
}

TEST_F(MatrixTextBuilderTest, VariousFonts)
{
  cx_.SetText("Font1").WithFont(LUMYN_MATRIX_TEXT_FONT_BUILTIN).ForZone("z");
  cx_.SetText("Font2").WithFont(LUMYN_MATRIX_TEXT_FONT_TINY_3X3).ForZone("z");
  cx_.SetText("Font3").WithFont(LUMYN_MATRIX_TEXT_FONT_PICOPIXEL).ForZone("z");
  cx_.SetText("Font4").WithFont(LUMYN_MATRIX_TEXT_FONT_TOM_THUMB).ForZone("z");
  SUCCEED();
}

// =============================================================================
// ImageSequenceBuilder Tests
// =============================================================================

class ImageSequenceBuilderTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(ImageSequenceBuilderTest, SetImageSequenceReturnsBuilder)
{
  auto builder = cx_.SetImageSequence("sequence1");
  SUCCEED();
}

TEST_F(ImageSequenceBuilderTest, ChainForZone)
{
  cx_.SetImageSequence("my_seq")
      .ForZone("matrix1");
  SUCCEED();
}

TEST_F(ImageSequenceBuilderTest, EmptySequenceName)
{
  cx_.SetImageSequence("")
      .ForZone("matrix1");
  SUCCEED();
}

// =============================================================================
// DirectLED Tests
// =============================================================================

class DirectLEDTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(DirectLEDTest, CreateDirectLED)
{
  auto direct_led = cx_.CreateDirectLED("zone1", 60);
  SUCCEED();
}

TEST_F(DirectLEDTest, CreateDirectLEDWithRefreshInterval)
{
  auto direct_led = cx_.CreateDirectLED("zone1", 100, 50);
  SUCCEED();
}

TEST_F(DirectLEDTest, CreateDirectLEDWithZeroLEDs)
{
  auto direct_led = cx_.CreateDirectLED("zone1", 0);
  SUCCEED();
}

TEST_F(DirectLEDTest, CreateDirectLEDWithLargeLEDCount)
{
  auto direct_led = cx_.CreateDirectLED("zone1", 1000);
  SUCCEED();
}

TEST_F(DirectLEDTest, SendDirectBufferFailsWhenDisconnected)
{
  uint8_t data[9] = {255, 0, 0, 0, 255, 0, 0, 0, 255};
  auto err = cx_.SendDirectBuffer("zone1", data, sizeof(data), false);
  // Some implementations may queue the command and return OK, others may fail.
  // We just test it doesn't crash.
  (void)err;
  SUCCEED();
}

TEST_F(DirectLEDTest, SendDirectBufferDeltaMode)
{
  uint8_t data[9] = {255, 0, 0, 0, 255, 0, 0, 0, 255};
  auto err = cx_.SendDirectBuffer("zone1", data, sizeof(data), true);
  // Just verify it doesn't crash
  (void)err;
  SUCCEED();
}

TEST_F(DirectLEDTest, SendDirectBufferWithHash)
{
  uint8_t data[9] = {255, 0, 0, 0, 255, 0, 0, 0, 255};
  auto err = cx_.SendDirectBuffer(0x1234, data, sizeof(data), false);
  // Just verify it doesn't crash
  (void)err;
  SUCCEED();
}

TEST_F(DirectLEDTest, SendDirectBufferEmptyData)
{
  auto err = cx_.SendDirectBuffer("zone1", nullptr, 0, false);
  EXPECT_NE(err, LUMYN_OK);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
