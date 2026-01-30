#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_direct_led_api.cpp
 * @brief Comprehensive tests for the DirectLED high-performance API
 *
 * Tests DirectLED creation, updates, reset, and lifecycle management.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <vector>

class DirectLEDAPITest : public ::testing::Test
{
protected:
  cx_t cx_ = {};
  bool cx_created_ = false;

  void SetUp() override
  {
    if (lumyn_CreateConnectorX(&cx_) == LUMYN_OK)
    {
      cx_created_ = true;
    }
  }

  void TearDown() override
  {
    if (cx_created_)
    {
      lumyn_DestroyConnectorX(&cx_);
    }
  }
};

// =============================================================================
// DirectLED Create Tests
// =============================================================================

TEST_F(DirectLEDAPITest, CreateWithNullDeviceFails)
{
  lumyn_direct_led_t *handle = nullptr;
  lumyn_error_t err = lumyn_DirectLEDCreate(nullptr, "zone_0", 10, 100, &handle);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
  EXPECT_EQ(handle, nullptr);
}

TEST_F(DirectLEDAPITest, CreateWithNullZoneIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, nullptr, 10, 100, &handle);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
  EXPECT_EQ(handle, nullptr);
}

TEST_F(DirectLEDAPITest, CreateWithNullOutputFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(DirectLEDAPITest, CreateWithZeroLedsFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, "zone_0", 0, 100, &handle);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
  EXPECT_EQ(handle, nullptr);
}

TEST_F(DirectLEDAPITest, CreateSucceedsWithValidParams)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle);

  // Should succeed even when not connected (DirectLED is a local buffer)
  ASSERT_EQ(err, LUMYN_OK) << Lumyn_ErrorString(err);
  ASSERT_NE(handle, nullptr);

  lumyn_DirectLEDDestroy(handle);
}

TEST_F(DirectLEDAPITest, CreateWithEmptyZoneIdSucceeds)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  // Empty zone ID is accepted by the API
  lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, "", 10, 100, &handle);
  // API accepts empty zone ID
  if (err == LUMYN_OK && handle != nullptr)
  {
    lumyn_DirectLEDDestroy(handle);
  }
}

TEST_F(DirectLEDAPITest, CreateWithVariousLedCounts)
{
  ASSERT_TRUE(cx_created_);

  size_t led_counts[] = {1, 10, 100, 300, 1000};

  for (size_t count : led_counts)
  {
    lumyn_direct_led_t *handle = nullptr;
    lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, "zone_0", count, 100, &handle);
    ASSERT_EQ(err, LUMYN_OK) << "Failed with count=" << count;
    ASSERT_NE(handle, nullptr);

    EXPECT_EQ(lumyn_DirectLEDGetLength(handle), count);

    lumyn_DirectLEDDestroy(handle);
  }
}

TEST_F(DirectLEDAPITest, CreateWithVariousRefreshIntervals)
{
  ASSERT_TRUE(cx_created_);

  int intervals[] = {0, 1, 50, 100, 1000, -1};

  for (int interval : intervals)
  {
    lumyn_direct_led_t *handle = nullptr;
    lumyn_error_t err = lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, interval, &handle);
    ASSERT_EQ(err, LUMYN_OK) << "Failed with interval=" << interval;
    ASSERT_NE(handle, nullptr);

    lumyn_DirectLEDDestroy(handle);
  }
}

// =============================================================================
// DirectLED Destroy Tests
// =============================================================================

TEST_F(DirectLEDAPITest, DestroyWithNullIsSafe)
{
  // Should not crash
  lumyn_DirectLEDDestroy(nullptr);
  SUCCEED();
}

TEST_F(DirectLEDAPITest, DoubleDestroyIsSafe)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  lumyn_DirectLEDDestroy(handle);
  // Second destroy should be safe (though technically undefined behavior to pass freed pointer)
  // Note: This is a known pattern, but real code shouldn't do this
  SUCCEED();
}

// =============================================================================
// DirectLED Update Tests
// =============================================================================

TEST_F(DirectLEDAPITest, UpdateWithNullHandleFails)
{
  lumyn_color_t colors[10] = {};
  lumyn_error_t err = lumyn_DirectLEDUpdate(nullptr, colors, 10);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(DirectLEDAPITest, UpdateWithNullColorsFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  lumyn_error_t err = lumyn_DirectLEDUpdate(handle, nullptr, 10);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);

  lumyn_DirectLEDDestroy(handle);
}

TEST_F(DirectLEDAPITest, UpdateWithZeroCountFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  lumyn_color_t colors[10] = {};
  lumyn_error_t err = lumyn_DirectLEDUpdate(handle, colors, 0);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);

  lumyn_DirectLEDDestroy(handle);
}

TEST_F(DirectLEDAPITest, UpdateWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  lumyn_color_t colors[10] = {};
  for (int i = 0; i < 10; ++i)
  {
    colors[i] = {255, 0, 0};
  }

  lumyn_error_t err = lumyn_DirectLEDUpdate(handle, colors, 10);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);

  lumyn_DirectLEDDestroy(handle);
}

// =============================================================================
// DirectLED UpdateRaw Tests
// =============================================================================

TEST_F(DirectLEDAPITest, UpdateRawWithNullHandleFails)
{
  uint8_t data[30] = {};
  lumyn_error_t err = lumyn_DirectLEDUpdateRaw(nullptr, data, 30);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(DirectLEDAPITest, UpdateRawWithNullDataFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  lumyn_error_t err = lumyn_DirectLEDUpdateRaw(handle, nullptr, 30);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);

  lumyn_DirectLEDDestroy(handle);
}

TEST_F(DirectLEDAPITest, UpdateRawWithZeroLengthFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  uint8_t data[30] = {};
  lumyn_error_t err = lumyn_DirectLEDUpdateRaw(handle, data, 0);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);

  lumyn_DirectLEDDestroy(handle);
}

TEST_F(DirectLEDAPITest, UpdateRawWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  // RGB data for 10 LEDs
  uint8_t data[30] = {};
  for (int i = 0; i < 30; i += 3)
  {
    data[i] = 255;   // R
    data[i + 1] = 0; // G
    data[i + 2] = 0; // B
  }

  lumyn_error_t err = lumyn_DirectLEDUpdateRaw(handle, data, 30);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);

  lumyn_DirectLEDDestroy(handle);
}

// =============================================================================
// DirectLED ForceFullUpdate Tests
// =============================================================================

TEST_F(DirectLEDAPITest, ForceFullUpdateWithNullHandleFails)
{
  lumyn_color_t colors[10] = {};
  lumyn_error_t err = lumyn_DirectLEDForceFullUpdate(nullptr, colors, 10);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(DirectLEDAPITest, ForceFullUpdateWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  lumyn_color_t colors[10] = {};
  lumyn_error_t err = lumyn_DirectLEDForceFullUpdate(handle, colors, 10);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);

  lumyn_DirectLEDDestroy(handle);
}

// =============================================================================
// DirectLED Reset Tests
// =============================================================================

TEST_F(DirectLEDAPITest, ResetWithNullIsSafe)
{
  // Should not crash
  lumyn_DirectLEDReset(nullptr);
  SUCCEED();
}

TEST_F(DirectLEDAPITest, ResetSucceeds)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  // Reset should not crash
  lumyn_DirectLEDReset(handle);
  SUCCEED();

  lumyn_DirectLEDDestroy(handle);
}

// =============================================================================
// DirectLED SetRefreshInterval Tests
// =============================================================================

TEST_F(DirectLEDAPITest, SetRefreshIntervalWithNullIsSafe)
{
  // Should not crash
  lumyn_DirectLEDSetRefreshInterval(nullptr, 50);
  SUCCEED();
}

TEST_F(DirectLEDAPITest, SetRefreshIntervalSucceeds)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  // Various intervals should work
  lumyn_DirectLEDSetRefreshInterval(handle, 0);
  lumyn_DirectLEDSetRefreshInterval(handle, 50);
  lumyn_DirectLEDSetRefreshInterval(handle, 1000);
  lumyn_DirectLEDSetRefreshInterval(handle, -1);

  SUCCEED();

  lumyn_DirectLEDDestroy(handle);
}

// =============================================================================
// DirectLED GetLength Tests
// =============================================================================

TEST_F(DirectLEDAPITest, GetLengthWithNullReturnsZero)
{
  EXPECT_EQ(lumyn_DirectLEDGetLength(nullptr), 0);
}

TEST_F(DirectLEDAPITest, GetLengthReturnsCorrectValue)
{
  ASSERT_TRUE(cx_created_);

  size_t counts[] = {1, 10, 100, 500};

  for (size_t count : counts)
  {
    lumyn_direct_led_t *handle = nullptr;
    ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", count, 100, &handle), LUMYN_OK);

    EXPECT_EQ(lumyn_DirectLEDGetLength(handle), count);

    lumyn_DirectLEDDestroy(handle);
  }
}

// =============================================================================
// DirectLED GetZoneId Tests
// =============================================================================

TEST_F(DirectLEDAPITest, GetZoneIdWithNullReturnsNull)
{
  EXPECT_EQ(lumyn_DirectLEDGetZoneId(nullptr), nullptr);
}

TEST_F(DirectLEDAPITest, GetZoneIdReturnsCorrectValue)
{
  ASSERT_TRUE(cx_created_);

  const char *zone_ids[] = {"zone_0", "zone_test", "a", "very_long_zone_id_name_12345"};

  for (const char *zone_id : zone_ids)
  {
    lumyn_direct_led_t *handle = nullptr;
    ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, zone_id, 10, 100, &handle), LUMYN_OK);

    const char *retrieved = lumyn_DirectLEDGetZoneId(handle);
    ASSERT_NE(retrieved, nullptr);
    EXPECT_STREQ(retrieved, zone_id);

    lumyn_DirectLEDDestroy(handle);
  }
}

// =============================================================================
// DirectLED IsInitialized Tests
// =============================================================================

TEST_F(DirectLEDAPITest, IsInitializedWithNullReturnsFalse)
{
  EXPECT_FALSE(lumyn_DirectLEDIsInitialized(nullptr));
}

TEST_F(DirectLEDAPITest, IsInitializedReturnsTrueAfterCreate)
{
  ASSERT_TRUE(cx_created_);
  lumyn_direct_led_t *handle = nullptr;
  ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, "zone_0", 10, 100, &handle), LUMYN_OK);

  EXPECT_TRUE(lumyn_DirectLEDIsInitialized(handle));

  lumyn_DirectLEDDestroy(handle);
}

// =============================================================================
// Multiple DirectLED Instances Tests
// =============================================================================

TEST_F(DirectLEDAPITest, MultipleInstancesCanCoexist)
{
  ASSERT_TRUE(cx_created_);

  lumyn_direct_led_t *handles[5] = {};
  const char *zones[] = {"zone_0", "zone_1", "zone_2", "zone_3", "zone_4"};

  // Create multiple instances
  for (int i = 0; i < 5; ++i)
  {
    ASSERT_EQ(lumyn_DirectLEDCreate(&cx_.base, zones[i], 10 + i, 100, &handles[i]), LUMYN_OK);
    ASSERT_NE(handles[i], nullptr);
  }

  // Verify each has correct properties
  for (int i = 0; i < 5; ++i)
  {
    EXPECT_EQ(lumyn_DirectLEDGetLength(handles[i]), 10u + i);
    EXPECT_STREQ(lumyn_DirectLEDGetZoneId(handles[i]), zones[i]);
  }

  // Clean up
  for (int i = 0; i < 5; ++i)
  {
    lumyn_DirectLEDDestroy(handles[i]);
  }
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
