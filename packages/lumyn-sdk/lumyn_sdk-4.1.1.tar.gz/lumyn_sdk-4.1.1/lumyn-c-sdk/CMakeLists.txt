cmake_minimum_required(VERSION 3.16)

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/version.txt" LUMYN_SDK_VERSION)
string(STRIP "${LUMYN_SDK_VERSION}" LUMYN_SDK_VERSION)

project(lumyn_sdk VERSION ${LUMYN_SDK_VERSION} LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(BUILD_SHARED_LIBS ON CACHE BOOL "Build shared libraries" FORCE)

option(LUMYN_SDK_ENABLE_BUILTIN_SERIAL "Build built-in cross-platform serial backend" ON)
option(LUMYN_SDK_BUILD_EXAMPLES "Build SDK examples" OFF)

find_package(Threads REQUIRED)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(GENERATED_INCLUDE_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated/include")
file(MAKE_DIRECTORY "${GENERATED_INCLUDE_DIR}/lumyn")
configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/cmake/version.h.in
  ${GENERATED_INCLUDE_DIR}/lumyn/sdk_version.h
  @ONLY
)
configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/cmake/version.hpp.in
  ${GENERATED_INCLUDE_DIR}/lumyn/sdk_version.hpp
  @ONLY
)

set(COMMON_DIR "${CMAKE_CURRENT_SOURCE_DIR}/common")
if(NOT EXISTS "${COMMON_DIR}/CMakeLists.txt")
  set(COMMON_DIR_FALLBACK "${CMAKE_CURRENT_SOURCE_DIR}/../common")
  if(EXISTS "${COMMON_DIR_FALLBACK}/CMakeLists.txt")
    message(WARNING "Common submodule not found; using sibling directory ${COMMON_DIR_FALLBACK} for local builds. For a clean checkout, run: git submodule update --init --recursive")
    set(COMMON_DIR "${COMMON_DIR_FALLBACK}")
  else()
    message(FATAL_ERROR "Common library not found at ${CMAKE_CURRENT_SOURCE_DIR}/common. Run: git submodule update --init --recursive")
  endif()
endif()

# Process common headers for installation (inline Constants, remove internal dependencies)
set(PROCESSED_HEADERS_DIR "${CMAKE_CURRENT_BINARY_DIR}/processed_headers")
execute_process(
  COMMAND ${CMAKE_COMMAND}
    -DCOMMON_DIR=${COMMON_DIR}
    -DOUTPUT_DIR=${PROCESSED_HEADERS_DIR}
    -DALLOWLIST_FILE=${CMAKE_CURRENT_SOURCE_DIR}/allowed_common_headers.txt
    -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/ProcessHeadersForInstall.cmake
  RESULT_VARIABLE process_result
  OUTPUT_VARIABLE process_output
  ERROR_VARIABLE process_error
)

if(NOT process_result EQUAL 0)
  message(FATAL_ERROR "Header processing failed: ${process_error}")
endif()

message(STATUS "${process_output}")

add_subdirectory(${COMMON_DIR} ${CMAKE_BINARY_DIR}/common)

# Force the internal common library to build with hidden visibility so our public
# shared libraries do not leak internal/protocol symbols in their export table.
if(TARGET LumynSDK)
  set_target_properties(LumynSDK PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    C_VISIBILITY_PRESET hidden
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
  )
  if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|AppleClang")
    target_compile_options(LumynSDK PRIVATE 
      -fvisibility=hidden 
      -fvisibility-inlines-hidden
      -Wunused-function 
      -Wunused-variable 
      -Wunused-parameter
    )
  endif()
endif()

add_library(lumyn_sdk_c SHARED
  src/c_abi/lumyn_c_abi.cpp
  src/c_abi/internal/ConnectorXInternal.cpp
  src/cpp/lumyn_sdk_cpp_base_connectorx.cpp
  src/cpp/lumyn_sdk_cpp_connectorx.cpp
  src/cpp/lumyn_sdk_cpp_animate.cpp
  src/cpp/device/AnimationBuilder.cpp
  src/cpp/device/ImageSequenceBuilder.cpp
  src/cpp/device/MatrixTextBuilder.cpp
  src/cpp/device/BaseLumynDevice.cpp
  src/cpp/device/BaseModuleDevice.cpp
  src/cpp/device/DirectLED.cpp
  src/cpp/led/LEDCommander.cpp
  src/cpp/led/MatrixCommander.cpp
  src/cpp/util/serial/builtin_serial.cpp
  src/cpp/util/SerialIOAdapter.cpp
  src/cpp/managers/ConfigManager.cpp
  src/cpp/managers/EventManager.cpp
)
set_target_properties(lumyn_sdk_c PROPERTIES
  VERSION ${PROJECT_VERSION}
  SOVERSION ${PROJECT_VERSION_MAJOR}
  C_VISIBILITY_PRESET hidden
  CXX_VISIBILITY_PRESET hidden
  VISIBILITY_INLINES_HIDDEN ON
)

target_include_directories(lumyn_sdk_c
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${GENERATED_INCLUDE_DIR}>
    $<BUILD_INTERFACE:${COMMON_DIR}/include>
    $<INSTALL_INTERFACE:include>
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_definitions(lumyn_sdk_c PRIVATE LUMYN_SDK_BUILDING=1)
target_compile_definitions(lumyn_sdk_c PRIVATE LUMYN_SDK_CPP_BUILDING=1)
target_compile_definitions(lumyn_sdk_c PRIVATE LUMYN_SDK_ENABLE_BUILTIN_SERIAL=$<BOOL:${LUMYN_SDK_ENABLE_BUILTIN_SERIAL}>)

# Enable threading support when builtin serial is enabled and threads are available
if(LUMYN_SDK_ENABLE_BUILTIN_SERIAL AND Threads_FOUND)
  target_compile_definitions(lumyn_sdk_c PUBLIC LUMYN_HAS_THREADS=1)
endif()

target_link_libraries(lumyn_sdk_c PRIVATE LumynSDK)
target_link_libraries(lumyn_sdk_c PRIVATE Threads::Threads)

# Also build a STATIC archive variant of the C ABI. This archive is used by
# the C++ layer which pulls in the C ABI as a static dependency.
add_library(lumyn_sdk_c_static STATIC
  src/c_abi/lumyn_c_abi.cpp
  src/c_abi/internal/ConnectorXInternal.cpp
  src/cpp/lumyn_sdk_cpp_base_connectorx.cpp
  src/cpp/lumyn_sdk_cpp_connectorx.cpp
  src/cpp/lumyn_sdk_cpp_animate.cpp
  src/cpp/device/AnimationBuilder.cpp
  src/cpp/device/ImageSequenceBuilder.cpp
  src/cpp/device/MatrixTextBuilder.cpp
  src/cpp/device/BaseLumynDevice.cpp
  src/cpp/device/BaseModuleDevice.cpp
  src/cpp/device/DirectLED.cpp
  src/cpp/led/LEDCommander.cpp
  src/cpp/led/MatrixCommander.cpp
  src/cpp/util/serial/builtin_serial.cpp
  src/cpp/util/SerialIOAdapter.cpp
  src/cpp/managers/ConfigManager.cpp
  src/cpp/managers/EventManager.cpp
)
set_target_properties(lumyn_sdk_c_static PROPERTIES
  OUTPUT_NAME "lumyn_sdk_c_static"
  C_VISIBILITY_PRESET hidden
  CXX_VISIBILITY_PRESET hidden
  VISIBILITY_INLINES_HIDDEN ON
  POSITION_INDEPENDENT_CODE ON
)

target_include_directories(lumyn_sdk_c_static
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${GENERATED_INCLUDE_DIR}>
    $<BUILD_INTERFACE:${COMMON_DIR}/include>
    $<INSTALL_INTERFACE:include>
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_definitions(lumyn_sdk_c_static PRIVATE LUMYN_SDK_BUILDING=1)
target_compile_definitions(lumyn_sdk_c_static PRIVATE LUMYN_SDK_CPP_BUILDING=1)
target_compile_definitions(lumyn_sdk_c_static PRIVATE LUMYN_SDK_ENABLE_BUILTIN_SERIAL=$<BOOL:${LUMYN_SDK_ENABLE_BUILTIN_SERIAL}>)

if(LUMYN_SDK_ENABLE_BUILTIN_SERIAL AND Threads_FOUND)
  target_compile_definitions(lumyn_sdk_c_static PUBLIC LUMYN_HAS_THREADS=1)
endif()

target_link_libraries(lumyn_sdk_c_static PRIVATE LumynSDK)
target_link_libraries(lumyn_sdk_c_static PRIVATE Threads::Threads)

add_library(lumyn_sdk_cpp SHARED
  src/cpp/lumyn_sdk_cpp_base_connectorx.cpp
  src/cpp/lumyn_sdk_cpp_connectorx.cpp
  src/cpp/lumyn_sdk_cpp_animate.cpp
  src/cpp/device/AnimationBuilder.cpp
  src/cpp/device/ImageSequenceBuilder.cpp
  src/cpp/device/MatrixTextBuilder.cpp
  src/cpp/device/BaseLumynDevice.cpp
  src/cpp/device/BaseModuleDevice.cpp
  src/cpp/util/SerialIOAdapter.cpp
  src/cpp/managers/ConfigManager.cpp
  src/cpp/managers/EventManager.cpp
)
set_target_properties(lumyn_sdk_cpp PROPERTIES
  VERSION ${PROJECT_VERSION}
  SOVERSION ${PROJECT_VERSION_MAJOR}
  C_VISIBILITY_PRESET hidden
  CXX_VISIBILITY_PRESET hidden
  VISIBILITY_INLINES_HIDDEN ON
)

target_include_directories(lumyn_sdk_cpp
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${GENERATED_INCLUDE_DIR}>
    $<BUILD_INTERFACE:${COMMON_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_definitions(lumyn_sdk_cpp PRIVATE LUMYN_SDK_BUILDING=1)
target_compile_definitions(lumyn_sdk_cpp PRIVATE LUMYN_SDK_CPP_BUILDING=1)
target_link_libraries(lumyn_sdk_cpp PRIVATE lumyn_sdk_c_static)
target_link_libraries(lumyn_sdk_cpp PRIVATE LumynSDK)

if(LUMYN_SDK_BUILD_EXAMPLES)
  # C examples
  add_subdirectory(examples/c)
  
  # C++ examples
  add_subdirectory(examples/cpp)
endif()

# ---------------------------
# Tests
# ---------------------------

option(LUMYN_SDK_BUILD_TESTS "Build SDK tests" ON)

enable_testing()
add_subdirectory(tests)

# ---------------------------
# Install / Package
# ---------------------------

install(
  TARGETS lumyn_sdk_c lumyn_sdk_cpp
  EXPORT lumyn_sdk_targets
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

# Install the static C archive as a separate (non-exported) target. We avoid
# exporting it because it depends on the internal `LumynSDK` target which
# in turn depends on third-party targets that are not part of our export set.
install(
  TARGETS lumyn_sdk_c_static
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

install(
  FILES
    ${GENERATED_INCLUDE_DIR}/lumyn/sdk_version.h
    ${GENERATED_INCLUDE_DIR}/lumyn/sdk_version.hpp
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/lumyn
)

install(
  DIRECTORY include/lumyn
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# Install processed common headers (Constants values inlined, Constants.h excluded)
install(
  DIRECTORY ${PROCESSED_HEADERS_DIR}/lumyn
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
  FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp"
)

configure_package_config_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/cmake/lumyn-sdk-config.cmake.in
  ${CMAKE_CURRENT_BINARY_DIR}/lumyn-sdk-config.cmake
  INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/lumyn-sdk
)

write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/lumyn-sdk-config-version.cmake
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion
)

install(
  FILES
    ${CMAKE_CURRENT_BINARY_DIR}/lumyn-sdk-config.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/lumyn-sdk-config-version.cmake
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/lumyn-sdk
)

install(
  EXPORT lumyn_sdk_targets
  NAMESPACE lumyn::
  FILE lumyn-sdk-targets.cmake
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/lumyn-sdk
)
