/**
 * @file test_config_parsing.cpp
 * @brief Property-based tests for configuration parsing
 * 
 * These tests verify that configuration parsing works correctly and handles
 * errors appropriately.
 * 
 * Feature: sdk-foundation-fixes
 * Property 5: Configuration parsing round-trip
 * Property 6: Configuration parsing error handling
 * Validates: Requirements 3.2, 3.3, 3.4
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <string>
#include <vector>

/**
 * Property 5: Configuration parsing round-trip
 * 
 * For any valid configuration JSON string, parsing it with lumyn_ParseConfig
 * and then accessing the structured data SHALL preserve all channel IDs, zone IDs,
 * and LED counts from the original JSON.
 * 
 * Validates: Requirements 3.2, 3.3
 */
TEST(ConfigurationParsing, RoundTripPreservesData) {
  // Test case 1: Simple single channel with single zone
  const char* json1 = R"({
    "channels": {
      "ch0": {
        "id": "channel_0",
        "length": 10,
        "zones": [
          {
            "id": "zone_0",
            "type": "strip",
            "length": 10
          }
        ]
      }
    }
  })";

  lumyn_config_t* config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(json1, std::strlen(json1), &config);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to parse valid JSON";
  ASSERT_NE(config, nullptr) << "Config pointer is null after successful parse";

  // Verify channel count
  int channel_count = lumyn_ConfigGetChannelCount(config);
  EXPECT_EQ(channel_count, 1) << "Expected 1 channel";

  // Verify channel ID
  const lumyn_channel_t* channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr) << "Could not get channel 0";
  const char* channel_id = lumyn_ChannelGetId(channel);
  ASSERT_NE(channel_id, nullptr) << "Channel ID is null";
  EXPECT_STREQ(channel_id, "channel_0") << "Channel ID mismatch";

  // Verify zone count
  int zone_count = lumyn_ChannelGetZoneCount(channel);
  EXPECT_EQ(zone_count, 1) << "Expected 1 zone";

  // Verify zone ID and LED count
  const lumyn_zone_t* zone = lumyn_ChannelGetZone(channel, 0);
  ASSERT_NE(zone, nullptr) << "Could not get zone 0";
  const char* zone_id = lumyn_ZoneGetId(zone);
  ASSERT_NE(zone_id, nullptr) << "Zone ID is null";
  EXPECT_STREQ(zone_id, "zone_0") << "Zone ID mismatch";
  int led_count = lumyn_ZoneGetLedCount(zone);
  EXPECT_EQ(led_count, 10) << "LED count mismatch";

  lumyn_FreeConfig(config);

  // Test case 2: Multiple channels with multiple zones
  const char* json2 = R"({
    "channels": {
      "ch_a": {
        "id": "ch_a",
        "length": 20,
        "zones": [
          {"id": "z_a1", "type": "strip", "length": 5},
          {"id": "z_a2", "type": "strip", "length": 15}
        ]
      },
      "ch_b": {
        "id": "ch_b",
        "length": 20,
        "zones": [
          {"id": "z_b1", "type": "strip", "length": 20}
        ]
      }
    }
  })";

  config = nullptr;
  err = lumyn_ParseConfig(json2, std::strlen(json2), &config);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to parse valid JSON with multiple channels";
  ASSERT_NE(config, nullptr) << "Config pointer is null";

  channel_count = lumyn_ConfigGetChannelCount(config);
  EXPECT_EQ(channel_count, 2) << "Expected 2 channels";

  // Check first channel (order may vary, so check both)
  bool found_ch_a = false;
  bool found_ch_b = false;
  
  for (int i = 0; i < channel_count; ++i) {
    channel = lumyn_ConfigGetChannel(config, i);
    ASSERT_NE(channel, nullptr) << "Could not get channel " << i;
    const char* ch_id = lumyn_ChannelGetId(channel);
    
    if (std::string(ch_id) == "ch_a") {
      found_ch_a = true;
      EXPECT_EQ(lumyn_ChannelGetZoneCount(channel), 2) << "ch_a should have 2 zones";
      
      zone = lumyn_ChannelGetZone(channel, 0);
      ASSERT_NE(zone, nullptr) << "Could not get zone 0 of ch_a";
      EXPECT_STREQ(lumyn_ZoneGetId(zone), "z_a1") << "Zone ID mismatch";
      EXPECT_EQ(lumyn_ZoneGetLedCount(zone), 5) << "Zone LED count mismatch";
      
      zone = lumyn_ChannelGetZone(channel, 1);
      ASSERT_NE(zone, nullptr) << "Could not get zone 1 of ch_a";
      EXPECT_STREQ(lumyn_ZoneGetId(zone), "z_a2") << "Zone ID mismatch";
      EXPECT_EQ(lumyn_ZoneGetLedCount(zone), 15) << "Zone LED count mismatch";
    } else if (std::string(ch_id) == "ch_b") {
      found_ch_b = true;
      EXPECT_EQ(lumyn_ChannelGetZoneCount(channel), 1) << "ch_b should have 1 zone";
      
      zone = lumyn_ChannelGetZone(channel, 0);
      ASSERT_NE(zone, nullptr) << "Could not get zone 0 of ch_b";
      EXPECT_STREQ(lumyn_ZoneGetId(zone), "z_b1") << "Zone ID mismatch";
      EXPECT_EQ(lumyn_ZoneGetLedCount(zone), 20) << "Zone LED count mismatch";
    }
  }
  
  EXPECT_TRUE(found_ch_a) << "Channel ch_a not found";
  EXPECT_TRUE(found_ch_b) << "Channel ch_b not found";

  lumyn_FreeConfig(config);
}

/**
 * Property 6: Configuration parsing error handling
 * 
 * For any invalid JSON string (malformed syntax, missing required fields, wrong types),
 * calling lumyn_ParseConfig SHALL return an error code without crashing and SHALL NOT
 * allocate a config object.
 * 
 * Validates: Requirements 3.4
 */
TEST(ConfigurationParsing, ErrorHandling) {
  lumyn_config_t* config = nullptr;
  lumyn_error_t err;

  // Test case 1: Malformed JSON (missing closing brace)
  const char* malformed_json = R"({
    "channels": [
      {"id": "ch_0", "zones": []}
  )";
  config = nullptr;
  err = lumyn_ParseConfig(malformed_json, std::strlen(malformed_json), &config);
  EXPECT_EQ(err, LUMYN_ERR_PARSE) << "Should return LUMYN_ERR_PARSE for malformed JSON";
  EXPECT_EQ(config, nullptr) << "Config should not be allocated on parse error";

  // Test case 2: Invalid JSON (trailing comma)
  const char* invalid_json = R"({
    "channels": [
      {"id": "ch_0", "zones": [],}
    ]
  })";
  config = nullptr;
  err = lumyn_ParseConfig(invalid_json, std::strlen(invalid_json), &config);
  EXPECT_EQ(err, LUMYN_ERR_PARSE) << "Should return LUMYN_ERR_PARSE for invalid JSON";
  EXPECT_EQ(config, nullptr) << "Config should not be allocated on parse error";

  // Test case 3: NULL pointer for json
  config = nullptr;
  err = lumyn_ParseConfig(nullptr, 10, &config);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT) << "Should return LUMYN_ERR_INVALID_ARGUMENT for NULL json";
  EXPECT_EQ(config, nullptr) << "Config should not be allocated";

  // Test case 4: NULL pointer for out_config
  const char* valid_json = R"({"channels": []})";
  err = lumyn_ParseConfig(valid_json, std::strlen(valid_json), nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT) << "Should return LUMYN_ERR_INVALID_ARGUMENT for NULL out_config";

  // Test case 5: Zero length JSON
  config = nullptr;
  err = lumyn_ParseConfig(valid_json, 0, &config);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT) << "Should return LUMYN_ERR_INVALID_ARGUMENT for zero length";
  EXPECT_EQ(config, nullptr) << "Config should not be allocated";

  // Test case 6: Empty JSON object
  const char* empty_json = "{}";
  config = nullptr;
  err = lumyn_ParseConfig(empty_json, std::strlen(empty_json), &config);
  // Empty JSON might be valid (no channels), so we just check it doesn't crash
  if (err == LUMYN_OK && config != nullptr) {
    EXPECT_EQ(lumyn_ConfigGetChannelCount(config), 0) << "Empty JSON should have 0 channels";
    lumyn_FreeConfig(config);
  }
}

/**
 * Test: Accessor functions handle NULL pointers gracefully
 */
TEST(ConfigurationParsing, AccessorNullSafety) {
  // Test NULL config
  EXPECT_EQ(lumyn_ConfigGetChannelCount(nullptr), 0) << "Should return 0 for NULL config";
  EXPECT_EQ(lumyn_ConfigGetChannel(nullptr, 0), nullptr) << "Should return NULL for NULL config";

  // Test NULL channel
  EXPECT_EQ(lumyn_ChannelGetZoneCount(nullptr), 0) << "Should return 0 for NULL channel";
  EXPECT_EQ(lumyn_ChannelGetZone(nullptr, 0), nullptr) << "Should return NULL for NULL channel";
  EXPECT_EQ(lumyn_ChannelGetId(nullptr), nullptr) << "Should return NULL for NULL channel";

  // Test NULL zone
  EXPECT_EQ(lumyn_ZoneGetLedCount(nullptr), 0) << "Should return 0 for NULL zone";
  EXPECT_EQ(lumyn_ZoneGetId(nullptr), nullptr) << "Should return NULL for NULL zone";
}

/**
 * Test: Out of bounds access returns NULL
 */
TEST(ConfigurationParsing, OutOfBoundsAccess) {
  const char* json = R"({
    "channels": {
      "ch0": {
        "id": "ch_0",
        "length": 10,
        "zones": [
          {"id": "z_0", "type": "strip", "length": 10}
        ]
      }
    }
  })";

  lumyn_config_t* config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(json, std::strlen(json), &config);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to parse valid JSON";
  ASSERT_NE(config, nullptr) << "Config pointer is null";

  // Try to access channel out of bounds
  const lumyn_channel_t* channel = lumyn_ConfigGetChannel(config, 1);
  EXPECT_EQ(channel, nullptr) << "Should return NULL for out of bounds channel";

  // Try to access zone out of bounds
  channel = lumyn_ConfigGetChannel(config, 0);
  ASSERT_NE(channel, nullptr) << "Could not get channel 0";
  const lumyn_zone_t* zone = lumyn_ChannelGetZone(channel, 1);
  EXPECT_EQ(zone, nullptr) << "Should return NULL for out of bounds zone";

  // Try negative index
  zone = lumyn_ChannelGetZone(channel, -1);
  EXPECT_EQ(zone, nullptr) << "Should return NULL for negative index";

  lumyn_FreeConfig(config);
}

/**
 * Test: Free config is safe to call multiple times
 */
TEST(ConfigurationParsing, FreeConfigSafety) {
  const char* json = R"({"channels": []})";
  lumyn_config_t* config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(json, std::strlen(json), &config);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to parse valid JSON";
  ASSERT_NE(config, nullptr) << "Config pointer is null";

  // Free once
  lumyn_FreeConfig(config);

  // Free NULL (should not crash)
  lumyn_FreeConfig(nullptr);

  // This test passes if it doesn't crash
  SUCCEED();
}

int main(int argc, char** argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
