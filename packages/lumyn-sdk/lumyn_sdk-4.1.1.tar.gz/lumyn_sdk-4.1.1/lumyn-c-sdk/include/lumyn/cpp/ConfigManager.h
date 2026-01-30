#pragma once

#include <string>
#include <cstdint>

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

    class LUMYN_MANAGERS_EXPORT ConfigManager
    {
    public:
      explicit ConfigManager(cx_base_t *base);

      // Request configuration into a std::string
      lumyn_error_t RequestConfig(std::string &out_json, uint32_t timeout_ms = 1000);

      // Request configuration and return allocated string (caller must free via lumyn_FreeString)
      lumyn_error_t RequestConfigAlloc(char **out, uint32_t timeout_ms = 1000);

      // Not yet implemented server-side
      lumyn_error_t SetConfig(const std::string & /*config_json*/);

    private:
      cx_base_t *base_;
    };

  } // namespace managers
} // namespace lumyn
