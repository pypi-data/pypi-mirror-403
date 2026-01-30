#pragma once

#include <cstdarg>
#include <cstdio>
#include <functional>

#include "lumyn/util/logging/ILogger.h"

namespace lumyn::internal {

class ConsoleLogger : public ILogger {
 public:
  static ConsoleLogger& getInstance() {
    static ConsoleLogger instance;
    return instance;
  }

  // string+fmt
  void logVerbose(const char* key, const char* fmt, ...) override;
  void logInfo(const char* key, const char* fmt, ...) override;
  void logWarning(const char* key, const char* fmt, ...) override;
  void logError(const char* key, const char* fmt, ...) override;
  void logFatal(const char* key, const char* fmt, ...) override;

  // int
  void logVerbose(const char* key, int v) override;
  void logInfo(const char* key, int v) override;
  void logWarning(const char* key, int v) override;
  void logError(const char* key, int v) override;
  void logFatal(const char* key, int v) override;

  // double
  void logVerbose(const char* key, double v) override;
  void logInfo(const char* key, double v) override;
  void logWarning(const char* key, double v) override;
  void logError(const char* key, double v) override;
  void logFatal(const char* key, double v) override;

  void setLogFunction(
      std::function<void(Constants::Logging::Level, const char*)> func) {
    logFunc = func;
  }

 private:
  ConsoleLogger() = default;

  #ifdef TP_USE_FREERTOS
  static constexpr size_t BUF = 256;
  #else
  static constexpr size_t BUF = 512;
  #endif
  void vlog(Constants::Logging::Level level, const char* key, const char* fmt,
            va_list ap);

  std::function<void(Constants::Logging::Level, const char*)> logFunc;
};

}  // namespace lumyn::internal
