# C Examples
add_executable(quickstart_c quickstart.c)
target_link_libraries(quickstart_c PRIVATE lumyn_sdk_c)

add_executable(connectorx_basic_c connectorx_basic.c)
target_link_libraries(connectorx_basic_c PRIVATE lumyn_sdk_c)

add_executable(connectorx_animate_c connectorx_animate.c)
target_link_libraries(connectorx_animate_c PRIVATE lumyn_sdk_c)

add_executable(matrix_text_advanced_c matrix_text_advanced.c)
target_link_libraries(matrix_text_advanced_c PRIVATE lumyn_sdk_c)

add_executable(modules_typed_c modules_typed.c)
target_link_libraries(modules_typed_c PRIVATE lumyn_sdk_c)

add_executable(modules_from_config_c modules_from_config.c)
target_link_libraries(modules_from_config_c PRIVATE lumyn_sdk_c)

add_executable(direct_led_patterns_c direct_led_patterns.c)
target_link_libraries(direct_led_patterns_c PRIVATE lumyn_sdk_c)
if(NOT WIN32)
  target_link_libraries(direct_led_patterns_c PRIVATE m)  # For math functions (Unix only)
endif()

add_executable(config_builder_basic_c config_builder_basic.c)
target_link_libraries(config_builder_basic_c PRIVATE lumyn_sdk_c)

add_executable(config_builder_advanced_c config_builder_advanced.c)
target_link_libraries(config_builder_advanced_c PRIVATE lumyn_sdk_c)

add_executable(config_apply_file_c config_apply_file.c)
target_link_libraries(config_apply_file_c PRIVATE lumyn_sdk_c)

add_executable(handshake_basic_c handshake_basic.c)
target_link_libraries(handshake_basic_c PRIVATE lumyn_sdk_c)

add_executable(port_scan_c port_scan.c)
target_link_libraries(port_scan_c PRIVATE lumyn_sdk_c)

add_executable(device_comparison_c device_comparison.c)
target_link_libraries(device_comparison_c PRIVATE lumyn_sdk_c)

add_executable(event_demo_c event_demo.c)
target_link_libraries(event_demo_c PRIVATE lumyn_sdk_c)
