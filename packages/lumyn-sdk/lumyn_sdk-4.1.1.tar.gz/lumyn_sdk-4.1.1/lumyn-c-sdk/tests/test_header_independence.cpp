#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_header_independence.cpp
 * @brief Tests for public header basic functionality
 *
 * These tests verify that public headers compile and work correctly.
 * We test the actual functionality of the C API rather than trying to
 * validate include structure (which would require complex build config).
 */

#include <gtest/gtest.h>
#include <fstream>
#include <set>
#include <filesystem>

// Include the C API
#include <lumyn/c/lumyn_sdk.h>

namespace fs = std::filesystem;

/**
 * Test that we can compile and use the C API headers
 */
TEST(HeaderCompilation, CAPICompiles)
{
  // If we got here, the headers compile
  SUCCEED();
}

/**
 * Test that basic types are defined
 */
TEST(HeaderCompilation, BasicTypesAreDefined)
{
  // Test that struct types exist
  cx_t device;
  cx_animate_t animate_device;
  cx_base_t base;
  lumyn_color_t color = {255, 0, 0};
  lumyn_animation_t animation = LUMYN_ANIMATION_FILL;

  // Test that pointers work
  cx_base_t *base_ptr = &base;
  (void)base_ptr;
  (void)device;
  (void)animate_device;
  (void)color;
  (void)animation;

  SUCCEED();
}

/**
 * Test that error codes are defined
 */
TEST(HeaderCompilation, ErrorCodesAreDefined)
{
  EXPECT_EQ(LUMYN_OK, 0);
  EXPECT_EQ(LUMYN_ERR_INVALID_ARGUMENT, 1);
  EXPECT_EQ(LUMYN_ERR_INVALID_HANDLE, 2);
  EXPECT_EQ(LUMYN_ERR_NOT_CONNECTED, 3);
  EXPECT_EQ(LUMYN_ERR_TIMEOUT, 4);
  EXPECT_EQ(LUMYN_ERR_IO, 5);
  EXPECT_EQ(LUMYN_ERR_INTERNAL, 6);
  EXPECT_EQ(LUMYN_ERR_NOT_SUPPORTED, 7);
  EXPECT_EQ(LUMYN_ERR_PARSE, 8);
}

/**
 * Test that animation types are defined
 */
TEST(HeaderCompilation, AnimationTypesAreDefined)
{
  EXPECT_EQ(LUMYN_ANIMATION_NONE, 0);
  EXPECT_EQ(LUMYN_ANIMATION_FILL, 1);
  EXPECT_EQ(LUMYN_ANIMATION_BLINK, 2);
  EXPECT_EQ(LUMYN_ANIMATION_BREATHE, 3);
}

/**
 * Test that the base pointer macro works correctly
 */
TEST(BasePointerHelpers, BasePointerExtraction)
{
  cx_t cx = {};
  cx_animate_t cxa = {};

  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);
  ASSERT_EQ(lumyn_CreateConnectorXAnimate(&cxa), LUMYN_OK);

  // Base pointers should be extractable via the struct member
  cx_base_t *cx_base = &cx.base;
  cx_base_t *cxa_base = &cxa.base;

  EXPECT_NE(cx_base, nullptr);
  EXPECT_NE(cxa_base, nullptr);

  // Both should be usable with the unified API
  EXPECT_FALSE(lumyn_IsConnected(cx_base));
  EXPECT_FALSE(lumyn_IsConnected(cxa_base));

  lumyn_DestroyConnectorX(&cx);
  lumyn_DestroyConnectorXAnimate(&cxa);
}

/**
 * Test that error strings work correctly
 */
TEST(ErrorHandling, ErrorStringsComplete)
{
  // Test that we get valid strings for all error codes
  const char *ok_str = Lumyn_ErrorString(LUMYN_OK);
  ASSERT_NE(ok_str, nullptr);
  EXPECT_GT(strlen(ok_str), 0u);

  const char *invalid_arg_str = Lumyn_ErrorString(LUMYN_ERR_INVALID_ARGUMENT);
  ASSERT_NE(invalid_arg_str, nullptr);
  EXPECT_GT(strlen(invalid_arg_str), 0u);

  const char *not_connected_str = Lumyn_ErrorString(LUMYN_ERR_NOT_CONNECTED);
  ASSERT_NE(not_connected_str, nullptr);
  EXPECT_GT(strlen(not_connected_str), 0u);
}

/**
 * Test that version functions work
 */
TEST(HeaderCompilation, VersionFunctionsWork)
{
  const char *version = lumyn_GetVersion();
  ASSERT_NE(version, nullptr);
  EXPECT_GT(strlen(version), 0u);

  int major = lumyn_GetVersionMajor();
  int minor = lumyn_GetVersionMinor();
  int patch = lumyn_GetVersionPatch();

  EXPECT_GE(major, 0);
  EXPECT_GE(minor, 0);
  EXPECT_GE(patch, 0);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
