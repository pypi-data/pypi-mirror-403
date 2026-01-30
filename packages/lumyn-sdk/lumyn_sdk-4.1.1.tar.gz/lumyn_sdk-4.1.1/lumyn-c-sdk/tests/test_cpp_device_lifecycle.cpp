/**
 * @file test_cpp_device_lifecycle.cpp
 * @brief Tests for C++ SDK device construction and destruction
 *
 * Tests ConnectorX and ConnectorXAnimate lifecycle management.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>

// =============================================================================
// ConnectorX Lifecycle Tests
// =============================================================================

class ConnectorXLifecycleTest : public ::testing::Test
{
};

TEST_F(ConnectorXLifecycleTest, DefaultConstruction)
{
  lumyn::device::ConnectorX cx;
  SUCCEED();
}

TEST_F(ConnectorXLifecycleTest, DestructionWithoutConnection)
{
  {
    lumyn::device::ConnectorX cx;
  }
  SUCCEED();
}

TEST_F(ConnectorXLifecycleTest, IsConnectedReturnsFalseInitially)
{
  lumyn::device::ConnectorX cx;
  EXPECT_FALSE(cx.IsConnected());
}

TEST_F(ConnectorXLifecycleTest, GetCurrentStatusReturnsDisconnected)
{
  lumyn::device::ConnectorX cx;
  auto status = cx.GetCurrentStatus();
  EXPECT_FALSE(status.connected);
  EXPECT_FALSE(status.enabled);
}

TEST_F(ConnectorXLifecycleTest, GetDeviceHealthReturnsUnknown)
{
  lumyn::device::ConnectorX cx;
  auto health = cx.GetDeviceHealth();
  EXPECT_EQ(health, LUMYN_STATUS_UNKNOWN);
}

TEST_F(ConnectorXLifecycleTest, MultipleInstancesAreIndependent)
{
  lumyn::device::ConnectorX cx1;
  lumyn::device::ConnectorX cx2;

  EXPECT_FALSE(cx1.IsConnected());
  EXPECT_FALSE(cx2.IsConnected());
}

// =============================================================================
// ConnectorXAnimate Lifecycle Tests
// =============================================================================

class ConnectorXAnimateLifecycleTest : public ::testing::Test
{
};

TEST_F(ConnectorXAnimateLifecycleTest, DefaultConstruction)
{
  lumyn::device::ConnectorXAnimate cxa;
  SUCCEED();
}

TEST_F(ConnectorXAnimateLifecycleTest, DestructionWithoutConnection)
{
  {
    lumyn::device::ConnectorXAnimate cxa;
  }
  SUCCEED();
}

TEST_F(ConnectorXAnimateLifecycleTest, IsConnectedReturnsFalseInitially)
{
  lumyn::device::ConnectorXAnimate cxa;
  EXPECT_FALSE(cxa.IsConnected());
}

TEST_F(ConnectorXAnimateLifecycleTest, GetCurrentStatusReturnsDisconnected)
{
  lumyn::device::ConnectorXAnimate cxa;
  auto status = cxa.GetCurrentStatus();
  EXPECT_FALSE(status.connected);
}

TEST_F(ConnectorXAnimateLifecycleTest, GetDeviceHealthReturnsUnknown)
{
  lumyn::device::ConnectorXAnimate cxa;
  auto health = cxa.GetDeviceHealth();
  EXPECT_EQ(health, LUMYN_STATUS_UNKNOWN);
}

TEST_F(ConnectorXAnimateLifecycleTest, MultipleInstancesAreIndependent)
{
  lumyn::device::ConnectorXAnimate cxa1;
  lumyn::device::ConnectorXAnimate cxa2;

  EXPECT_FALSE(cxa1.IsConnected());
  EXPECT_FALSE(cxa2.IsConnected());
}

// =============================================================================
// Mixed Device Types
// =============================================================================

TEST(MixedDeviceTest, ConnectorXAndAnimateCanCoexist)
{
  lumyn::device::ConnectorX cx;
  lumyn::device::ConnectorXAnimate cxa;

  EXPECT_FALSE(cx.IsConnected());
  EXPECT_FALSE(cxa.IsConnected());
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
