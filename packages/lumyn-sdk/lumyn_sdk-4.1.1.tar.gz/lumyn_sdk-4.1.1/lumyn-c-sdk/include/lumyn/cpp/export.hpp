#pragma once

#if defined(_WIN32) || defined(__CYGWIN__)
  #if defined(LUMYN_SDK_CPP_BUILDING)
    #define LUMYN_SDK_CPP_API __declspec(dllexport)
  #else
    #define LUMYN_SDK_CPP_API __declspec(dllimport)
  #endif
#else
  #if defined(__GNUC__) && __GNUC__ >= 4
    #define LUMYN_SDK_CPP_API __attribute__((visibility("default")))
  #else
    #define LUMYN_SDK_CPP_API
  #endif
#endif
