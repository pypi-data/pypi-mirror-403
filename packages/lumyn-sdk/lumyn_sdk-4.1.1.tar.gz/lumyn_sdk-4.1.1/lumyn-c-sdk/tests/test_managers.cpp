#include <gtest/gtest.h>

#include <lumyn/cpp/ConfigManager.h>
#include <lumyn/cpp/EventManager.h>

TEST(Managers, ConfigManagerNullBase)
{
  lumyn::managers::ConfigManager cfg(nullptr);
  std::string out;
  EXPECT_EQ(cfg.RequestConfig(out), LUMYN_ERR_INVALID_ARGUMENT);
  char *p = nullptr;
  EXPECT_EQ(cfg.RequestConfigAlloc(&p), LUMYN_ERR_INVALID_ARGUMENT);
}

TEST(Managers, EventManagerNullBase)
{
  lumyn::managers::EventManager evt(nullptr);
  lumyn_event_t e{};
  EXPECT_EQ(evt.GetLatestEvent(e), LUMYN_ERR_INVALID_ARGUMENT);
  EXPECT_FALSE(evt.GetLatestEvent().has_value());
  EXPECT_TRUE(evt.GetEvents().empty());
  EXPECT_EQ(evt.AddEventHandler([](const lumyn_event_t &) {}), LUMYN_ERR_INVALID_ARGUMENT);
}
