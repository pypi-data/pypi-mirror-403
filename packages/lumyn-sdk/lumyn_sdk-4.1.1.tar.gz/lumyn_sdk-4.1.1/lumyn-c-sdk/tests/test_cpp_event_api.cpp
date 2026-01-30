/**
 * @file test_cpp_event_api.cpp
 * @brief Tests for C++ SDK event handling
 *
 * Tests event handlers, polling, and event retrieval.
 */

#include <lumyn/Constants.h> // Required by SDK headers
#include <gtest/gtest.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>
#include <lumyn/cpp/types.hpp>

// =============================================================================
// ConnectorX Event Tests
// =============================================================================

class CppConnectorXEventTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorX cx_;
};

TEST_F(CppConnectorXEventTest, AddEventHandlerWithValidCallback)
{
  bool called = false;
  auto err = cx_.AddEventHandler([&called](const lumyn::Event &evt)
                                 {
    called = true;
    (void)evt; });
  // AddEventHandler may succeed or return LUMYN_ERR_NOT_CONNECTED when disconnected
  // depending on implementation. We just verify it doesn't crash.
  (void)err;
  SUCCEED();
}

TEST_F(CppConnectorXEventTest, AddMultipleEventHandlers)
{
  int count = 0;
  auto handler = [&count](const lumyn::Event &)
  { count++; };

  // AddEventHandler may succeed or fail when disconnected - we test it doesn't crash
  cx_.AddEventHandler(handler);
  cx_.AddEventHandler(handler);
  cx_.AddEventHandler(handler);
  SUCCEED();
}

TEST_F(CppConnectorXEventTest, GetLatestEventReturnsNulloptWhenDisconnected)
{
  auto evt = cx_.GetLatestEvent();
  EXPECT_FALSE(evt.has_value());
}

TEST_F(CppConnectorXEventTest, GetLatestEventWithOutParamFailsWhenDisconnected)
{
  lumyn_event_t evt{};
  auto err = cx_.GetLatestEvent(evt);
  EXPECT_NE(err, LUMYN_OK);
}

TEST_F(CppConnectorXEventTest, GetEventsReturnsEmptyWhenDisconnected)
{
  auto events = cx_.GetEvents();
  EXPECT_TRUE(events.empty());
}

TEST_F(CppConnectorXEventTest, SetAutoPollEventsTrue)
{
  cx_.SetAutoPollEvents(true);
  SUCCEED();
}

TEST_F(CppConnectorXEventTest, SetAutoPollEventsFalse)
{
  cx_.SetAutoPollEvents(false);
  SUCCEED();
}

TEST_F(CppConnectorXEventTest, SetAutoPollEventsToggle)
{
  cx_.SetAutoPollEvents(true);
  cx_.SetAutoPollEvents(false);
  cx_.SetAutoPollEvents(true);
  SUCCEED();
}

TEST_F(CppConnectorXEventTest, PollEventsDoesNotCrashWhenDisconnected)
{
  cx_.PollEvents();
  SUCCEED();
}

TEST_F(CppConnectorXEventTest, PollEventsMultipleTimes)
{
  cx_.PollEvents();
  cx_.PollEvents();
  cx_.PollEvents();
  SUCCEED();
}

// =============================================================================
// ConnectorXAnimate Event Tests
// =============================================================================

class CppConnectorXAnimateEventTest : public ::testing::Test
{
protected:
  lumyn::device::ConnectorXAnimate cxa_;
};

TEST_F(CppConnectorXAnimateEventTest, AddEventHandler)
{
  auto err = cxa_.AddEventHandler([](const lumyn::Event &) {});
  // May succeed or fail when disconnected - just verify it doesn't crash
  (void)err;
  SUCCEED();
}

TEST_F(CppConnectorXAnimateEventTest, GetLatestEventReturnsNullopt)
{
  auto evt = cxa_.GetLatestEvent();
  EXPECT_FALSE(evt.has_value());
}

TEST_F(CppConnectorXAnimateEventTest, GetEventsReturnsEmpty)
{
  auto events = cxa_.GetEvents();
  EXPECT_TRUE(events.empty());
}

TEST_F(CppConnectorXAnimateEventTest, SetAutoPollEvents)
{
  cxa_.SetAutoPollEvents(true);
  cxa_.SetAutoPollEvents(false);
  SUCCEED();
}

TEST_F(CppConnectorXAnimateEventTest, PollEvents)
{
  cxa_.PollEvents();
  SUCCEED();
}

// =============================================================================
// Event Type Wrapper Tests
// =============================================================================

TEST(EventWrapperTest, DefaultConstruction)
{
  lumyn::Event evt;
  SUCCEED();
}

TEST(EventWrapperTest, ConstructFromCEvent)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_CONNECTED;
  lumyn::Event evt(c_evt);
  EXPECT_EQ(evt.getType(), LUMYN_EVENT_CONNECTED);
}

TEST(EventWrapperTest, CopyConstruction)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_DISCONNECTED;
  lumyn::Event evt1(c_evt);
  lumyn::Event evt2(evt1);
  EXPECT_EQ(evt2.getType(), LUMYN_EVENT_DISCONNECTED);
}

TEST(EventWrapperTest, CopyAssignment)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_ENABLED;
  lumyn::Event evt1(c_evt);
  lumyn::Event evt2;
  evt2 = evt1;
  EXPECT_EQ(evt2.getType(), LUMYN_EVENT_ENABLED);
}

TEST(EventWrapperTest, MoveConstruction)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_DISABLED;
  lumyn::Event evt1(c_evt);
  lumyn::Event evt2(std::move(evt1));
  EXPECT_EQ(evt2.getType(), LUMYN_EVENT_DISABLED);
}

TEST(EventWrapperTest, MoveAssignment)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_HEARTBEAT;
  lumyn::Event evt1(c_evt);
  lumyn::Event evt2;
  evt2 = std::move(evt1);
  EXPECT_EQ(evt2.getType(), LUMYN_EVENT_HEARTBEAT);
}

TEST(EventWrapperTest, IsErrorChecker)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_ERROR;
  lumyn::Event evt(c_evt);
  EXPECT_TRUE(evt.isError());
  EXPECT_FALSE(evt.isConnected());
  EXPECT_FALSE(evt.isDisconnected());
}

TEST(EventWrapperTest, IsConnectedChecker)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_CONNECTED;
  lumyn::Event evt(c_evt);
  EXPECT_TRUE(evt.isConnected());
  EXPECT_FALSE(evt.isError());
  EXPECT_FALSE(evt.isDisconnected());
}

TEST(EventWrapperTest, IsDisconnectedChecker)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_DISCONNECTED;
  lumyn::Event evt(c_evt);
  EXPECT_TRUE(evt.isDisconnected());
  EXPECT_FALSE(evt.isError());
  EXPECT_FALSE(evt.isConnected());
}

TEST(EventWrapperTest, GetData)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_HEARTBEAT;
  c_evt.data.heartbeat.enabled = 1;
  lumyn::Event evt(c_evt);
  EXPECT_EQ(evt.getData().heartbeat.enabled, 1);
}

TEST(EventWrapperTest, GetExtraMessageNull)
{
  lumyn_event_t c_evt{};
  c_evt.type = LUMYN_EVENT_ERROR;
  c_evt.extra_message = nullptr;
  lumyn::Event evt(c_evt);
  EXPECT_EQ(evt.getExtraMessage(), nullptr);
}

int main(int argc, char **argv)
{
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
