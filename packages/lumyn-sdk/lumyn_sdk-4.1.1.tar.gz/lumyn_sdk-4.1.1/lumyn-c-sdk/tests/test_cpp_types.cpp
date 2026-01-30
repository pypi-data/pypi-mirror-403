/**
 * @file test_cpp_types.cpp
 * @brief Tests for C++ SDK type wrappers and aliases
 *
 * Tests lumyn::Event, lumyn::ConnectionStatus, and type aliases.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/types.hpp>
#include <lumyn/c/lumyn_common.h>

// =============================================================================
// ConnectionStatus Tests
// =============================================================================

TEST(ConnectionStatusTest, DefaultConstruction)
{
  lumyn::ConnectionStatus status;
  EXPECT_FALSE(status.connected);
  EXPECT_FALSE(status.enabled);
}

TEST(ConnectionStatusTest, SetConnected)
{
  lumyn::ConnectionStatus status;
  status.connected = true;
  EXPECT_TRUE(status.connected);
  EXPECT_FALSE(status.enabled);
}

TEST(ConnectionStatusTest, SetEnabled)
{
  lumyn::ConnectionStatus status;
  status.enabled = true;
  EXPECT_FALSE(status.connected);
  EXPECT_TRUE(status.enabled);
}

TEST(ConnectionStatusTest, SetBoth)
{
  lumyn::ConnectionStatus status;
  status.connected = true;
  status.enabled = true;
  EXPECT_TRUE(status.connected);
  EXPECT_TRUE(status.enabled);
}

// =============================================================================
// Error Code Tests
// =============================================================================

TEST(ErrorCodeTest, OK)
{
  lumyn_error_t err = LUMYN_OK;
  EXPECT_EQ(err, LUMYN_OK);
}

TEST(ErrorCodeTest, InvalidArgument)
{
  lumyn_error_t err = LUMYN_ERR_INVALID_ARGUMENT;
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST(ErrorCodeTest, NotConnected)
{
  lumyn_error_t err = LUMYN_ERR_NOT_CONNECTED;
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST(ErrorCodeTest, Timeout)
{
  lumyn_error_t err = LUMYN_ERR_TIMEOUT;
  EXPECT_EQ(err, LUMYN_ERR_TIMEOUT);
}

// =============================================================================
// Device Status Tests
// =============================================================================

TEST(StatusAliasTest, Unknown)
{
  lumyn::Status status = LUMYN_STATUS_UNKNOWN;
  EXPECT_EQ(status, LUMYN_STATUS_UNKNOWN);
}

TEST(StatusAliasTest, Booting)
{
  lumyn::Status status = LUMYN_STATUS_BOOTING;
  EXPECT_EQ(status, LUMYN_STATUS_BOOTING);
}

TEST(StatusAliasTest, Active)
{
  lumyn::Status status = LUMYN_STATUS_ACTIVE;
  EXPECT_EQ(status, LUMYN_STATUS_ACTIVE);
}

TEST(StatusAliasTest, Error)
{
  lumyn::Status status = LUMYN_STATUS_ERROR;
  EXPECT_EQ(status, LUMYN_STATUS_ERROR);
}

// =============================================================================
// EventType Alias Tests
// =============================================================================

TEST(EventTypeAliasTest, Heartbeat)
{
  lumyn::EventType type = LUMYN_EVENT_HEARTBEAT;
  EXPECT_EQ(type, LUMYN_EVENT_HEARTBEAT);
}

TEST(EventTypeAliasTest, Connected)
{
  lumyn::EventType type = LUMYN_EVENT_CONNECTED;
  EXPECT_EQ(type, LUMYN_EVENT_CONNECTED);
}

TEST(EventTypeAliasTest, Disconnected)
{
  lumyn::EventType type = LUMYN_EVENT_DISCONNECTED;
  EXPECT_EQ(type, LUMYN_EVENT_DISCONNECTED);
}

TEST(EventTypeAliasTest, Error)
{
  lumyn::EventType type = LUMYN_EVENT_ERROR;
  EXPECT_EQ(type, LUMYN_EVENT_ERROR);
}

TEST(EventTypeAliasTest, Enabled)
{
  lumyn::EventType type = LUMYN_EVENT_ENABLED;
  EXPECT_EQ(type, LUMYN_EVENT_ENABLED);
}

TEST(EventTypeAliasTest, Disabled)
{
  lumyn::EventType type = LUMYN_EVENT_DISABLED;
  EXPECT_EQ(type, LUMYN_EVENT_DISABLED);
}

// =============================================================================
// Animation Type Alias Tests
// =============================================================================

TEST(AnimationAliasTest, None)
{
  lumyn::Animation anim = LUMYN_ANIMATION_NONE;
  EXPECT_EQ(anim, LUMYN_ANIMATION_NONE);
}

TEST(AnimationAliasTest, Fill)
{
  lumyn::Animation anim = LUMYN_ANIMATION_FILL;
  EXPECT_EQ(anim, LUMYN_ANIMATION_FILL);
}

TEST(AnimationAliasTest, RainbowRoll)
{
  lumyn::Animation anim = LUMYN_ANIMATION_RAINBOW_ROLL;
  EXPECT_EQ(anim, LUMYN_ANIMATION_RAINBOW_ROLL);
}

TEST(AnimationAliasTest, Chase)
{
  lumyn::Animation anim = LUMYN_ANIMATION_CHASE;
  EXPECT_EQ(anim, LUMYN_ANIMATION_CHASE);
}

// =============================================================================
// MatrixText Type Alias Tests
// =============================================================================

TEST(MatrixTextFontAliasTest, Builtin)
{
  lumyn::MatrixTextFont font = LUMYN_MATRIX_TEXT_FONT_BUILTIN;
  EXPECT_EQ(font, LUMYN_MATRIX_TEXT_FONT_BUILTIN);
}

TEST(MatrixTextAlignAliasTest, Left)
{
  lumyn::MatrixTextAlign align = LUMYN_MATRIX_TEXT_ALIGN_LEFT;
  EXPECT_EQ(align, LUMYN_MATRIX_TEXT_ALIGN_LEFT);
}

TEST(MatrixTextAlignAliasTest, Center)
{
  lumyn::MatrixTextAlign align = LUMYN_MATRIX_TEXT_ALIGN_CENTER;
  EXPECT_EQ(align, LUMYN_MATRIX_TEXT_ALIGN_CENTER);
}

TEST(MatrixTextAlignAliasTest, Right)
{
  lumyn::MatrixTextAlign align = LUMYN_MATRIX_TEXT_ALIGN_RIGHT;
  EXPECT_EQ(align, LUMYN_MATRIX_TEXT_ALIGN_RIGHT);
}

TEST(MatrixTextScrollDirectionAliasTest, Left)
{
  lumyn::MatrixTextScrollDirection dir = LUMYN_MATRIX_TEXT_SCROLL_LEFT;
  EXPECT_EQ(dir, LUMYN_MATRIX_TEXT_SCROLL_LEFT);
}

TEST(MatrixTextScrollDirectionAliasTest, Right)
{
  lumyn::MatrixTextScrollDirection dir = LUMYN_MATRIX_TEXT_SCROLL_RIGHT;
  EXPECT_EQ(dir, LUMYN_MATRIX_TEXT_SCROLL_RIGHT);
}

// =============================================================================
// Color Tests
// =============================================================================

TEST(ColorTest, CreateRGB)
{
  lumyn_color_t color{255, 128, 64};
  EXPECT_EQ(color.r, 255);
  EXPECT_EQ(color.g, 128);
  EXPECT_EQ(color.b, 64);
}

TEST(ColorTest, CreateBlack)
{
  lumyn_color_t color{0, 0, 0};
  EXPECT_EQ(color.r, 0);
  EXPECT_EQ(color.g, 0);
  EXPECT_EQ(color.b, 0);
}

TEST(ColorTest, CreateWhite)
{
  lumyn_color_t color{255, 255, 255};
  EXPECT_EQ(color.r, 255);
  EXPECT_EQ(color.g, 255);
  EXPECT_EQ(color.b, 255);
}

TEST(ColorTest, CreateRed)
{
  lumyn_color_t color{255, 0, 0};
  EXPECT_EQ(color.r, 255);
  EXPECT_EQ(color.g, 0);
  EXPECT_EQ(color.b, 0);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
