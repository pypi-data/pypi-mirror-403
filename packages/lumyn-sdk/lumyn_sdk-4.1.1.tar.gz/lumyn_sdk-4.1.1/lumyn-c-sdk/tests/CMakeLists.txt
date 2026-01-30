# Tests for lumyn-c-sdk

# Fetch Google Test
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)

# Helper function to create test executables with common configuration
function(lumyn_add_test test_name)
  add_executable(${test_name} ${test_name}.cpp)
  target_link_libraries(${test_name} GTest::gtest GTest::gtest_main lumyn_sdk_c)
  target_include_directories(${test_name} PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}/..
    ${CMAKE_CURRENT_SOURCE_DIR}/../include
    ${CMAKE_CURRENT_BINARY_DIR}/../generated/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../common/include
  )
  target_compile_definitions(${test_name} PRIVATE PROJECT_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/..")
  add_test(NAME ${test_name} COMMAND ${test_name})
  
  # On Windows, ensure DLLs are in the same directory as the test executable
  if(WIN32)
    add_custom_command(TARGET ${test_name} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:lumyn_sdk_c>
        $<TARGET_FILE_DIR:${test_name}>
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:lumyn_sdk_cpp>
        $<TARGET_FILE_DIR:${test_name}>
    )
  endif()
endfunction()

# =============================================================================
# Core API Tests
# =============================================================================

# Test: Version API
lumyn_add_test(test_version_api)

# Test: Device Lifecycle (Create/Destroy)
lumyn_add_test(test_device_lifecycle)

# Test: Connection API
lumyn_add_test(test_connection_api)

# Test: LED Control API
lumyn_add_test(test_led_api)

# Test: Animation Consistency (AnimationBuilder vs BuiltInAnimations)
# This test uses C++ APIs, so it needs lumyn_sdk_cpp
add_executable(test_animation_consistency test_animation_consistency.cpp)
target_link_libraries(test_animation_consistency GTest::gtest GTest::gtest_main lumyn_sdk_c lumyn_sdk_cpp)
target_include_directories(test_animation_consistency PRIVATE 
  ${CMAKE_CURRENT_SOURCE_DIR}/..
  ${CMAKE_CURRENT_SOURCE_DIR}/../include
  ${CMAKE_CURRENT_BINARY_DIR}/../generated/include
  ${CMAKE_CURRENT_SOURCE_DIR}/../common/include
)
target_compile_definitions(test_animation_consistency PRIVATE PROJECT_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/..")
add_test(NAME test_animation_consistency COMMAND test_animation_consistency)

# =============================================================================
# C++ SDK Tests
# =============================================================================

# Helper function for C++ SDK tests (links lumyn_sdk_cpp instead of lumyn_sdk_c)
function(lumyn_add_cpp_test test_name)
  add_executable(${test_name} ${test_name}.cpp)
  target_link_libraries(${test_name} GTest::gtest GTest::gtest_main lumyn_sdk_cpp)
  target_include_directories(${test_name} PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}/..
    ${CMAKE_CURRENT_SOURCE_DIR}/../include
    ${CMAKE_CURRENT_BINARY_DIR}/../generated/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../common/include
  )
  target_compile_definitions(${test_name} PRIVATE PROJECT_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/..")
  add_test(NAME ${test_name} COMMAND ${test_name})
  
  # On Windows, ensure DLLs are in the same directory as the test executable
  if(WIN32)
    add_custom_command(TARGET ${test_name} POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:lumyn_sdk_c>
        $<TARGET_FILE_DIR:${test_name}>
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:lumyn_sdk_cpp>
        $<TARGET_FILE_DIR:${test_name}>
    )
  endif()
endfunction()

# Test: C++ Device Lifecycle (ConnectorX, ConnectorXAnimate construction/destruction)
lumyn_add_cpp_test(test_cpp_device_lifecycle)

# Test: C++ Connection API (Connect, Disconnect, IsConnected, GetStatus)
lumyn_add_cpp_test(test_cpp_connection_api)

# Test: C++ Event API (event handlers, polling, Event wrapper)
lumyn_add_cpp_test(test_cpp_event_api)

# Test: C++ Config API (RequestConfig, ApplyConfiguration, LoadConfiguration)
lumyn_add_cpp_test(test_cpp_config_api)

# Test: C++ LED API (SetColor, AnimationBuilder, MatrixTextBuilder, ImageSequenceBuilder, DirectLED)
lumyn_add_cpp_test(test_cpp_led_api)

# Test: C++ Module API (module polling, device restart)
lumyn_add_cpp_test(test_cpp_module_api)

# Test: C++ Types (ConnectionStatus, type aliases, Event wrapper)
lumyn_add_cpp_test(test_cpp_types)

# Test: DirectLED API
lumyn_add_test(test_direct_led_api)

# Test: Event API
lumyn_add_test(test_event_api)

# Test: Module API
lumyn_add_test(test_module_api)

# Test: Configuration API
lumyn_add_test(test_config_api)

# =============================================================================
# Existing Tests (with updated configuration)
# =============================================================================

# Test: Header Independence
add_executable(test_header_independence test_header_independence.cpp)
target_link_libraries(test_header_independence GTest::gtest GTest::gtest_main lumyn_sdk_c)
target_include_directories(test_header_independence PRIVATE 
  ${CMAKE_CURRENT_SOURCE_DIR}/..
  ${CMAKE_CURRENT_SOURCE_DIR}/../include
  ${CMAKE_CURRENT_BINARY_DIR}/../generated/include
  ${CMAKE_CURRENT_SOURCE_DIR}/../common/include
)
target_compile_definitions(test_header_independence PRIVATE PROJECT_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/..")
add_test(NAME test_header_independence COMMAND test_header_independence)

# Test: Configuration Parsing (detailed)
lumyn_add_test(test_config_parsing)

# Test: Memory Allocation Tracking
lumyn_add_test(test_memory_allocation)

# Test: Error Handling Consistency
lumyn_add_test(test_error_handling)

# Test: Managers (C++ SDK)
lumyn_add_cpp_test(test_managers)

# =============================================================================
# Test Discovery and Running
# =============================================================================

enable_testing()

# Include Google Test discovery for IDE integration
include(GoogleTest)

# Create a custom target to run all tests
add_custom_target(run_tests
  COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure --parallel 4
  DEPENDS 
    test_version_api
    test_device_lifecycle
    test_connection_api
    test_led_api
    test_direct_led_api
    test_event_api
    test_module_api
    test_config_api
    test_animation_consistency
    test_cpp_device_lifecycle
    test_cpp_connection_api
    test_cpp_event_api
    test_cpp_config_api
    test_cpp_led_api
    test_cpp_module_api
    test_cpp_types
    test_header_independence
    test_config_parsing
    test_memory_allocation
    test_error_handling
    test_managers
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  COMMENT "Running all SDK tests..."
)

# Option to run tests automatically after build (disabled by default to avoid slowdowns)
option(LUMYN_SDK_RUN_TESTS_ON_BUILD "Run tests automatically after each build" OFF)

if(LUMYN_SDK_RUN_TESTS_ON_BUILD)
  add_custom_command(
    TARGET run_tests
    POST_BUILD
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure --parallel 4
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "Running tests after build..."
  )
endif()

