cmake_minimum_required(VERSION 3.16)

project(LumynSDK 
    VERSION 1.0.0
    DESCRIPTION "Lumyn Labs Common SDK - Core C++ library for Lumyn devices"
    LANGUAGES CXX
)

# C++ standard - C++20 required for designated initializers
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Find source files - only from common/src (shared protocol/base utilities)
# Device classes are compiled into the top-level SDK targets, not the common library
file(GLOB_RECURSE LUMYN_SOURCES "src/*.cpp")
file(GLOB_RECURSE LUMYN_HEADERS "include/*.h")

# Create static library
add_library(LumynSDK STATIC ${LUMYN_SOURCES} ${LUMYN_HEADERS})

# Include directories
target_include_directories(LumynSDK
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_BINARY_DIR}/../generated/include
        ${CMAKE_CURRENT_SOURCE_DIR}/../include
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Fetch and link nlohmann/json for JSON configuration support
include(FetchContent)

# Set policy for DOWNLOAD_EXTRACT_TIMESTAMP if CMake >= 3.24
if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()

FetchContent_Declare(
    nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
    URL_HASH SHA256=d6c65aca6b1ed68e7a182f4757257b107ae403032760ed6ef121c9d55e81757d
)
FetchContent_MakeAvailable(nlohmann_json)
target_link_libraries(LumynSDK PUBLIC nlohmann_json::nlohmann_json)

# Define export macros so that LUMYN_SDK_API and LUMYN_SDK_CPP_API resolve to
# dllexport when building (rather than dllimport). The common library is linked
# statically into the final DLLs, so these symbols are ultimately exported.
target_compile_definitions(LumynSDK PRIVATE LUMYN_SDK_BUILDING=1)
target_compile_definitions(LumynSDK PRIVATE LUMYN_SDK_CPP_BUILDING=1)

# Compiler features
target_compile_features(LumynSDK PUBLIC cxx_std_20)