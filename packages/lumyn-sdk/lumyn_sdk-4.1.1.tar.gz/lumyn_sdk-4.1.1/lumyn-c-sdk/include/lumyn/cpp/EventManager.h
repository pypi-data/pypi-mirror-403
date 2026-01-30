#pragma once

#include <functional>
#include <mutex>
#include <vector>
#include <optional>

extern "C"
{
#include <lumyn/c/lumyn_sdk.h>
}

// Cross-platform DLL export macro
#ifdef _WIN32
#define LUMYN_MANAGERS_EXPORT __declspec(dllexport)
#else
#define LUMYN_MANAGERS_EXPORT __attribute__((visibility("default")))
#endif

namespace lumyn
{
  namespace managers
  {

    class LUMYN_MANAGERS_EXPORT EventManager
    {
    public:
      explicit EventManager(cx_base_t *base);
      ~EventManager();

      // Add a handler that receives C event structs
      lumyn_error_t AddEventHandler(std::function<void(const lumyn_event_t &)> handler);

      // Get latest event via C ABI
      lumyn_error_t GetLatestEvent(lumyn_event_t &out_event);

      // Get latest event as optional C struct
      std::optional<lumyn_event_t> GetLatestEvent();

      // Get buffered events
      std::vector<lumyn_event_t> GetEvents();

    private:
      cx_base_t *base_;
      std::mutex handlers_mutex_;
      std::vector<std::function<void(const lumyn_event_t &)>> handlers_;
      bool registered_{false};

      static void c_event_callback(lumyn_event_t *evt, void *user);
    };

  } // namespace managers
} // namespace lumyn
