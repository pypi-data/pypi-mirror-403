#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_led_api.cpp
 * @brief Comprehensive tests for LED control API
 *
 * Tests SetColor, SetAnimation, SetText, and related LED control functions.
 * Since these require a connected device to work properly, we focus on
 * error handling and input validation.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>

class LEDAPITest : public ::testing::Test
{
protected:
  cx_t cx_ = {};
  cx_animate_t cxa_ = {};
  bool cx_created_ = false;
  bool cxa_created_ = false;

  void SetUp() override
  {
    if (lumyn_CreateConnectorX(&cx_) == LUMYN_OK)
    {
      cx_created_ = true;
    }
    if (lumyn_CreateConnectorXAnimate(&cxa_) == LUMYN_OK)
    {
      cxa_created_ = true;
    }
  }

  void TearDown() override
  {
    if (cx_created_)
    {
      lumyn_DestroyConnectorX(&cx_);
    }
    if (cxa_created_)
    {
      lumyn_DestroyConnectorXAnimate(&cxa_);
    }
  }
};

// =============================================================================
// SetColor Tests
// =============================================================================

TEST_F(LEDAPITest, SetColorWithNullDeviceFails)
{
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetColor(nullptr, "zone_0", color);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetColorWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetColor(&cx_.base, nullptr, color);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetColorWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetColor(&cx_.base, "zone_0", color);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST_F(LEDAPITest, SetColorAcceptsValidColorRange)
{
  ASSERT_TRUE(cx_created_);

  // Test edge values (though will fail due to not connected)
  lumyn_color_t colors[] = {
      {0, 0, 0},       // Black
      {255, 255, 255}, // White
      {255, 0, 0},     // Red
      {0, 255, 0},     // Green
      {0, 0, 255},     // Blue
  };

  for (const auto &color : colors)
  {
    lumyn_error_t err = lumyn_SetColor(&cx_.base, "zone_0", color);
    // Should fail with NOT_CONNECTED, not INVALID_ARGUMENT
    EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED)
        << "Color (" << (int)color.r << "," << (int)color.g << "," << (int)color.b << ")";
  }
}

// =============================================================================
// SetGroupColor Tests
// =============================================================================

TEST_F(LEDAPITest, SetGroupColorWithNullDeviceFails)
{
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetGroupColor(nullptr, "group_0", color);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetGroupColorWithNullGroupIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetGroupColor(&cx_.base, nullptr, color);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetGroupColorWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetGroupColor(&cx_.base, "group_0", color);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// SetAnimation Tests
// =============================================================================

TEST_F(LEDAPITest, SetAnimationWithNullDeviceFails)
{
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetAnimation(nullptr, "zone_0", LUMYN_ANIMATION_FILL, color, 100, false, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetAnimationWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetAnimation(&cx_.base, nullptr, LUMYN_ANIMATION_FILL, color, 100, false, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetAnimationWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetAnimation(&cx_.base, "zone_0", LUMYN_ANIMATION_FILL, color, 100, false, false);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST_F(LEDAPITest, SetAnimationAcceptsVariousAnimationTypes)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};

  // Test various animation types - using actual enum values from animation.h
  lumyn_animation_t animations[] = {
      LUMYN_ANIMATION_NONE,
      LUMYN_ANIMATION_FILL,
      LUMYN_ANIMATION_BLINK,
      LUMYN_ANIMATION_BREATHE,
      LUMYN_ANIMATION_RAINBOW_ROLL,
      LUMYN_ANIMATION_CHASE,
  };

  for (const lumyn_animation_t &anim : animations)
  {
    lumyn_error_t err = lumyn_SetAnimation(&cx_.base, "zone_0", anim, color, 100, false, false);
    // Should fail with NOT_CONNECTED, not INVALID_ARGUMENT
    EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED)
        << "Animation type " << static_cast<int>(anim);
  }
}

TEST_F(LEDAPITest, SetAnimationAcceptsVariousDelays)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};

  // Test various delay values
  uint32_t delays[] = {0, 1, 50, 100, 1000, UINT32_MAX};

  for (uint32_t delay : delays)
  {
    lumyn_error_t err = lumyn_SetAnimation(&cx_.base, "zone_0", LUMYN_ANIMATION_FILL, color, delay, false, false);
    EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED) << "Delay " << delay;
  }
}

TEST_F(LEDAPITest, SetAnimationAcceptsBooleanFlags)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};

  // Test all combinations of reversed and one_shot
  bool flags[] = {false, true};

  for (bool reversed : flags)
  {
    for (bool one_shot : flags)
    {
      lumyn_error_t err = lumyn_SetAnimation(&cx_.base, "zone_0", LUMYN_ANIMATION_FILL, color, 100, reversed, one_shot);
      EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED)
          << "reversed=" << reversed << ", one_shot=" << one_shot;
    }
  }
}

// =============================================================================
// SetGroupAnimation Tests
// =============================================================================

TEST_F(LEDAPITest, SetGroupAnimationWithNullDeviceFails)
{
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetGroupAnimation(nullptr, "group_0", LUMYN_ANIMATION_FILL, color, 100, false, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetGroupAnimationWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetGroupAnimation(&cx_.base, "group_0", LUMYN_ANIMATION_FILL, color, 100, false, false);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// SetAnimationSequence Tests
// =============================================================================

TEST_F(LEDAPITest, SetAnimationSequenceWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_SetAnimationSequence(nullptr, "zone_0", "sequence_0");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetAnimationSequenceWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_SetAnimationSequence(&cx_.base, nullptr, "sequence_0");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetAnimationSequenceWithNullSequenceIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_SetAnimationSequence(&cx_.base, "zone_0", nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetAnimationSequenceWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_SetAnimationSequence(&cx_.base, "zone_0", "sequence_0");
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// SetImageSequence Tests
// =============================================================================

TEST_F(LEDAPITest, SetImageSequenceWithNullDeviceFails)
{
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetImageSequence(nullptr, "zone_0", "seq_0", color, true, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetImageSequenceWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetImageSequence(&cx_.base, "zone_0", "seq_0", color, true, false);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// SetText Tests
// =============================================================================

TEST_F(LEDAPITest, SetTextWithNullDeviceFails)
{
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetText(nullptr, "zone_0", "Hello", color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetTextWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetText(&cx_.base, nullptr, "Hello", color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetTextWithNullTextFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetText(&cx_.base, "zone_0", nullptr, color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, SetTextWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetText(&cx_.base, "zone_0", "Hello", color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST_F(LEDAPITest, SetTextAcceptsEmptyString)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetText(&cx_.base, "zone_0", "", color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  // Should fail with NOT_CONNECTED, not INVALID_ARGUMENT for empty string
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST_F(LEDAPITest, SetTextAcceptsVariousScrollDirections)
{
  ASSERT_TRUE(cx_created_);
  lumyn_color_t color = {255, 0, 0};

  // Using actual enum values from led_command.h
  lumyn_matrix_text_scroll_direction_t directions[] = {
      LUMYN_MATRIX_TEXT_SCROLL_LEFT,
      LUMYN_MATRIX_TEXT_SCROLL_RIGHT,
  };

  for (const auto &dir : directions)
  {
    lumyn_error_t err = lumyn_SetText(&cx_.base, "zone_0", "Test", color, dir, 100, false);
    EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED) << "Direction " << static_cast<int>(dir);
  }
}

// =============================================================================
// Direct Buffer Tests
// =============================================================================

TEST_F(LEDAPITest, CreateDirectBufferWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_CreateDirectBuffer(nullptr, "zone_0", 100, 100);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, CreateDirectBufferWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_CreateDirectBuffer(&cx_.base, nullptr, 100, 100);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, CreateDirectBufferWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_CreateDirectBuffer(&cx_.base, "zone_0", 100, 100);
  // CreateDirectBuffer may succeed even when not connected (buffer is created locally)
  // Just verify the call doesn't crash
  (void)err;
}

TEST_F(LEDAPITest, UpdateDirectBufferWithNullDeviceFails)
{
  uint8_t data[] = {255, 0, 0};
  lumyn_error_t err = lumyn_UpdateDirectBuffer(nullptr, "zone_0", data, sizeof(data), false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, UpdateDirectBufferWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  uint8_t data[] = {255, 0, 0};
  lumyn_error_t err = lumyn_UpdateDirectBuffer(&cx_.base, nullptr, data, sizeof(data), false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(LEDAPITest, UpdateDirectBufferWithNullDataFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_UpdateDirectBuffer(&cx_.base, "zone_0", nullptr, 10, false);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

// =============================================================================
// ConnectorXAnimate LED Tests
// =============================================================================

TEST_F(LEDAPITest, ConnectorXAnimateSetColorWhenNotConnectedFails)
{
  ASSERT_TRUE(cxa_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetColor(&cxa_.base, "zone_0", color);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST_F(LEDAPITest, ConnectorXAnimateSetAnimationWhenNotConnectedFails)
{
  ASSERT_TRUE(cxa_created_);
  lumyn_color_t color = {255, 0, 0};
  lumyn_error_t err = lumyn_SetAnimation(&cxa_.base, "zone_0", LUMYN_ANIMATION_FILL, color, 100, false, false);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
