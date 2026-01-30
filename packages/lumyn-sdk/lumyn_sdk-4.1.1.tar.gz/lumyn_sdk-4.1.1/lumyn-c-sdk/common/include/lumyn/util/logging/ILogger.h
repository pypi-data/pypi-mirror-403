#pragma once

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

namespace lumyn::internal {

class ILogger {
 public:
  // string + variadic
  virtual void logVerbose(const char* key, const char* fmt, ...) = 0;
  virtual void logInfo(const char* key, const char* fmt, ...) = 0;
  virtual void logWarning(const char* key, const char* fmt, ...) = 0;
  virtual void logError(const char* key, const char* fmt, ...) = 0;
  virtual void logFatal(const char* key, const char* fmt, ...) = 0;

  // int
  virtual void logVerbose(const char* key, int v) = 0;
  virtual void logInfo(const char* key, int v) = 0;
  virtual void logWarning(const char* key, int v) = 0;
  virtual void logError(const char* key, int v) = 0;
  virtual void logFatal(const char* key, int v) = 0;

  // double
  virtual void logVerbose(const char* key, double v) = 0;
  virtual void logInfo(const char* key, double v) = 0;
  virtual void logWarning(const char* key, double v) = 0;
  virtual void logError(const char* key, double v) = 0;
  virtual void logFatal(const char* key, double v) = 0;

 protected:
  const char* levelToString(Constants::Logging::Level level) const {
    using L = Constants::Logging::Level;
    switch (level) {
      case L::VERBOSE:
        return "VERBOSE";
      case L::INFO:
        return "INFO";
      case L::WARNING:
        return "WARNING";
      case L::ERROR:
        return "ERROR";
      case L::FATAL:
        return "FATAL";
    }
    return "UNKNOWN";
  }

  inline bool shouldLog(Constants::Logging::Level level) {
    return static_cast<int>(level) >=
           static_cast<int>(Constants::Logging::kMinLogLevel);
  }
};

}  // namespace lumyn::internal
