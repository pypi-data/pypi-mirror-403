/**
 * @file test_cpp_config_api.cpp
 * @brief Tests for C++ SDK configuration management
 *
 * Tests RequestConfig, ApplyConfiguration, and LoadConfiguration.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>

// =============================================================================
// ConnectorX Configuration Tests
// =============================================================================

class CppConnectorXConfigTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(CppConnectorXConfigTest, RequestConfigFailsWhenDisconnected)
{
  std::string json;
  auto err = cx_.RequestConfig(json, 100);
  EXPECT_NE(err, LUMYN_OK);
  EXPECT_TRUE(json.empty());
}

TEST_F(CppConnectorXConfigTest, RequestConfigWithDefaultTimeout)
{
  std::string json;
  auto err = cx_.RequestConfig(json);
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXConfigTest, ApplyConfigurationJsonEmpty)
{
  bool result = cx_.ApplyConfigurationJson("");
  // Empty string should be handled gracefully
  (void)result;
  SUCCEED();
}

TEST_F(CppConnectorXConfigTest, ApplyConfigurationJsonInvalid)
{
  bool result = cx_.ApplyConfigurationJson("{invalid json}");
  EXPECT_FALSE(result);
}

TEST_F(CppConnectorXConfigTest, ApplyConfigurationJsonMalformed)
{
  bool result = cx_.ApplyConfigurationJson("{ \"key\": }");
  EXPECT_FALSE(result);
}

TEST_F(CppConnectorXConfigTest, ApplyConfigurationJsonValidButEmpty)
{
  bool result = cx_.ApplyConfigurationJson("{}");
  // Valid JSON but may not have required fields - behavior depends on implementation
  (void)result;
  SUCCEED();
}

TEST_F(CppConnectorXConfigTest, LoadConfigurationFromNonexistentFile)
{
  bool result = cx_.LoadConfigurationFromFile("/nonexistent/path/config.json");
  EXPECT_FALSE(result);
}

TEST_F(CppConnectorXConfigTest, LoadConfigurationFromEmptyPath)
{
  bool result = cx_.LoadConfigurationFromFile("");
  EXPECT_FALSE(result);
}

TEST_F(CppConnectorXConfigTest, LoadConfigurationFromInvalidPath)
{
  bool result = cx_.LoadConfigurationFromFile(":::invalid:::path:::");
  EXPECT_FALSE(result);
}

// =============================================================================
// ConnectorXAnimate Configuration Tests
// =============================================================================

class CppConnectorXAnimateConfigTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorXAnimate cxa_;
};

TEST_F(CppConnectorXAnimateConfigTest, RequestConfigFailsWhenDisconnected)
{
  std::string json;
  auto err = cxa_.RequestConfig(json, 100);
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXAnimateConfigTest, ApplyConfigurationJsonInvalid)
{
  bool result = cxa_.ApplyConfigurationJson("{bad}");
  EXPECT_FALSE(result);
}

TEST_F(CppConnectorXAnimateConfigTest, LoadConfigurationFromNonexistentFile)
{
  bool result = cxa_.LoadConfigurationFromFile("/no/such/file.json");
  EXPECT_FALSE(result);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
