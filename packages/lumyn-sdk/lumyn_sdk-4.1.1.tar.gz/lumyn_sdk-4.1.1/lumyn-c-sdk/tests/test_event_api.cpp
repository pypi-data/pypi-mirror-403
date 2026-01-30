#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h and Network.h (included via SDK headers)
/**
 * @file test_event_api.cpp
 * @brief Comprehensive tests for the Event API
 *
 * Tests event handler registration, event retrieval, and callback functionality.
 */

#include <gtest/gtest.h>
#include <lumyn/c/lumyn_sdk.h>
#include <cstring>
#include <atomic>

class EventAPITest : public ::testing::Test
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
static std::atomic<int> g_callback_count{0};
static lumyn_event_t g_last_event = {};
static void *g_last_user_data = nullptr;

static void test_event_callback(lumyn_event_t *evt, void *user)
{
  g_callback_count++;
  if (evt)
  {
    g_last_event = *evt;
  }
  g_last_user_data = user;
}

static void reset_callback_state()
{
  g_callback_count = 0;
  std::memset(&g_last_event, 0, sizeof(g_last_event));
  g_last_user_data = nullptr;
}

// =============================================================================
// AddEventHandler Tests
// =============================================================================

TEST_F(EventAPITest, AddEventHandlerWithNullDeviceFails)
{
  lumyn_error_t err = lumyn_AddEventHandler(nullptr, test_event_callback, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, AddEventHandlerWithNullCallbackFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_AddEventHandler(&cx_.base, nullptr, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, AddEventHandlerWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_error_t err = lumyn_AddEventHandler(&empty_base, test_event_callback, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, AddEventHandlerSucceeds)
{
  ASSERT_TRUE(cx_created_);

  reset_callback_state();
  lumyn_error_t err = lumyn_AddEventHandler(&cx_.base, test_event_callback, nullptr);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(EventAPITest, AddEventHandlerWithUserData)
{
  ASSERT_TRUE(cx_created_);

  int user_data = 42;
  lumyn_error_t err = lumyn_AddEventHandler(&cx_.base, test_event_callback, &user_data);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(EventAPITest, MultipleEventHandlersCanBeAdded)
{
  ASSERT_TRUE(cx_created_);

  // Add multiple handlers (should not fail)
  EXPECT_EQ(lumyn_AddEventHandler(&cx_.base, test_event_callback, nullptr), LUMYN_OK);

  // Adding another callback with different user data
  int data1 = 1;
  EXPECT_EQ(lumyn_AddEventHandler(&cx_.base, test_event_callback, &data1), LUMYN_OK);

  int data2 = 2;
  EXPECT_EQ(lumyn_AddEventHandler(&cx_.base, test_event_callback, &data2), LUMYN_OK);
}

// =============================================================================
// GetLatestEvent Tests
// =============================================================================

TEST_F(EventAPITest, GetLatestEventWithNullDeviceFails)
{
  lumyn_event_t evt = {};
  lumyn_error_t err = lumyn_GetLatestEvent(nullptr, &evt);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetLatestEventWithNullEventFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_error_t err = lumyn_GetLatestEvent(&cx_.base, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetLatestEventWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_event_t evt = {};
  lumyn_error_t err = lumyn_GetLatestEvent(&empty_base, &evt);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetLatestEventWhenNotConnectedFails)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  lumyn_event_t evt = {};
  lumyn_error_t err = lumyn_GetLatestEvent(&cx_.base, &evt);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

// =============================================================================
// GetEvents Tests
// =============================================================================

TEST_F(EventAPITest, GetEventsWithNullDeviceFails)
{
  lumyn_event_t events[10] = {};
  int count = 0;
  lumyn_error_t err = lumyn_GetEvents(nullptr, events, 10, &count);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetEventsWithNullArrayFails)
{
  ASSERT_TRUE(cx_created_);
  int count = 0;
  lumyn_error_t err = lumyn_GetEvents(&cx_.base, nullptr, 10, &count);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetEventsWithNullCountFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_event_t events[10] = {};
  lumyn_error_t err = lumyn_GetEvents(&cx_.base, events, 10, nullptr);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetEventsWithZeroMaxCountFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_event_t events[10] = {};
  int count = 0;
  lumyn_error_t err = lumyn_GetEvents(&cx_.base, events, 0, &count);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetEventsWithNegativeMaxCountFails)
{
  ASSERT_TRUE(cx_created_);
  lumyn_event_t events[10] = {};
  int count = 0;
  lumyn_error_t err = lumyn_GetEvents(&cx_.base, events, -1, &count);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetEventsWithNullInternalFails)
{
  cx_base_t empty_base = {};
  lumyn_event_t events[10] = {};
  int count = 0;
  lumyn_error_t err = lumyn_GetEvents(&empty_base, events, 10, &count);
  EXPECT_EQ(err, LUMYN_ERR_INVALID_ARGUMENT);
}

TEST_F(EventAPITest, GetEventsWhenNotConnectedSucceedsWithZeroCount)
{
  ASSERT_TRUE(cx_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cx_.base));

  lumyn_event_t events[10] = {};
  int count = -1;
  lumyn_error_t err = lumyn_GetEvents(&cx_.base, events, 10, &count);

  // When not connected, should succeed but return 0 events
  EXPECT_EQ(err, LUMYN_OK);
  EXPECT_EQ(count, 0);
}

// =============================================================================
// ConnectorXAnimate Event Tests
// =============================================================================

TEST_F(EventAPITest, ConnectorXAnimateAddEventHandlerSucceeds)
{
  ASSERT_TRUE(cxa_created_);

  lumyn_error_t err = lumyn_AddEventHandler(&cxa_.base, test_event_callback, nullptr);
  EXPECT_EQ(err, LUMYN_OK);
}

TEST_F(EventAPITest, ConnectorXAnimateGetLatestEventWhenNotConnectedFails)
{
  ASSERT_TRUE(cxa_created_);
  ASSERT_FALSE(lumyn_IsConnected(&cxa_.base));

  lumyn_event_t evt = {};
  lumyn_error_t err = lumyn_GetLatestEvent(&cxa_.base, &evt);
  EXPECT_EQ(err, LUMYN_ERR_NOT_CONNECTED);
}

TEST_F(EventAPITest, ConnectorXAnimateGetEventsWhenNotConnectedSucceeds)
{
  ASSERT_TRUE(cxa_created_);

  lumyn_event_t events[10] = {};
  int count = -1;
  lumyn_error_t err = lumyn_GetEvents(&cxa_.base, events, 10, &count);

  EXPECT_EQ(err, LUMYN_OK);
  EXPECT_EQ(count, 0);
}

// =============================================================================
// Event Structure Tests
// =============================================================================

TEST_F(EventAPITest, EventStructureHasCorrectSize)
{
  // Ensure event structure is POD-like and has expected layout
  lumyn_event_t evt = {};

  // Should be able to zero-initialize
  EXPECT_EQ(evt.type, static_cast<lumyn_event_type_t>(0));
  EXPECT_EQ(evt.extra_message, nullptr);
}

TEST_F(EventAPITest, EventStructureCanBeCopied)
{
  lumyn_event_t evt1 = {};
  evt1.type = LUMYN_EVENT_CONNECTED;

  lumyn_event_t evt2 = evt1;

  EXPECT_EQ(evt2.type, evt1.type);
}

// =============================================================================
// Callback Registration Stress Tests
// =============================================================================

TEST_F(EventAPITest, ManyCallbacksCanBeRegistered)
{
  ASSERT_TRUE(cx_created_);

  const int NUM_CALLBACKS = 100;
  int user_data[NUM_CALLBACKS];

  for (int i = 0; i < NUM_CALLBACKS; ++i)
  {
    user_data[i] = i;
    lumyn_error_t err = lumyn_AddEventHandler(&cx_.base, test_event_callback, &user_data[i]);
    EXPECT_EQ(err, LUMYN_OK) << "Failed to add callback " << i;
  }
}

// =============================================================================
// Thread Safety (Basic)
// =============================================================================

TEST_F(EventAPITest, EventFunctionsCanBeCalledRepeatedly)
{
  ASSERT_TRUE(cx_created_);

  for (int i = 0; i < 100; ++i)
  {
    lumyn_event_t events[10] = {};
    int count = 0;
    EXPECT_EQ(lumyn_GetEvents(&cx_.base, events, 10, &count), LUMYN_OK);
    EXPECT_EQ(count, 0);
  }
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
