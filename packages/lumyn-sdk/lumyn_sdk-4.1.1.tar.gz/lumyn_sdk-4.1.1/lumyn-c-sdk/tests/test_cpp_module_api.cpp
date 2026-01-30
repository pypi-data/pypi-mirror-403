/**
 * @file test_cpp_module_api.cpp
 * @brief Tests for C++ SDK module functionality (ConnectorX only)
 *
 * Tests module polling, registration, and data retrieval.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>

// =============================================================================
// Module Polling Tests
// =============================================================================

class CppModulePollingTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(CppModulePollingTest, SetModulePollingEnabledTrue)
{
  cx_.SetModulePollingEnabled(true);
  SUCCEED();
}

TEST_F(CppModulePollingTest, SetModulePollingEnabledFalse)
{
  cx_.SetModulePollingEnabled(false);
  SUCCEED();
}

TEST_F(CppModulePollingTest, SetModulePollingEnabledToggle)
{
  cx_.SetModulePollingEnabled(true);
  cx_.SetModulePollingEnabled(false);
  cx_.SetModulePollingEnabled(true);
  SUCCEED();
}

TEST_F(CppModulePollingTest, PollModulesWhenDisconnected)
{
  cx_.PollModules();
  SUCCEED();
}

TEST_F(CppModulePollingTest, PollModulesMultipleTimes)
{
  cx_.PollModules();
  cx_.PollModules();
  cx_.PollModules();
  SUCCEED();
}

// =============================================================================
// Device Control Tests
// =============================================================================

class CppDeviceControlTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(CppDeviceControlTest, RestartDeviceWithZeroDelay)
{
  cx_.RestartDevice(0);
  SUCCEED();
}

TEST_F(CppDeviceControlTest, RestartDeviceWithDelay)
{
  cx_.RestartDevice(1000);
  SUCCEED();
}

TEST_F(CppDeviceControlTest, RestartDeviceWithLargeDelay)
{
  cx_.RestartDevice(60000);
  SUCCEED();
}

TEST_F(CppDeviceControlTest, RestartDeviceMultipleTimes)
{
  cx_.RestartDevice(0);
  cx_.RestartDevice(100);
  cx_.RestartDevice(0);
  SUCCEED();
}

// =============================================================================
// SetAutoPollEvents Chaining Tests (ConnectorX specific)
// =============================================================================

TEST(ConnectorXChainingTest, SetAutoPollEventsReturnsSelf)
{
  lumyn::device::ConnectorX cx;
  auto &ref = cx.SetAutoPollEvents(true);
  EXPECT_EQ(&ref, &cx);
}

TEST(ConnectorXAnimateChainingTest, SetAutoPollEventsReturnsSelf)
{
  lumyn::device::ConnectorXAnimate cxa;
  auto &ref = cxa.SetAutoPollEvents(true);
  EXPECT_EQ(&ref, &cxa);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
