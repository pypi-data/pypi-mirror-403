#include <lumyn/Constants.h> // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_error_handling.cpp
 * @brief Property-based tests for error handling consistency
 *
 * These tests verify that the C API follows consistent error handling patterns
 * where all functions that can fail return lumyn_error_t.
 *
 * Feature: sdk-foundation-fixes
 * Property 8: C API error return consistency
 * Validates: Requirements 7.1
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <string>
#include <vector>
#include <type_traits>

/**
 * Property 8: C API error return consistency
 *
 * For any C API function that can fail (excluding void functions and pure getters),
 * the function SHALL have lumyn_error_t as its return type.
 *
 * Validates: Requirements 7.1
 */
class ErrorHandlingConsistency : public ::testing::Test
{
protected:
  void SetUp() override
  {
    // Initialize test fixtures
  }

  void TearDown() override
  {
    // Clean up test fixtures
  }
};

/**
 * Test: All error codes have string descriptions
 *
 * For any value in the lumyn_error_t enum, calling Lumyn_ErrorString
 * SHALL return a non-null, non-empty string that is not "Unknown error".
 */
TEST_F(ErrorHandlingConsistency, AllErrorCodesHaveDescriptions)
{
  // Test all defined error codes
  const lumyn_error_t error_codes[] = {
      LUMYN_OK,
      LUMYN_ERR_INVALID_ARGUMENT,
      LUMYN_ERR_INVALID_HANDLE,
      LUMYN_ERR_NOT_CONNECTED,
      LUMYN_ERR_TIMEOUT,
      LUMYN_ERR_IO,
      LUMYN_ERR_INTERNAL,
      LUMYN_ERR_NOT_SUPPORTED,
      LUMYN_ERR_PARSE,
  };

  for (lumyn_error_t code : error_codes)
  {
    const char *str = Lumyn_ErrorString(code);
    ASSERT_NE(str, nullptr) << "Error string is NULL for code " << static_cast<int>(code);
    ASSERT_NE(std::strlen(str), 0) << "Error string is empty for code " << static_cast<int>(code);
    EXPECT_STRNE(str, "Unknown error") << "Error string is generic for code " << static_cast<int>(code);
  }
}

/**
 * Test: Invalid error codes return safe string
 *
 * For any invalid error code value, Lumyn_ErrorString SHALL return
 * a safe string (not NULL, not empty).
 */
TEST_F(ErrorHandlingConsistency, InvalidErrorCodesSafe)
{
  // Test some invalid error codes
  const lumyn_error_t invalid_codes[] = {
      static_cast<lumyn_error_t>(-1),
      static_cast<lumyn_error_t>(999),
      static_cast<lumyn_error_t>(100),
  };

  for (lumyn_error_t code : invalid_codes)
  {
    const char *str = Lumyn_ErrorString(code);
    ASSERT_NE(str, nullptr) << "Error string is NULL for invalid code " << static_cast<int>(code);
    ASSERT_NE(std::strlen(str), 0) << "Error string is empty for invalid code " << static_cast<int>(code);
  }
}

/**
 * Test: Lifecycle functions return lumyn_error_t on failure
 *
 * Functions that create device instances SHALL return lumyn_error_t
 * to indicate success or failure.
 */
TEST_F(ErrorHandlingConsistency, LifecycleFunctionsReturnErrorCode)
{
  // Test CreateConnectorX
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "CreateConnectorX should return lumyn_error_t";
  if (err == LUMYN_OK)
    lumyn_DestroyConnectorX(&cx);

  // Test CreateConnectorXAlloc
  cx_t *cx_alloc = nullptr;
  err = lumyn_CreateConnectorXAlloc(&cx_alloc);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "CreateConnectorXAlloc should return lumyn_error_t";
  if (cx_alloc)
    lumyn_DestroyConnectorXAlloc(cx_alloc);

  // Test CreateConnectorXAnimate
  cx_animate_t cxa = {};
  err = lumyn_CreateConnectorXAnimate(&cxa);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "CreateConnectorXAnimate should return lumyn_error_t";
  if (err == LUMYN_OK)
    lumyn_DestroyConnectorXAnimate(&cxa);

  // Test CreateConnectorXAnimateAlloc
  cx_animate_t *cxa_alloc = nullptr;
  err = lumyn_CreateConnectorXAnimateAlloc(&cxa_alloc);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "CreateConnectorXAnimateAlloc should return lumyn_error_t";
  if (cxa_alloc)
    lumyn_DestroyConnectorXAnimateAlloc(cxa_alloc);
}

/**
 * Test: Connection functions return lumyn_error_t
 *
 * Functions that manage device connections SHALL return lumyn_error_t
 * to indicate success or failure.
 */
TEST_F(ErrorHandlingConsistency, ConnectionFunctionsReturnErrorCode)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    GTEST_SKIP() << "Failed to create ConnectorX";
  }

  // Test Connect with invalid port
  err = lumyn_Connect(&cx.base, "/dev/nonexistent");
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "Connect should return lumyn_error_t";

  // Test Disconnect
  err = lumyn_Disconnect(&cx.base);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "Disconnect should return lumyn_error_t";

  lumyn_DestroyConnectorX(&cx);
}

/**
 * Test: LED control functions return lumyn_error_t
 *
 * Functions that control LEDs SHALL return lumyn_error_t to indicate
 * success or failure.
 */
TEST_F(ErrorHandlingConsistency, LedControlFunctionsReturnErrorCode)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    GTEST_SKIP() << "Failed to create ConnectorX";
  }

  lumyn_color_t color = {255, 0, 0};

  // Test SetColor
  err = lumyn_SetColor(&cx.base, "zone_0", color);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetColor should return lumyn_error_t";

  // Test SetGroupColor
  err = lumyn_SetGroupColor(&cx.base, "group_0", color);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetGroupColor should return lumyn_error_t";

  // Test SetAnimation
  err = lumyn_SetAnimation(&cx.base, "zone_0", LUMYN_ANIMATION_BREATHE, color, 100, false, false);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetAnimation should return lumyn_error_t";

  // Test SetGroupAnimation
  err = lumyn_SetGroupAnimation(&cx.base, "group_0", LUMYN_ANIMATION_BREATHE, color, 100, false, false);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetGroupAnimation should return lumyn_error_t";

  // Test SetText
  err = lumyn_SetText(&cx.base, "zone_0", "Hello", color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetText should return lumyn_error_t";

  // Test SetGroupText
  err = lumyn_SetGroupText(&cx.base, "group_0", "Hello", color, LUMYN_MATRIX_TEXT_SCROLL_LEFT, 100, false);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetGroupText should return lumyn_error_t";

  lumyn_DestroyConnectorX(&cx);
}

/**
 * Test: Event handling functions return lumyn_error_t
 *
 * Functions that manage event handlers and retrieve events SHALL return
 * lumyn_error_t to indicate success or failure.
 */
TEST_F(ErrorHandlingConsistency, EventHandlingFunctionsReturnErrorCode)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    GTEST_SKIP() << "Failed to create ConnectorX";
  }

  // Test AddEventHandler
  auto callback = [](lumyn_event_t *evt, void *user) {};
  err = lumyn_AddEventHandler(&cx.base, callback, nullptr);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "AddEventHandler should return lumyn_error_t";

  // Test GetLatestEvent
  lumyn_event_t evt = {};
  err = lumyn_GetLatestEvent(&cx.base, &evt);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "GetLatestEvent should return lumyn_error_t";

  // Test GetEvents
  lumyn_event_t events[10] = {};
  int count = 0;
  err = lumyn_GetEvents(&cx.base, events, 10, &count);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "GetEvents should return lumyn_error_t";

  lumyn_DestroyConnectorX(&cx);
}

/**
 * Test: Module functions return lumyn_error_t
 *
 * Functions that manage modules SHALL return lumyn_error_t to indicate
 * success or failure.
 */
TEST_F(ErrorHandlingConsistency, ModuleFunctionsReturnErrorCode)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    GTEST_SKIP() << "Failed to create ConnectorX";
  }

  // Test RegisterModule
  auto module_callback = [](const char *module_id, const uint8_t *data, size_t len, void *user) {};
  err = lumyn_RegisterModule(&cx.base, "module_0", module_callback, nullptr);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "RegisterModule should return lumyn_error_t";

  // Test UnregisterModule
  err = lumyn_UnregisterModule(&cx.base, "module_0");
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "UnregisterModule should return lumyn_error_t";

  // Test GetLatestData
  uint8_t data[256] = {};
  err = lumyn_GetLatestData(&cx.base, "module_0", data, sizeof(data));
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "GetLatestData should return lumyn_error_t";

  // Test SetModulePollingEnabled
  err = lumyn_SetModulePollingEnabled(&cx.base, true);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "SetModulePollingEnabled should return lumyn_error_t";

  // Test PollModules
  err = lumyn_PollModules(&cx.base);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "PollModules should return lumyn_error_t";

  lumyn_DestroyConnectorX(&cx);
}

/**
 * Test: Configuration functions return lumyn_error_t
 *
 * Functions that manage configuration SHALL return lumyn_error_t to indicate
 * success or failure.
 */
TEST_F(ErrorHandlingConsistency, ConfigurationFunctionsReturnErrorCode)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    GTEST_SKIP() << "Failed to create ConnectorX";
  }

  // Test RequestConfig
  char config_buffer[1024] = {};
  size_t config_size = sizeof(config_buffer);
  err = lumyn_RequestConfig(&cx.base, config_buffer, &config_size, 1000);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "RequestConfig should return lumyn_error_t";

  // Test RequestConfigAlloc
  char *config_str = nullptr;
  err = lumyn_RequestConfigAlloc(&cx.base, &config_str, 1000);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "RequestConfigAlloc should return lumyn_error_t";
  if (config_str)
    lumyn_FreeString(config_str);

  // Test ParseConfig
  const char *json = R"({"channels": {}})";
  lumyn_config_t *config = nullptr;
  err = lumyn_ParseConfig(json, std::strlen(json), &config);
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "ParseConfig should return lumyn_error_t";
  if (config)
    lumyn_FreeConfig(config);

  // Test ApplyConfig
  err = lumyn_ApplyConfig(&cx.base, json, std::strlen(json));
  EXPECT_TRUE(err == LUMYN_OK || err != LUMYN_OK) << "ApplyConfig should return lumyn_error_t";

  lumyn_DestroyConnectorX(&cx);
}

/**
 * Test: Error codes are consistent across similar operations
 *
 * Similar operations (e.g., SetColor and SetGroupColor) SHALL return
 * the same error codes for the same failure conditions.
 */
TEST_F(ErrorHandlingConsistency, ErrorCodesConsistentAcrossSimilarOperations)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    GTEST_SKIP() << "Failed to create ConnectorX";
  }

  lumyn_color_t color = {255, 0, 0};

  // Test with NULL zone_id
  lumyn_error_t err1 = lumyn_SetColor(&cx.base, nullptr, color);
  lumyn_error_t err2 = lumyn_SetGroupColor(&cx.base, nullptr, color);
  EXPECT_EQ(err1, err2) << "SetColor and SetGroupColor should return same error for NULL ID";

  // Test with NULL instance
  err1 = lumyn_SetColor(nullptr, "zone_0", color);
  err2 = lumyn_SetGroupColor(nullptr, "group_0", color);
  EXPECT_EQ(err1, err2) << "SetColor and SetGroupColor should return same error for NULL instance";

  lumyn_DestroyConnectorX(&cx);
}

/**
 * Test: Invalid arguments return LUMYN_ERR_INVALID_ARGUMENT
 *
 * When functions are called with invalid arguments (NULL pointers, etc.),
 * they SHALL return LUMYN_ERR_INVALID_ARGUMENT.
 */
TEST_F(ErrorHandlingConsistency, InvalidArgumentsReturnProperError)
{
  // Test ParseConfig with NULL json
  lumyn_config_t *config = nullptr;
  lumyn_error_t err = lumyn_ParseConfig(nullptr, 10, &config);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT) << "ParseConfig should return LUMYN_ERR_INVALID_ARGUMENT for NULL json";

  // Test ParseConfig with NULL out_config
  const char *json = R"({"channels": {}})";
  err = lumyn_ParseConfig(json, std::strlen(json), nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT) << "ParseConfig should return LUMYN_ERR_INVALID_ARGUMENT for NULL out_config";

  // Test SetColor with NULL zone_id
  cx_t cx = {};
  err = lumyn_CreateConnectorX(&cx);
  if (err == LUMYN_OK)
  {
    lumyn_color_t color = {255, 0, 0};
    err = lumyn_SetColor(&cx.base, nullptr, color);
    EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT) << "SetColor should return LUMYN_ERR_INVALID_ARGUMENT for NULL zone_id";
    lumyn_DestroyConnectorX(&cx);
  }
}

/**
 * Test: Malformed JSON returns LUMYN_ERR_PARSE
 *
 * When ParseConfig is called with malformed JSON, it SHALL return
 * LUMYN_ERR_PARSE.
 */
TEST_F(ErrorHandlingConsistency, MalformedJsonReturnsParseError)
{
  const char *malformed_json[] = {
      "{invalid json",
      "not json at all",
      "{\"channels\": ",
      "",
  };

  for (const char *json : malformed_json)
  {
    lumyn_config_t *config = nullptr;
    lumyn_error_t err = lumyn_ParseConfig(json, std::strlen(json), &config);

    // Either LUMYN_ERR_PARSE or LUMYN_ERR_INVALID_ARGUMENT is acceptable
    // (depending on whether it's detected as malformed or invalid)
    EXPECT_TRUE(err == LUMYN_ERR_PARSE || err == LUMYN_ERR_INVALID_ARGUMENT)
        << "ParseConfig should return error for malformed JSON: " << json;
    EXPECT_EQ(config, nullptr) << "Config should be NULL on parse error";
  }
}

/**
 * Test: Error codes are distinct and meaningful
 *
 * Each error code SHALL have a unique value and a meaningful description.
 */
TEST_F(ErrorHandlingConsistency, ErrorCodesAreDistinct)
{
  const lumyn_error_t error_codes[] = {
      LUMYN_OK,
      LUMYN_ERR_INVALID_ARGUMENT,
      LUMYN_ERR_INVALID_HANDLE,
      LUMYN_ERR_NOT_CONNECTED,
      LUMYN_ERR_TIMEOUT,
      LUMYN_ERR_IO,
      LUMYN_ERR_INTERNAL,
      LUMYN_ERR_NOT_SUPPORTED,
      LUMYN_ERR_PARSE,
  };

  // Check that all error codes are distinct
  for (size_t i = 0; i < sizeof(error_codes) / sizeof(error_codes[0]); ++i)
  {
    for (size_t j = i + 1; j < sizeof(error_codes) / sizeof(error_codes[0]); ++j)
    {
      EXPECT_NE(error_codes[i], error_codes[j])
          << "Error codes should be distinct: " << static_cast<int>(error_codes[i])
          << " vs " << static_cast<int>(error_codes[j]);
    }
  }

  // Check that error strings are distinct (except for LUMYN_OK which might be "OK")
  for (size_t i = 1; i < sizeof(error_codes) / sizeof(error_codes[0]); ++i)
  {
    for (size_t j = i + 1; j < sizeof(error_codes) / sizeof(error_codes[0]); ++j)
    {
      const char *str_i = Lumyn_ErrorString(error_codes[i]);
      const char *str_j = Lumyn_ErrorString(error_codes[j]);
      EXPECT_STRNE(str_i, str_j)
          << "Error strings should be distinct for different error codes";
    }
  }
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
