#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_connection_api.cpp
 * @brief Comprehensive tests for connection management API
 *
 * Tests Connect, Disconnect, IsConnected, and related connection functions.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>

class ConnectionAPITest : public ::testing::Test
{
protected:
  cx_t cx_ = {};
  cx_animate_t cxa_ = {};
  bool cx_created_ = false;
  bool cxa_created_ = false;

  void SetUp() override
  {
    if (lumyn_CreateConnectorX(&cx_) == LUMYN_OK)
    {
      cx_created_ = true;
    }
    if (lumyn_CreateConnectorXAnimate(&cxa_) == LUMYN_OK)
    {
      cxa_created_ = true;
    }
  }

  void TearDown() override
  {
    if (cx_created_)
    {
      lumyn_DestroyConnectorX(&cx_);
    }
    if (cxa_created_)
    {
      lumyn_DestroyConnectorXAnimate(&cxa_);
    }
  }
};

// =============================================================================
// IsConnected Tests
// =============================================================================

TEST_F(ConnectionAPITest, IsConnectedReturnsFalseForNewDevice)
{
  ASSERT_TRUE(cx_created_);
  EXPECT_FALSE(lumyn_IsConnected(&cx_.base));
}

TEST_F(ConnectionAPITest, IsConnectedReturnsFalseForNullDevice)
{
  EXPECT_FALSE(lumyn_IsConnected(nullptr));
}

TEST_F(ConnectionAPITest, IsConnectedReturnsFalseForNullInternal)
{
  cx_base_t empty_base = {};
  EXPECT_FALSE(lumyn_IsConnected(&empty_base));
}

// =============================================================================
// Connect Tests - Error Cases
// =============================================================================

TEST_F(ConnectionAPITest, ConnectWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_Connect(nullptr, "/dev/test");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConnectionAPITest, ConnectWithNullPortFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_Connect(&cx_.base, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConnectionAPITest, ConnectWithEmptyPortFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_Connect(&cx_.base, "");
  // Empty port should fail - either INVALID_ARGUMENT or IO error
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(ConnectionAPITest, ConnectWithInvalidPortFails)
{
  ASSERT_TRUE(cx_created_);
  // This should fail with IO error since port doesn't exist
  lumyn_error_t err = lumyn_Connect(&cx_.base, "/dev/nonexistent_port_12345");
  EXPECT_NE(err, LUMYN_OK);
  // Should return IO error or similar
  EXPECT_TRUE(err == LUMYN_ERR_IO || err == LUMYN_ERR_INVALID_ARGUMENT)
      << "Unexpected error: " << Lumyn_ErrorString(err);
}

TEST_F(ConnectionAPITest, ConnectWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_Connect(&empty_base, "/dev/test");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

// =============================================================================
// ConnectWithBaud Tests
// =============================================================================

TEST_F(ConnectionAPITest, ConnectWithBaudNullDeviceFails)
{
  lumyn_error_t err = lumyn_ConnectWithBaud(nullptr, "/dev/test", 115200);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConnectionAPITest, ConnectWithBaudNullPortFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_ConnectWithBaud(&cx_.base, nullptr, 115200);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConnectionAPITest, ConnectWithBaudInvalidPortFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_ConnectWithBaud(&cx_.base, "/dev/nonexistent_port_12345", 115200);
  EXPECT_NE(err, LUMYN_OK);
}

// =============================================================================
// Disconnect Tests
// =============================================================================

TEST_F(ConnectionAPITest, DisconnectWithNullDeviceReturnsError)
{
  lumyn_error_t err = lumyn_Disconnect(nullptr);
  // API returns INVALID_HANDLE (2) for null device
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(ConnectionAPITest, DisconnectOnNotConnectedDeviceSucceeds)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  // Disconnect should succeed even if not connected
  lumyn_error_t err = lumyn_Disconnect(&cx_.base);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(ConnectionAPITest, DisconnectWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_Disconnect(&empty_base);
  // API returns INVALID_HANDLE (2) for null internal
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(ConnectionAPITest, DoubleDisconnectIsSafe)
{
  ASSERT_TRUE(cx_created_);

  EXPECT_EQ(lumyn_Disconnect(&cx_.base), LUMYN_OK);
  EXPECT_EQ(lumyn_Disconnect(&cx_.base), LUMYN_OK);
}

// =============================================================================
// Connection Status Tests
// =============================================================================

TEST_F(ConnectionAPITest, GetCurrentStatusReturnsValidStructure)
{
  ASSERT_TRUE(cx_created_);

  lumyn_connection_status_t status = lumyn_GetCurrentStatus(&cx_.base);

  // New device should not be connected
  EXPECT_FALSE(status.connected);
}

TEST_F(ConnectionAPITest, GetCurrentStatusForNullDeviceReturnsSafe)
{
  lumyn_connection_status_t status = lumyn_GetCurrentStatus(nullptr);

  // Should return a safe default (not connected)
  EXPECT_FALSE(status.connected);
}

// =============================================================================
// Device Health Tests
// =============================================================================

TEST_F(ConnectionAPITest, GetDeviceHealthReturnsValidStatus)
{
  ASSERT_TRUE(cx_created_);

  lumyn_status_t health = lumyn_GetDeviceHealth(&cx_.base);

  // Just verify it returns some value without crashing
  // The actual value depends on device state
  (void)health; // Avoid unused variable warning
  SUCCEED();
}

TEST_F(ConnectionAPITest, GetDeviceHealthForNullDeviceReturnsSafe)
{
  lumyn_status_t health = lumyn_GetDeviceHealth(nullptr);

  // Should return a safe default
  (void)health;
  SUCCEED();
}

// =============================================================================
// Connection State Callback Tests
// =============================================================================

static bool g_callback_invoked = false;
static bool g_callback_connected_state = false;

static void test_connection_callback(bool connected, void *user)
{
  g_callback_invoked = true;
  g_callback_connected_state = connected;
  if (user)
  {
    *static_cast<int *>(user) = connected ? 1 : 0;
  }
}

TEST_F(ConnectionAPITest, SetConnectionStateCallbackWithValidParams)
{
  ASSERT_TRUE(cx_created_);

  int user_data = -1;
  // Setting the callback should not crash
  lumyn_SetConnectionStateCallback(&cx_.base, test_connection_callback, &user_data);

  SUCCEED();
}

TEST_F(ConnectionAPITest, SetConnectionStateCallbackWithNullCallback)
{
  ASSERT_TRUE(cx_created_);

  // Should not crash
  lumyn_SetConnectionStateCallback(&cx_.base, nullptr, nullptr);

  SUCCEED();
}

TEST_F(ConnectionAPITest, SetConnectionStateCallbackWithNullDevice)
{
  // Should not crash
  lumyn_SetConnectionStateCallback(nullptr, test_connection_callback, nullptr);

  SUCCEED();
}

// =============================================================================
// ConnectorXAnimate Connection Tests
// =============================================================================

TEST_F(ConnectionAPITest, ConnectorXAnimateIsConnectedReturnsFalse)
{
  ASSERT_TRUE(cxa_created_);
  EXPECT_FALSE(lumyn_IsConnected(&cxa_.base));
}

TEST_F(ConnectionAPITest, ConnectorXAnimateConnectWithInvalidPortFails)
{
  ASSERT_TRUE(cxa_created_);
  lumyn_error_t err = lumyn_Connect(&cxa_.base, "/dev/nonexistent_port_12345");
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(ConnectionAPITest, ConnectorXAnimateDisconnectWhenNotConnectedSucceeds)
{
  ASSERT_TRUE(cxa_created_);
  lumyn_error_t err = lumyn_Disconnect(&cxa_.base);
  EXPECT_EQ(err, LUMYN_OK);
}

// =============================================================================
// Connection with Destroyed Device
// =============================================================================

TEST_F(ConnectionAPITest, ConnectAfterDestroyFails)
{
  cx_t cx = {};
  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);
  lumyn_DestroyConnectorX(&cx);

  // Internal should be null now
  EXPECT_EQ(cx.base._internal, nullptr);

  // Connection should fail
  lumyn_error_t err = lumyn_Connect(&cx.base, "/dev/test");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ConnectionAPITest, IsConnectedAfterDestroyReturnsFalse)
{
  cx_t cx = {};
  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);
  lumyn_DestroyConnectorX(&cx);

  EXPECT_FALSE(lumyn_IsConnected(&cx.base));
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
