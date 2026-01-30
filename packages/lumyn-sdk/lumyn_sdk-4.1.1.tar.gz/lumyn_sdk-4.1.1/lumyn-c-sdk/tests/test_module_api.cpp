#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_module_api.cpp
 * @brief Comprehensive tests for the Module API
 *
 * Tests module registration, unregistration, data retrieval, and polling.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <atomic>

class ModuleAPITest : public ::testing::Test
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

// Static test helpers
static std::atomic<int> g_module_callback_count{0};
static const char *g_last_module_id = nullptr;

static void test_module_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  g_module_callback_count++;
  g_last_module_id = module_id;
  (void)data;
  (void)len;
  (void)user;
}

static void reset_module_state()
{
  g_module_callback_count = 0;
  g_last_module_id = nullptr;
}

// =============================================================================
// RegisterModule Tests
// =============================================================================

TEST_F(ModuleAPITest, RegisterModuleWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_RegisterModule(nullptr, "module_0", test_module_callback, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, RegisterModuleWithEmptyId)
{
  ASSERT_TRUE(cx_created_);
  // Empty module ID is accepted by the API
  lumyn_error_t err = lumyn_RegisterModule(&cx_.base, "", test_module_callback, nullptr);
  // Just verify the call doesn't crash - API may accept empty strings
  (void)err;
}

TEST_F(ModuleAPITest, RegisterModuleWithNullCallbackFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_RegisterModule(&cx_.base, "module_0", nullptr, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, RegisterModuleWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_RegisterModule(&empty_base, "module_0", test_module_callback, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, RegisterModuleSucceeds)
{
  ASSERT_TRUE(cx_created_);

  reset_module_state();
  lumyn_error_t err = lumyn_RegisterModule(&cx_.base, "module_0", test_module_callback, nullptr);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(ModuleAPITest, RegisterModuleWithUserData)
{
  ASSERT_TRUE(cx_created_);

  int user_data = 42;
  lumyn_error_t err = lumyn_RegisterModule(&cx_.base, "module_0", test_module_callback, &user_data);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(ModuleAPITest, RegisterMultipleModules)
{
  ASSERT_TRUE(cx_created_);

  EXPECT_EQ(lumyn_RegisterModule(&cx_.base, "module_0", test_module_callback, nullptr), LUMYN_OK);
  EXPECT_EQ(lumyn_RegisterModule(&cx_.base, "module_1", test_module_callback, nullptr), LUMYN_OK);
  EXPECT_EQ(lumyn_RegisterModule(&cx_.base, "module_2", test_module_callback, nullptr), LUMYN_OK);
}

// =============================================================================
// UnregisterModule Tests
// =============================================================================

TEST_F(ModuleAPITest, UnregisterModuleWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_UnregisterModule(nullptr, "module_0");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, UnregisterModuleWithNullModuleIdFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_UnregisterModule(&cx_.base, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, UnregisterModuleWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_UnregisterModule(&empty_base, "module_0");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, UnregisterNonExistentModuleFails)
{
  ASSERT_TRUE(cx_created_);

  // Try to unregister a module that was never registered
  lumyn_error_t err = lumyn_UnregisterModule(&cx_.base, "nonexistent_module");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, UnregisterRegisteredModuleSucceeds)
{
  ASSERT_TRUE(cx_created_);

  // Register first
  ASSERT_EQ(lumyn_RegisterModule(&cx_.base, "module_0", test_module_callback, nullptr), LUMYN_OK);

  // Then unregister
  lumyn_error_t err = lumyn_UnregisterModule(&cx_.base, "module_0");
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(ModuleAPITest, DoubleUnregisterFails)
{
  ASSERT_TRUE(cx_created_);

  ASSERT_EQ(lumyn_RegisterModule(&cx_.base, "module_0", test_module_callback, nullptr), LUMYN_OK);
  ASSERT_EQ(lumyn_UnregisterModule(&cx_.base, "module_0"), LUMYN_OK);

  // Second unregister should fail
  lumyn_error_t err = lumyn_UnregisterModule(&cx_.base, "module_0");
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

// =============================================================================
// GetLatestData Tests
// =============================================================================

TEST_F(ModuleAPITest, GetLatestDataWithNullDeviceFails)
{
  uint8_t buffer[256] = {};
  lumyn_error_t err = lumyn_GetLatestData(nullptr, "module_0", buffer, sizeof(buffer));
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, GetLatestDataWithNullModuleIdFails)
{
  ASSERT_TRUE(cx_created_);
  uint8_t buffer[256] = {};
  lumyn_error_t err = lumyn_GetLatestData(&cx_.base, nullptr, buffer, sizeof(buffer));
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, GetLatestDataWithNullBufferFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_GetLatestData(&cx_.base, "module_0", nullptr, 256);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, GetLatestDataWithZeroSizeFails)
{
  ASSERT_TRUE(cx_created_);
  uint8_t buffer[256] = {};
  lumyn_error_t err = lumyn_GetLatestData(&cx_.base, "module_0", buffer, 0);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, GetLatestDataWithNullInternalFails)
{
  cx_base_t empty_base = {};
  uint8_t buffer[256] = {};
  lumyn_error_t err = lumyn_GetLatestData(&empty_base, "module_0", buffer, sizeof(buffer));
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, GetLatestDataWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  uint8_t buffer[256] = {};
  lumyn_error_t err = lumyn_GetLatestData(&cx_.base, "module_0", buffer, sizeof(buffer));
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// SetModulePollingEnabled Tests
// =============================================================================

TEST_F(ModuleAPITest, SetModulePollingEnabledWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_SetModulePollingEnabled(nullptr, true);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, SetModulePollingEnabledWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_SetModulePollingEnabled(&empty_base, true);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, SetModulePollingEnabledSucceeds)
{
  ASSERT_TRUE(cx_created_);

  EXPECT_EQ(lumyn_SetModulePollingEnabled(&cx_.base, true), LUMYN_OK);
  EXPECT_EQ(lumyn_SetModulePollingEnabled(&cx_.base, false), LUMYN_OK);
}

TEST_F(ModuleAPITest, SetModulePollingEnabledCanBeToggled)
{
  ASSERT_TRUE(cx_created_);

  for (int i = 0; i < 10; ++i)
  {
    EXPECT_EQ(lumyn_SetModulePollingEnabled(&cx_.base, i % 2 == 0), LUMYN_OK);
  }
}

// =============================================================================
// PollModules Tests
// =============================================================================

TEST_F(ModuleAPITest, PollModulesWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_PollModules(nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, PollModulesWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_PollModules(&empty_base);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(ModuleAPITest, PollModulesSucceeds)
{
  ASSERT_TRUE(cx_created_);

  // Polling should succeed even when not connected (it just won't do anything)
  lumyn_error_t err = lumyn_PollModules(&cx_.base);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(ModuleAPITest, PollModulesCanBeCalledRepeatedly)
{
  ASSERT_TRUE(cx_created_);

  for (int i = 0; i < 100; ++i)
  {
    EXPECT_EQ(lumyn_PollModules(&cx_.base), LUMYN_OK);
  }
}

// =============================================================================
// ConnectorXAnimate Module Tests
// =============================================================================

TEST_F(ModuleAPITest, ConnectorXAnimateRegisterModuleFails)
{
  ASSERT_TRUE(cxa_created_);

  // ConnectorXAnimate doesn't support modules (no module vtable)
  lumyn_error_t err = lumyn_RegisterModule(&cxa_.base, "module_0", test_module_callback, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_NOT_SUPPORTED);
}

TEST_F(ModuleAPITest, ConnectorXAnimateUnregisterModuleFails)
{
  ASSERT_TRUE(cxa_created_);

  lumyn_error_t err = lumyn_UnregisterModule(&cxa_.base, "module_0");
  EXPECT_EQ(err, LUMYN_ERR_NOT_SUPPORTED);
}

TEST_F(ModuleAPITest, ConnectorXAnimateGetLatestDataFails)
{
  ASSERT_TRUE(cxa_created_);

  uint8_t buffer[256] = {};
  lumyn_error_t err = lumyn_GetLatestData(&cxa_.base, "module_0", buffer, sizeof(buffer));
  EXPECT_EQ(err, LUMYN_ERR_NOT_SUPPORTED);
}

TEST_F(ModuleAPITest, ConnectorXAnimateSetModulePollingEnabledFails)
{
  ASSERT_TRUE(cxa_created_);

  lumyn_error_t err = lumyn_SetModulePollingEnabled(&cxa_.base, true);
  EXPECT_EQ(err, LUMYN_ERR_NOT_SUPPORTED);
}

TEST_F(ModuleAPITest, ConnectorXAnimatePollModulesFails)
{
  ASSERT_TRUE(cxa_created_);

  lumyn_error_t err = lumyn_PollModules(&cxa_.base);
  EXPECT_EQ(err, LUMYN_ERR_NOT_SUPPORTED);
}

// =============================================================================
// Module ID Edge Cases
// =============================================================================

TEST_F(ModuleAPITest, RegisterModuleWithLongId)
{
  ASSERT_TRUE(cx_created_);

  // Very long module ID
  std::string long_id(1000, 'a');
  lumyn_error_t err = lumyn_RegisterModule(&cx_.base, long_id.c_str(), test_module_callback, nullptr);
  // Should succeed (no length limit specified in API)
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(ModuleAPITest, RegisterModuleWithSpecialCharacters)
{
  ASSERT_TRUE(cx_created_);

  // Module IDs with special characters
  const char *ids[] = {
      "module-with-dashes",
      "module_with_underscores",
      "module.with.dots",
      "module/with/slashes",
      "module:with:colons",
  };

  for (const char *id : ids)
  {
    lumyn_error_t err = lumyn_RegisterModule(&cx_.base, id, test_module_callback, nullptr);
    EXPECT_EQ(err, LUMYN_OK) << "Failed to register module with ID: " << id;
  }
}

// =============================================================================
// Module Registration Stress Tests
// =============================================================================

TEST_F(ModuleAPITest, ManyModulesCanBeRegistered)
{
  ASSERT_TRUE(cx_created_);

  const int NUM_MODULES = 50;

  for (int i = 0; i < NUM_MODULES; ++i)
  {
    std::string module_id = "module_" + std::to_string(i);
    lumyn_error_t err = lumyn_RegisterModule(&cx_.base, module_id.c_str(), test_module_callback, nullptr);
    EXPECT_EQ(err, LUMYN_OK) << "Failed to register module " << i;
  }
}

TEST_F(ModuleAPITest, RegisterUnregisterCycle)
{
  ASSERT_TRUE(cx_created_);

  const int CYCLES = 20;

  for (int i = 0; i < CYCLES; ++i)
  {
    EXPECT_EQ(lumyn_RegisterModule(&cx_.base, "cycle_module", test_module_callback, nullptr), LUMYN_OK)
        << "Cycle " << i << " register failed";
    EXPECT_EQ(lumyn_UnregisterModule(&cx_.base, "cycle_module"), LUMYN_OK)
        << "Cycle " << i << " unregister failed";
  }
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
