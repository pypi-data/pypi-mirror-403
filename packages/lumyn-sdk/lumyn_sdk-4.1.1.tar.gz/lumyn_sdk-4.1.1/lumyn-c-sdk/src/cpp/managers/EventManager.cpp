#include "lumyn/cpp/EventManager.h"

#include <algorithm>
#include <cstring>

namespace lumyn
{
  namespace managers
  {

    EventManager::EventManager(cx_base_t *base) : base_(base) {}

    EventManager::~EventManager()
    {
      // No unregister API available in C ABI; handlers will remain registered until device destruction
    }

    lumyn_error_t EventManager::AddEventHandler(std::function<void(const lumyn_event_t &)> handler)
    {
      if (!base_)
        return LUMYN_ERR_INVALID_ARGUMENT;
      {
        std::lock_guard<std::mutex> lock(handlers_mutex_);
        handlers_.push_back(std::move(handler));
      }
      if (!registered_)
      {
        lumyn_error_t res = lumyn_AddEventHandler(base_, &EventManager::c_event_callback, this);
        if (res != LUMYN_OK)
          return res;
        registered_ = true;
      }
      return LUMYN_OK;
    }

    lumyn_error_t EventManager::GetLatestEvent(lumyn_event_t &out_event)
    {
      if (!base_)
        return LUMYN_ERR_INVALID_ARGUMENT;
      return lumyn_GetLatestEvent(base_, &out_event);
    }

    std::optional<lumyn_event_t> EventManager::GetLatestEvent()
    {
      if (!base_)
        return std::nullopt;
      lumyn_event_t evt{};
      if (lumyn_GetLatestEvent(base_, &evt) != LUMYN_OK)
        return std::nullopt;
      return evt;
    }

    std::vector<lumyn_event_t> EventManager::GetEvents()
    {
      std::vector<lumyn_event_t> out;
      if (!base_)
        return out;
      const int MAX_EVENTS = 64;
      lumyn_event_t arr[MAX_EVENTS];
      int count = 0;
      lumyn_error_t res = lumyn_GetEvents(base_, arr, MAX_EVENTS, &count);
      if (res != LUMYN_OK || count <= 0)
        return out;
      for (int i = 0; i < count; ++i)
      {
        out.emplace_back(arr[i]);
      }
      return out;
    }

    void EventManager::c_event_callback(lumyn_event_t *evt, void *user)
    {
      if (!evt || !user)
        return;
      auto *self = static_cast<EventManager *>(user);
      (void)self; // silence unused warnings in the rare case
      // Make a safe copy of C event (deep copy for extra_message string)
      lumyn_event_t local = *evt;
      if (evt->extra_message)
      {
        local.extra_message = strdup(evt->extra_message);
      }

      // Dispatch to handlers
      std::vector<std::function<void(const lumyn_event_t &)>> handlers_call;
      {
        std::lock_guard<std::mutex> lock(self->handlers_mutex_);
        handlers_call = self->handlers_;
      }

      for (auto &h : handlers_call)
      {
        try
        {
          h(local);
        }
        catch (...)
        {
          // swallow
        }
      }

      // Free duplicated extra_message
      if (local.extra_message)
        free((void *)local.extra_message);
    }

  } // namespace managers
} // namespace lumyn
