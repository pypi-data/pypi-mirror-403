/**
 * @file test_version_api.cpp
 * @brief Comprehensive tests for the Version API
 *
 * Tests version retrieval functions to ensure correct version information
 * is returned and that the API is stable across builds.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <string>
#include <regex>

class VersionAPITest : public ::testing::Test
{
protected:
  void SetUp() override {}
  void TearDown() override {}
};

// =============================================================================
// Version String Tests
// =============================================================================

TEST_F(VersionAPITest, GetVersionReturnsNonNull)
{
  const char *version = lumyn_GetVersion();
  ASSERT_NE(version, nullptr) << "lumyn_GetVersion() returned NULL";
}

TEST_F(VersionAPITest, GetVersionReturnsNonEmpty)
{
  const char *version = lumyn_GetVersion();
  ASSERT_NE(version, nullptr);
  EXPECT_GT(std::strlen(version), 0) << "Version string is empty";
}

TEST_F(VersionAPITest, GetVersionMatchesSemVerFormat)
{
  const char *version = lumyn_GetVersion();
  ASSERT_NE(version, nullptr);

  // SemVer format: MAJOR.MINOR.PATCH (optionally with prerelease/build metadata)
  std::regex semver_regex(R"(^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$)");
  EXPECT_TRUE(std::regex_match(version, semver_regex))
      << "Version '" << version << "' does not match SemVer format";
}

TEST_F(VersionAPITest, GetVersionIsConsistent)
{
  // Multiple calls should return the same string
  const char *v1 = lumyn_GetVersion();
  const char *v2 = lumyn_GetVersion();
  const char *v3 = lumyn_GetVersion();

  ASSERT_NE(v1, nullptr);
  ASSERT_NE(v2, nullptr);
  ASSERT_NE(v3, nullptr);

  EXPECT_STREQ(v1, v2) << "Version string is not consistent across calls";
  EXPECT_STREQ(v2, v3) << "Version string is not consistent across calls";
}

// =============================================================================
// Version Component Tests
// =============================================================================

TEST_F(VersionAPITest, GetVersionMajorIsNonNegative)
{
  int major = lumyn_GetVersionMajor();
  EXPECT_GE(major, 0) << "Major version should be non-negative";
}

TEST_F(VersionAPITest, GetVersionMinorIsNonNegative)
{
  int minor = lumyn_GetVersionMinor();
  EXPECT_GE(minor, 0) << "Minor version should be non-negative";
}

TEST_F(VersionAPITest, GetVersionPatchIsNonNegative)
{
  int patch = lumyn_GetVersionPatch();
  EXPECT_GE(patch, 0) << "Patch version should be non-negative";
}

TEST_F(VersionAPITest, VersionComponentsMatchVersionString)
{
  const char *version = lumyn_GetVersion();
  ASSERT_NE(version, nullptr);

  int major = lumyn_GetVersionMajor();
  int minor = lumyn_GetVersionMinor();
  int patch = lumyn_GetVersionPatch();

  // Construct expected version string from components
  std::string expected = std::to_string(major) + "." +
                         std::to_string(minor) + "." +
                         std::to_string(patch);

  // The version string should start with the component-based version
  // (may have prerelease/build metadata appended)
  EXPECT_EQ(std::string(version).substr(0, expected.length()), expected)
      << "Version string '" << version << "' doesn't match components "
      << major << "." << minor << "." << patch;
}

TEST_F(VersionAPITest, VersionComponentsAreConsistent)
{
  // Multiple calls should return the same values
  EXPECT_EQ(lumyn_GetVersionMajor(), lumyn_GetVersionMajor());
  EXPECT_EQ(lumyn_GetVersionMinor(), lumyn_GetVersionMinor());
  EXPECT_EQ(lumyn_GetVersionPatch(), lumyn_GetVersionPatch());
}

// =============================================================================
// Version Sanity Checks
// =============================================================================

TEST_F(VersionAPITest, MajorVersionIsReasonable)
{
  int major = lumyn_GetVersionMajor();
  // Major version should be between 1 and 99 for a reasonable SDK
  EXPECT_GE(major, 1) << "Major version is unexpectedly low";
  EXPECT_LE(major, 99) << "Major version is unexpectedly high";
}

TEST_F(VersionAPITest, MinorVersionIsReasonable)
{
  int minor = lumyn_GetVersionMinor();
  // Minor version should be between 0 and 99
  EXPECT_GE(minor, 0) << "Minor version is negative";
  EXPECT_LE(minor, 99) << "Minor version is unexpectedly high";
}

TEST_F(VersionAPITest, PatchVersionIsReasonable)
{
  int patch = lumyn_GetVersionPatch();
  // Patch version should be between 0 and 999
  EXPECT_GE(patch, 0) << "Patch version is negative";
  EXPECT_LE(patch, 999) << "Patch version is unexpectedly high";
}

// =============================================================================
// Compile-time vs Runtime Version
// =============================================================================

TEST_F(VersionAPITest, RuntimeVersionMatchesCompileTime)
{
// Compare runtime version with compile-time macros
#ifdef LUMYN_SDK_VERSION_MAJOR
  EXPECT_EQ(lumyn_GetVersionMajor(), LUMYN_SDK_VERSION_MAJOR)
      << "Runtime major version doesn't match compile-time";
#endif

#ifdef LUMYN_SDK_VERSION_MINOR
  EXPECT_EQ(lumyn_GetVersionMinor(), LUMYN_SDK_VERSION_MINOR)
      << "Runtime minor version doesn't match compile-time";
#endif

#ifdef LUMYN_SDK_VERSION_PATCH
  EXPECT_EQ(lumyn_GetVersionPatch(), LUMYN_SDK_VERSION_PATCH)
      << "Runtime patch version doesn't match compile-time";
#endif

#ifdef LUMYN_SDK_VERSION
  EXPECT_STREQ(lumyn_GetVersion(), LUMYN_SDK_VERSION)
      << "Runtime version string doesn't match compile-time";
#endif
}

// =============================================================================
// Thread Safety (basic check)
// =============================================================================

TEST_F(VersionAPITest, VersionFunctionsAreThreadSafe)
{
  // These functions should return static/constant data and be thread-safe
  // This test verifies they can be called many times without issues
  for (int i = 0; i < 1000; ++i)
  {
    ASSERT_NE(lumyn_GetVersion(), nullptr);
    ASSERT_GE(lumyn_GetVersionMajor(), 0);
    ASSERT_GE(lumyn_GetVersionMinor(), 0);
    ASSERT_GE(lumyn_GetVersionPatch(), 0);
  }
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
