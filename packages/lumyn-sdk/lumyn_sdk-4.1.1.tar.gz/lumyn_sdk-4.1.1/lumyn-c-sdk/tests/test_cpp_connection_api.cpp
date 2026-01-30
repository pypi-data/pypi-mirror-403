/**
 * @file test_cpp_connection_api.cpp
 * @brief Tests for C++ SDK connection management
 *
 * Tests Connect, Disconnect, IsConnected, and status functions.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>

// =============================================================================
// ConnectorX Connection Tests
// =============================================================================

class CppConnectorXConnectionTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(CppConnectorXConnectionTest, ConnectWithInvalidPortFails)
{
  auto err = cx_.Connect("/dev/nonexistent_port_12345");
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXConnectionTest, ConnectWithEmptyPortFails)
{
  auto err = cx_.Connect("");
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXConnectionTest, ConnectWithBaudRateFails)
{
  auto err = cx_.Connect("/dev/nonexistent", 115200);
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXConnectionTest, ConnectWithOptionalBaudFails)
{
  auto err = cx_.Connect("/dev/nonexistent", std::optional<int>(9600));
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXConnectionTest, DisconnectOnUnconnectedDeviceIsSafe)
{
  EXPECT_FALSE(cx_.IsConnected());
  cx_.Disconnect();
  EXPECT_FALSE(cx_.IsConnected());
}

TEST_F(CppConnectorXConnectionTest, DoubleDisconnectIsSafe)
{
  cx_.Disconnect();
  cx_.Disconnect();
  SUCCEED();
}

TEST_F(CppConnectorXConnectionTest, IsConnectedAfterFailedConnect)
{
  cx_.Connect("/dev/nonexistent");
  EXPECT_FALSE(cx_.IsConnected());
}

TEST_F(CppConnectorXConnectionTest, GetCurrentStatusAfterFailedConnect)
{
  cx_.Connect("/dev/nonexistent");
  auto status = cx_.GetCurrentStatus();
  EXPECT_FALSE(status.connected);
}

// =============================================================================
// ConnectorXAnimate Connection Tests
// =============================================================================

class CppConnectorXAnimateConnectionTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorXAnimate cxa_;
};

TEST_F(CppConnectorXAnimateConnectionTest, ConnectWithInvalidPortFails)
{
  auto err = cxa_.Connect("/dev/nonexistent_port_12345");
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXAnimateConnectionTest, ConnectWithEmptyPortFails)
{
  auto err = cxa_.Connect("");
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXAnimateConnectionTest, DisconnectOnUnconnectedIsSafe)
{
  cxa_.Disconnect();
  SUCCEED();
}

TEST_F(CppConnectorXAnimateConnectionTest, DoubleDisconnectIsSafe)
{
  cxa_.Disconnect();
  cxa_.Disconnect();
  SUCCEED();
}

TEST_F(CppConnectorXAnimateConnectionTest, IsConnectedAfterFailedConnect)
{
  cxa_.Connect("/dev/nonexistent");
  EXPECT_FALSE(cxa_.IsConnected());
}

// =============================================================================
// Connection State Callback Tests
// =============================================================================

TEST(ConnectionCallbackTest, SetConnectionStateCallbackConnectorX)
{
  lumyn::device::ConnectorX cx;
  bool called = false;
  cx.SetConnectionStateCallback([&called](bool connected)
                                {
    called = true;
    (void)connected; });
  SUCCEED();
}

// =============================================================================
// Thread Safety Tests
// =============================================================================

#include <thread>
#include <atomic>

class CppConnectionThreadSafetyTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(CppConnectionThreadSafetyTest, ConcurrentIsConnectedCalls)
{
  std::atomic<int> count{0};
  auto worker = [this, &count]()
  {
    for (int i = 0; i < 100; ++i)
    {
      (void)cx_.IsConnected();
      count++;
    }
  };

  std::thread t1(worker);
  std::thread t2(worker);
  t1.join();
  t2.join();

  EXPECT_EQ(count.load(), 200);
}

TEST_F(CppConnectionThreadSafetyTest, ConcurrentGetStatusCalls)
{
  std::atomic<int> count{0};
  auto worker = [this, &count]()
  {
    for (int i = 0; i < 100; ++i)
    {
      auto status = cx_.GetCurrentStatus();
      (void)status;
      count++;
    }
  };

  std::thread t1(worker);
  std::thread t2(worker);
  t1.join();
  t2.join();

  EXPECT_EQ(count.load(), 200);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
