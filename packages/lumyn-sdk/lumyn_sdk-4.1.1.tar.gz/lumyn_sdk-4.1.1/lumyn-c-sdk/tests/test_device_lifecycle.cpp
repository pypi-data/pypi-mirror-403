#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_device_lifecycle.cpp
 * @brief Comprehensive tests for device creation and destruction
 *
 * Tests the full lifecycle of ConnectorX and ConnectorXAnimate devices,
 * including stack and heap allocation patterns, and proper cleanup.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <vector>
#include <memory>

class DeviceLifecycleTest : public ::testing::Test
{
protected:
  void SetUp() override {}
  void TearDown() override {}
};

// =============================================================================
// ConnectorX Stack Allocation Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, CreateConnectorXStackAllocationSucceeds)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to create ConnectorX: " << Lumyn_ErrorString(err);

  // Internal pointer should be set
  EXPECT_NE(cx.base._internal, nullptr) << "Internal state not initialized";

  lumyn_DestroyConnectorX(&cx);
}

TEST_F(DeviceLifecycleTest, CreateConnectorXWithNullPointerFails)
{
  lumyn_error_t err = lumyn_CreateConnectorX(nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT)
      << "Expected INVALID_ARGUMENT for NULL pointer";
}

TEST_F(DeviceLifecycleTest, DestroyConnectorXWithNullPointerIsSafe)
{
  // Should not crash
  lumyn_DestroyConnectorX(nullptr);
  SUCCEED() << "DestroyConnectorX(nullptr) did not crash";
}

TEST_F(DeviceLifecycleTest, DestroyConnectorXClearsInternalState)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  ASSERT_EQ(err, LUMYN_OK);

  void *internal_before = cx.base._internal;
  EXPECT_NE(internal_before, nullptr);

  lumyn_DestroyConnectorX(&cx);

  EXPECT_EQ(cx.base._internal, nullptr) << "Internal pointer not cleared after destroy";
  EXPECT_EQ(cx.base._vtable, nullptr) << "VTable not cleared after destroy";
}

TEST_F(DeviceLifecycleTest, DoubleDestroyConnectorXIsSafe)
{
  cx_t cx = {};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  ASSERT_EQ(err, LUMYN_OK);

  lumyn_DestroyConnectorX(&cx);
  lumyn_DestroyConnectorX(&cx); // Should not crash

  SUCCEED() << "Double destroy did not crash";
}

// =============================================================================
// ConnectorX Heap Allocation Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, CreateConnectorXAllocSucceeds)
{
  cx_t *cx = nullptr;
  lumyn_error_t err = lumyn_CreateConnectorXAlloc(&cx);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to allocate ConnectorX: " << Lumyn_ErrorString(err);
  ASSERT_NE(cx, nullptr) << "ConnectorX pointer is NULL after successful allocation";

  EXPECT_NE(cx->base._internal, nullptr) << "Internal state not initialized";

  lumyn_DestroyConnectorXAlloc(cx);
}

TEST_F(DeviceLifecycleTest, CreateConnectorXAllocWithNullOutputFails)
{
  lumyn_error_t err = lumyn_CreateConnectorXAlloc(nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT)
      << "Expected INVALID_ARGUMENT for NULL output pointer";
}

TEST_F(DeviceLifecycleTest, DestroyConnectorXAllocWithNullIsSafe)
{
  lumyn_DestroyConnectorXAlloc(nullptr);
  SUCCEED() << "DestroyConnectorXAlloc(nullptr) did not crash";
}

// =============================================================================
// ConnectorXAnimate Stack Allocation Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, CreateConnectorXAnimateStackAllocationSucceeds)
{
  cx_animate_t cxa = {};
  lumyn_error_t err = lumyn_CreateConnectorXAnimate(&cxa);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to create ConnectorXAnimate: " << Lumyn_ErrorString(err);

  EXPECT_NE(cxa.base._internal, nullptr) << "Internal state not initialized";

  lumyn_DestroyConnectorXAnimate(&cxa);
}

TEST_F(DeviceLifecycleTest, CreateConnectorXAnimateWithNullPointerFails)
{
  lumyn_error_t err = lumyn_CreateConnectorXAnimate(nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT)
      << "Expected INVALID_ARGUMENT for NULL pointer";
}

TEST_F(DeviceLifecycleTest, DestroyConnectorXAnimateWithNullPointerIsSafe)
{
  lumyn_DestroyConnectorXAnimate(nullptr);
  SUCCEED() << "DestroyConnectorXAnimate(nullptr) did not crash";
}

TEST_F(DeviceLifecycleTest, DestroyConnectorXAnimateClearsInternalState)
{
  cx_animate_t cxa = {};
  lumyn_error_t err = lumyn_CreateConnectorXAnimate(&cxa);
  ASSERT_EQ(err, LUMYN_OK);

  lumyn_DestroyConnectorXAnimate(&cxa);

  EXPECT_EQ(cxa.base._internal, nullptr) << "Internal pointer not cleared after destroy";
  EXPECT_EQ(cxa.base._vtable, nullptr) << "VTable not cleared after destroy";
}

// =============================================================================
// ConnectorXAnimate Heap Allocation Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, CreateConnectorXAnimateAllocSucceeds)
{
  cx_animate_t *cxa = nullptr;
  lumyn_error_t err = lumyn_CreateConnectorXAnimateAlloc(&cxa);
  ASSERT_EQ(err, LUMYN_OK) << "Failed to allocate ConnectorXAnimate: " << Lumyn_ErrorString(err);
  ASSERT_NE(cxa, nullptr) << "ConnectorXAnimate pointer is NULL after successful allocation";

  EXPECT_NE(cxa->base._internal, nullptr) << "Internal state not initialized";

  lumyn_DestroyConnectorXAnimateAlloc(cxa);
}

TEST_F(DeviceLifecycleTest, CreateConnectorXAnimateAllocWithNullOutputFails)
{
  lumyn_error_t err = lumyn_CreateConnectorXAnimateAlloc(nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT)
      << "Expected INVALID_ARGUMENT for NULL output pointer";
}

TEST_F(DeviceLifecycleTest, DestroyConnectorXAnimateAllocWithNullIsSafe)
{
  lumyn_DestroyConnectorXAnimateAlloc(nullptr);
  SUCCEED() << "DestroyConnectorXAnimateAlloc(nullptr) did not crash";
}

// =============================================================================
// Multiple Instance Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, MultipleConnectorXInstancesCanCoexist)
{
  cx_t cx1 = {}, cx2 = {}, cx3 = {};

  ASSERT_EQ(lumyn_CreateConnectorX(&cx1), LUMYN_OK);
  ASSERT_EQ(lumyn_CreateConnectorX(&cx2), LUMYN_OK);
  ASSERT_EQ(lumyn_CreateConnectorX(&cx3), LUMYN_OK);

  // All should have different internal pointers
  EXPECT_NE(cx1.base._internal, cx2.base._internal);
  EXPECT_NE(cx2.base._internal, cx3.base._internal);
  EXPECT_NE(cx1.base._internal, cx3.base._internal);

  lumyn_DestroyConnectorX(&cx3);
  lumyn_DestroyConnectorX(&cx2);
  lumyn_DestroyConnectorX(&cx1);
}

TEST_F(DeviceLifecycleTest, MixedDeviceTypesCanCoexist)
{
  cx_t cx = {};
  cx_animate_t cxa = {};

  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);
  ASSERT_EQ(lumyn_CreateConnectorXAnimate(&cxa), LUMYN_OK);

  // Different internal pointers
  EXPECT_NE(cx.base._internal, cxa.base._internal);

  lumyn_DestroyConnectorXAnimate(&cxa);
  lumyn_DestroyConnectorX(&cx);
}

TEST_F(DeviceLifecycleTest, ManyHeapAllocatedDevicesCanBeCreated)
{
  std::vector<cx_t *> devices;
  const int NUM_DEVICES = 10;

  for (int i = 0; i < NUM_DEVICES; ++i)
  {
    cx_t *cx = nullptr;
    lumyn_error_t err = lumyn_CreateConnectorXAlloc(&cx);
    ASSERT_EQ(err, LUMYN_OK) << "Failed to create device " << i;
    ASSERT_NE(cx, nullptr);
    devices.push_back(cx);
  }

  // Verify all have unique internal pointers
  for (size_t i = 0; i < devices.size(); ++i)
  {
    for (size_t j = i + 1; j < devices.size(); ++j)
    {
      EXPECT_NE(devices[i]->base._internal, devices[j]->base._internal)
          << "Devices " << i << " and " << j << " share internal pointer";
    }
  }

  // Clean up
  for (cx_t *cx : devices)
  {
    lumyn_DestroyConnectorXAlloc(cx);
  }
}

// =============================================================================
// LUMYN_BASE_PTR Macro Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, LumynBasePtrMacroWorksForConnectorX)
{
  cx_t cx = {};
  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);

  cx_base_t *base = LUMYN_BASE_PTR(&cx);
  EXPECT_EQ(base, &cx.base);
  EXPECT_EQ(base->_internal, cx.base._internal);

  lumyn_DestroyConnectorX(&cx);
}

TEST_F(DeviceLifecycleTest, LumynBasePtrMacroWorksForConnectorXAnimate)
{
  cx_animate_t cxa = {};
  ASSERT_EQ(lumyn_CreateConnectorXAnimate(&cxa), LUMYN_OK);

  cx_base_t *base = LUMYN_BASE_PTR(&cxa);
  EXPECT_EQ(base, &cxa.base);
  EXPECT_EQ(base->_internal, cxa.base._internal);

  lumyn_DestroyConnectorXAnimate(&cxa);
}

// =============================================================================
// Re-initialization Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, ReinitializingDestroyedDeviceSucceeds)
{
  cx_t cx = {};

  // First creation
  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);
  lumyn_DestroyConnectorX(&cx);

  // Re-initialize the same struct
  std::memset(&cx, 0, sizeof(cx));
  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);

  // Should have valid internal pointer (address may be reused by allocator)
  EXPECT_NE(cx.base._internal, nullptr);

  lumyn_DestroyConnectorX(&cx);
}

// =============================================================================
// Initial State Tests
// =============================================================================

TEST_F(DeviceLifecycleTest, NewConnectorXIsNotConnected)
{
  cx_t cx = {};
  ASSERT_EQ(lumyn_CreateConnectorX(&cx), LUMYN_OK);

  EXPECT_FALSE(lumyn_IsConnected(&cx.base)) << "New device should not be connected";

  lumyn_DestroyConnectorX(&cx);
}

TEST_F(DeviceLifecycleTest, NewConnectorXAnimateIsNotConnected)
{
  cx_animate_t cxa = {};
  ASSERT_EQ(lumyn_CreateConnectorXAnimate(&cxa), LUMYN_OK);

  EXPECT_FALSE(lumyn_IsConnected(&cxa.base)) << "New device should not be connected";

  lumyn_DestroyConnectorXAnimate(&cxa);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
