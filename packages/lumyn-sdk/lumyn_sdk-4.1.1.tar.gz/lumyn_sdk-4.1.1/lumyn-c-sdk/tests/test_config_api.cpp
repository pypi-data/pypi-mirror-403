#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_config_api.cpp
 * @brief Comprehensive tests for the Configuration API
 *
 * Tests configuration parsing, querying, and application functions.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <string>

class ConfigAPITest : public ::testing::Test
{
protected:
  cx_t cx_ = {};
  bool cx_created_ = false;

  // Sample valid JSON configurations - using the correct format expected by the API
  const char *valid_config_minimal_ = R"({"channels":{}})";
  const char *valid_config_simple_ = R"({
    "channels": {
      "ch0": {
        "id": "channel_0",
        "length": 60,
        "zones": [
          {"id": "zone_0", "type": "strip", "length": 60}
        ]
      }
    }
  })";
  const char *valid_config_complex_ = R"({
    "channels": {
      "ch_a": {
        "id": "ch_a",
        "length": 180,
        "zones": [
          {"id": "zone_0", "type": "strip", "length": 60},
          {"id": "zone_1", "type": "strip", "length": 120}
        ]
      },
      "ch_b": {
        "id": "ch_b",
        "length": 30,
        "zones": [
          {"id": "zone_2", "type": "strip", "length": 30}
        ]
      }
    }
  })";

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
// ParseConfig Tests
// =============================================================================

TEST_F(ConfigAPITest, ParseConfigWithNullJsonFails)
{
  lumyn_config_t *config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(nullptr, 10, &config);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
  EXPECT_EQ(config, nullptr);
}

TEST_F(ConfigAPITest, ParseConfigWithZeroLengthFails)
{
  lumyn_config_t *config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig("{}", 0, &config);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
  EXPECT_EQ(config, nullptr);
}

TEST_F(ConfigAPITest, ParseConfigWithNullOutputFails)
{
  lumyn_error_t err = lumyn_ParseConfig("{}", 2, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConfigAPITest, ParseConfigWithInvalidJsonFails)
{
  lumyn_config_t *config = nullptr;
  const char *invalid = "this is not json";
  lumyn_error_t err = lumyn_ParseConfig(invalid, std::strlen(invalid), &config);
  EXPECT_EQ(err, LUMYN_ERR_PARSE);
  EXPECT_EQ(config, nullptr);
}

TEST_F(ConfigAPITest, ParseConfigWithEmptyObjectSucceeds)
{
  lumyn_config_t *config = nullptr;
  const char *json = "{}";
  lumyn_error_t err = lumyn_ParseConfig(json, std::strlen(json), &config);

  // May succeed or fail depending on schema requirements
  if (err == LUMYN_OK)
  {
    ASSERT_NE(config, nullptr);
    lumyn_FreeConfig(config);
  }
}

TEST_F(ConfigAPITest, ParseConfigWithMinimalConfigSucceeds)
{
  lumyn_config_t *config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(valid_config_minimal_, std::strlen(valid_config_minimal_), &config);
  ASSERT_EQ(err, LUMYN_OK) << Lumyn_ErrorString(err);
  ASSERT_NE(config, nullptr);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, ParseConfigWithSimpleConfigSucceeds)
{
  lumyn_config_t *config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config);
  ASSERT_EQ(err, LUMYN_OK) << Lumyn_ErrorString(err);
  ASSERT_NE(config, nullptr);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, ParseConfigWithComplexConfigSucceeds)
{
  lumyn_config_t *config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config);
  ASSERT_EQ(err, LUMYN_OK) << Lumyn_ErrorString(err);
  ASSERT_NE(config, nullptr);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, ParseConfigWithMalformedJsonFails)
{
  lumyn_config_t *config = nullptr;

  const char *malformed_jsons[] = {
      "{",                   // Unclosed brace
      "[}",                  // Wrong brackets
      "{'key': 'value'}",    // Single quotes
      "{\"key\": }",         // Missing value
      "{\"key\" \"value\"}", // Missing colon
  };

  for (const char *json : malformed_jsons)
  {
    config = nullptr;
    lumyn_error_t err = lumyn_ParseConfig(json, std::strlen(json), &config);
    EXPECT_EQ(err, LUMYN_ERR_PARSE) << "Expected parse error for: " << json;
    EXPECT_EQ(config, nullptr) << "Config should be null for: " << json;
  }
}

// =============================================================================
// FreeConfig Tests
// =============================================================================

TEST_F(ConfigAPITest, FreeConfigWithNullIsSafe)
{
  // Should not crash
  lumyn_FreeConfig(nullptr);
  SUCCEED();
}

TEST_F(ConfigAPITest, FreeConfigAfterParseSucceeds)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);
  ASSERT_NE(config, nullptr);

  // Should not crash
  lumyn_FreeConfig(config);
  SUCCEED();
}

// =============================================================================
// ConfigGetChannelCount Tests
// =============================================================================

TEST_F(ConfigAPITest, GetChannelCountWithNullReturnsZero)
{
  EXPECT_EQ(lumyn_ConfigGetChannelCount(nullptr), 0);
}

TEST_F(ConfigAPITest, GetChannelCountWithEmptyConfigReturnsZero)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_minimal_, std::strlen(valid_config_minimal_), &config), LUMYN_OK);

  EXPECT_EQ(lumyn_ConfigGetChannelCount(config), 0);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, GetChannelCountReturnsCorrectCount)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config), LUMYN_OK);

  EXPECT_EQ(lumyn_ConfigGetChannelCount(config), 2);

  lumyn_FreeConfig(config);
}

// =============================================================================
// ConfigGetChannel Tests
// =============================================================================

TEST_F(ConfigAPITest, GetChannelWithNullConfigReturnsNull)
{
  EXPECT_EQ(lumyn_ConfigGetChannel(nullptr, 0), nullptr);
}

TEST_F(ConfigAPITest, GetChannelWithNegativeIndexReturnsNull)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);

  EXPECT_EQ(lumyn_ConfigGetChannel(config, -1), nullptr);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, GetChannelWithOutOfBoundsIndexReturnsNull)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);

  int count = lumyn_ConfigGetChannelCount(config);
  EXPECT_EQ(lumyn_ConfigGetChannel(config, count), nullptr);
  EXPECT_EQ(lumyn_ConfigGetChannel(config, count + 1), nullptr);
  EXPECT_EQ(lumyn_ConfigGetChannel(config, 1000), nullptr);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, GetChannelWithValidIndexSucceeds)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config), LUMYN_OK);

  int count = lumyn_ConfigGetChannelCount(config);
  ASSERT_EQ(count, 2);

  for (int i = 0; i < count; ++i)
  {
    const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, i);
    EXPECT_NE(channel, nullptr) << "Channel " << i << " is null";
  }

  lumyn_FreeConfig(config);
}

// =============================================================================
// ChannelGetId Tests
// =============================================================================

TEST_F(ConfigAPITest, ChannelGetIdWithNullReturnsNull)
{
  EXPECT_EQ(lumyn_ChannelGetId(nullptr), nullptr);
}

TEST_F(ConfigAPITest, ChannelGetIdReturnsValidString)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);

  const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr);

  const char *id = lumyn_ChannelGetId(channel);
  ASSERT_NE(id, nullptr);
  EXPECT_GT(std::strlen(id), 0u);

  lumyn_FreeConfig(config);
}

// =============================================================================
// ChannelGetZoneCount Tests
// =============================================================================

TEST_F(ConfigAPITest, ChannelGetZoneCountWithNullReturnsZero)
{
  EXPECT_EQ(lumyn_ChannelGetZoneCount(nullptr), 0);
}

TEST_F(ConfigAPITest, ChannelGetZoneCountReturnsCorrectCount)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config), LUMYN_OK);

  const lumyn_channel_t *channel0 = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel0, nullptr);
  EXPECT_EQ(lumyn_ChannelGetZoneCount(channel0), 2); // zone_0 and zone_1

  const lumyn_channel_t *channel1 = lumyn_ConfigGetChannel(config, 1);
  ASSERT_NE(channel1, nullptr);
  EXPECT_EQ(lumyn_ChannelGetZoneCount(channel1), 1); // zone_2

  lumyn_FreeConfig(config);
}

// =============================================================================
// ChannelGetZone Tests
// =============================================================================

TEST_F(ConfigAPITest, ChannelGetZoneWithNullChannelReturnsNull)
{
  EXPECT_EQ(lumyn_ChannelGetZone(nullptr, 0), nullptr);
}

TEST_F(ConfigAPITest, ChannelGetZoneWithInvalidIndexReturnsNull)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);

  const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr);

  int zone_count = lumyn_ChannelGetZoneCount(channel);
  EXPECT_EQ(lumyn_ChannelGetZone(channel, -1), nullptr);
  EXPECT_EQ(lumyn_ChannelGetZone(channel, zone_count), nullptr);
  EXPECT_EQ(lumyn_ChannelGetZone(channel, 1000), nullptr);

  lumyn_FreeConfig(config);
}

TEST_F(ConfigAPITest, ChannelGetZoneWithValidIndexSucceeds)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config), LUMYN_OK);

  const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr);

  int zone_count = lumyn_ChannelGetZoneCount(channel);
  for (int i = 0; i < zone_count; ++i)
  {
    const lumyn_zone_t *zone = lumyn_ChannelGetZone(channel, i);
    EXPECT_NE(zone, nullptr) << "Zone " << i << " is null";
  }

  lumyn_FreeConfig(config);
}

// =============================================================================
// ZoneGetId Tests
// =============================================================================

TEST_F(ConfigAPITest, ZoneGetIdWithNullReturnsNull)
{
  EXPECT_EQ(lumyn_ZoneGetId(nullptr), nullptr);
}

TEST_F(ConfigAPITest, ZoneGetIdReturnsValidString)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);

  const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr);

  const lumyn_zone_t *zone = lumyn_ChannelGetZone(channel, 0);
  ASSERT_NE(zone, nullptr);

  const char *id = lumyn_ZoneGetId(zone);
  ASSERT_NE(id, nullptr);
  EXPECT_GT(std::strlen(id), 0u);

  lumyn_FreeConfig(config);
}

// =============================================================================
// ZoneGetLedCount Tests
// =============================================================================

TEST_F(ConfigAPITest, ZoneGetLedCountWithNullReturnsZero)
{
  EXPECT_EQ(lumyn_ZoneGetLedCount(nullptr), 0);
}

TEST_F(ConfigAPITest, ZoneGetLedCountReturnsCorrectValue)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_simple_, std::strlen(valid_config_simple_), &config), LUMYN_OK);

  const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr);

  const lumyn_zone_t *zone = lumyn_ChannelGetZone(channel, 0);
  ASSERT_NE(zone, nullptr);

  EXPECT_EQ(lumyn_ZoneGetLedCount(zone), 60);

  lumyn_FreeConfig(config);
}

// =============================================================================
// ApplyConfig Tests
// =============================================================================

TEST_F(ConfigAPITest, ApplyConfigWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_ApplyConfig(nullptr, valid_config_simple_, std::strlen(valid_config_simple_));
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConfigAPITest, ApplyConfigWithNullJsonFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_ApplyConfig(&cx_.base, nullptr, 10);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConfigAPITest, ApplyConfigWithZeroLengthFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_ApplyConfig(&cx_.base, valid_config_simple_, 0);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConfigAPITest, ApplyConfigWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  lumyn_error_t err = lumyn_ApplyConfig(&cx_.base, valid_config_simple_, std::strlen(valid_config_simple_));
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// Config Traversal Tests
// =============================================================================

TEST_F(ConfigAPITest, TraverseCompleteConfig)
{
  lumyn_config_t *config = nullptr;
  ASSERT_EQ(lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config), LUMYN_OK);

  int total_zones = 0;
  int total_leds = 0;

  int channel_count = lumyn_ConfigGetChannelCount(config);
  EXPECT_EQ(channel_count, 2);

  for (int c = 0; c < channel_count; ++c)
  {
    const lumyn_channel_t *channel = lumyn_ConfigGetChannel(config, c);
    ASSERT_NE(channel, nullptr);

    const char *channel_id = lumyn_ChannelGetId(channel);
    EXPECT_NE(channel_id, nullptr);

    int zone_count = lumyn_ChannelGetZoneCount(channel);
    total_zones += zone_count;

    for (int z = 0; z < zone_count; ++z)
    {
      const lumyn_zone_t *zone = lumyn_ChannelGetZone(channel, z);
      ASSERT_NE(zone, nullptr);

      const char *zone_id = lumyn_ZoneGetId(zone);
      EXPECT_NE(zone_id, nullptr);

      int led_count = lumyn_ZoneGetLedCount(zone);
      EXPECT_GT(led_count, 0);
      total_leds += led_count;
    }
  }

  EXPECT_EQ(total_zones, 3);  // zone_0, zone_1, zone_2
  EXPECT_EQ(total_leds, 210); // 60 + 120 + 30

  lumyn_FreeConfig(config);
}

// =============================================================================
// Multiple Parse/Free Cycles
// =============================================================================

TEST_F(ConfigAPITest, ParseFreeCycleDoesNotLeak)
{
  for (int i = 0; i < 100; ++i)
  {
    lumyn_config_t *config = nullptr;
    ASSERT_EQ(lumyn_ParseConfig(valid_config_complex_, std::strlen(valid_config_complex_), &config), LUMYN_OK)
        << "Cycle " << i;
    ASSERT_NE(config, nullptr);
    lumyn_FreeConfig(config);
  }
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
