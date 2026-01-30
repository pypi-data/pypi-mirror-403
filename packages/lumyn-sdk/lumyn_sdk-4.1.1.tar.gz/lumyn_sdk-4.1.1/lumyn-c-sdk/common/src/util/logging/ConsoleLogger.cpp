#include "lumyn/Constants.h"
#include "lumyn/util/logging/ConsoleLogger.h"

#include <cstdio>
#include <cstring>
#include <string>

namespace lumyn::internal {

void ConsoleLogger::vlog(Constants::Logging::Level level, const char* key,
                         const char* fmt, va_list ap) {
  if (!shouldLog(level)) return;

  #ifdef TP_USE_FREERTOS
  char msg[BUF];
  char full[BUF];

  // user message
  vsnprintf(msg, sizeof(msg), fmt, ap);

  // prefix "(key) "
  snprintf(full, sizeof(full), "(%s) %s", key ? key : "", msg);

  if (logFunc) {
    logFunc(level, full);
    return;
  }

  printf("%s[%s] %s\n", Constants::Logging::kLogPrefix, levelToString(level), full);
  #else
    char buf[512];
    vsnprintf(buf, sizeof(buf), fmt, ap);

    std::string full;
    full.reserve(64 + strlen(buf));

    full += Constants::Logging::kLogPrefix;
    full += levelToString(level);
    full += " - ";
    if (key) full += key;
    full += ": ";
    full += buf;

    if (logFunc) {
      logFunc(level, full.c_str());
      return;
    }

    fputs(full.c_str(), stdout);
    fputc('\n', stdout);
  #endif
}

// ------------------------- Format versions -------------------------

void ConsoleLogger::logVerbose(const char* key, const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  vlog(Constants::Logging::Level::VERBOSE, key, fmt, ap);
  va_end(ap);
}

void ConsoleLogger::logInfo(const char* key, const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  vlog(Constants::Logging::Level::INFO, key, fmt, ap);
  va_end(ap);
}

void ConsoleLogger::logWarning(const char* key, const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  vlog(Constants::Logging::Level::WARNING, key, fmt, ap);
  va_end(ap);
}

void ConsoleLogger::logError(const char* key, const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  vlog(Constants::Logging::Level::ERROR, key, fmt, ap);
  va_end(ap);
}

void ConsoleLogger::logFatal(const char* key, const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  vlog(Constants::Logging::Level::FATAL, key, fmt, ap);
  va_end(ap);
}

// ------------------------- int -------------------------

void ConsoleLogger::logVerbose(const char* key, int v) {
  if (!shouldLog(Constants::Logging::Level::VERBOSE)) return;
  printf("%s%s - %s: %d\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::VERBOSE), key, v);
}

void ConsoleLogger::logInfo(const char* key, int v) {
  if (!shouldLog(Constants::Logging::Level::INFO)) return;
  printf("%s%s - %s: %d\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::INFO), key, v);
}

void ConsoleLogger::logWarning(const char* key, int v) {
  if (!shouldLog(Constants::Logging::Level::WARNING)) return;
  printf("%s%s - %s: %d\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::WARNING), key, v);
}

void ConsoleLogger::logError(const char* key, int v) {
  if (!shouldLog(Constants::Logging::Level::ERROR)) return;
  printf("%s%s - %s: %d\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::ERROR), key, v);
}

void ConsoleLogger::logFatal(const char* key, int v) {
  if (!shouldLog(Constants::Logging::Level::FATAL)) return;
  printf("%s%s - %s: %d\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::FATAL), key, v);
}

// ------------------------- double -------------------------

void ConsoleLogger::logVerbose(const char* key, double v) {
  if (!shouldLog(Constants::Logging::Level::VERBOSE)) return;
  printf("%s%s - %s: %.3f\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::VERBOSE), key, v);
}

void ConsoleLogger::logInfo(const char* key, double v) {
  if (!shouldLog(Constants::Logging::Level::INFO)) return;
  printf("%s%s - %s: %.3f\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::INFO), key, v);
}

void ConsoleLogger::logWarning(const char* key, double v) {
  if (!shouldLog(Constants::Logging::Level::WARNING)) return;
  printf("%s%s - %s: %.3f\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::WARNING), key, v);
}

void ConsoleLogger::logError(const char* key, double v) {
  if (!shouldLog(Constants::Logging::Level::ERROR)) return;
  printf("%s%s - %s: %.3f\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::ERROR), key, v);
}

void ConsoleLogger::logFatal(const char* key, double v) {
  if (!shouldLog(Constants::Logging::Level::FATAL)) return;
  printf("%s%s - %s: %.3f\n", Constants::Logging::kLogPrefix, 
         levelToString(Constants::Logging::Level::FATAL), key, v);
}

}  // namespace lumyn::internal
