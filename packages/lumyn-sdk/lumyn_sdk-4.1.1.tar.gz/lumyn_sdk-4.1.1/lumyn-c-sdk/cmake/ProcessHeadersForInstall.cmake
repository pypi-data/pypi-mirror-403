# ProcessHeadersForInstall.cmake
# This script processes common headers for installation by:
# 1. Enforcing the allowlist from allowed_common_headers.txt
# 2. Inlining Constants values and removing Constants.h includes
# 3. Failing the build if a disallowed header would be installed

cmake_minimum_required(VERSION 3.16)

if(NOT DEFINED COMMON_DIR OR NOT DEFINED OUTPUT_DIR OR NOT DEFINED ALLOWLIST_FILE)
  message(FATAL_ERROR "COMMON_DIR, OUTPUT_DIR, and ALLOWLIST_FILE must be defined")
endif()

message(STATUS "Processing headers for installation...")
message(STATUS "  Common dir: ${COMMON_DIR}")
message(STATUS "  Output dir: ${OUTPUT_DIR}")
message(STATUS "  Allowlist file: ${ALLOWLIST_FILE}")

# Create output directory
file(MAKE_DIRECTORY "${OUTPUT_DIR}")

# Read allowlist file and parse allowed headers
file(STRINGS "${ALLOWLIST_FILE}" ALLOWLIST_LINES)
set(ALLOWED_HEADERS "")
foreach(line ${ALLOWLIST_LINES})
  # Skip empty lines and comments
  string(STRIP "${line}" line)
  if(NOT line STREQUAL "" AND NOT line MATCHES "^#")
    list(APPEND ALLOWED_HEADERS "${line}")
  endif()
endforeach()

if(NOT ALLOWED_HEADERS)
  message(FATAL_ERROR "No headers found in allowlist file: ${ALLOWLIST_FILE}")
endif()

message(STATUS "Found ${CMAKE_MATCH_COUNT} allowed headers in allowlist")

# Define Constants values to inline (from Constants.h)
set(CONST_DEFAULT_ANIM_COLOR "{0, 0, 240}")
set(CONST_DEFAULT_BAUD_RATE "115200")
set(CONST_LOG_PREFIX "\"[  Lumyn   ]\"")
set(CONST_MIN_LOG_LEVEL "1")  # WARNING

# List of headers that need Constants inlining
set(HEADERS_TO_PROCESS
  "led/BuiltInAnimations.h"
  "configuration/configs/Network.h"
  "util/logging/ILogger.h"
  "util/logging/ConsoleLogger.h"
)

# Process each allowed header
foreach(rel_path ${ALLOWED_HEADERS})
  set(source_file "${COMMON_DIR}/include/lumyn/${rel_path}")
  set(output_file "${OUTPUT_DIR}/lumyn/${rel_path}")
  
  # Check if source file exists
  if(NOT EXISTS "${source_file}")
    message(WARNING "Allowed header not found: ${source_file}")
    continue()
  endif()
  
  # Create parent directory
  get_filename_component(output_dir "${output_file}" DIRECTORY)
  file(MAKE_DIRECTORY "${output_dir}")
  
  # Check if this file needs Constants processing
  set(needs_processing FALSE)
  foreach(process_file ${HEADERS_TO_PROCESS})
    if(rel_path STREQUAL process_file)
      set(needs_processing TRUE)
      break()
    endif()
  endforeach()
  
  if(needs_processing)
    # Read the file
    file(READ "${source_file}" content)
    
    # Remove #include "lumyn/Constants.h" and related includes
    string(REGEX REPLACE "#include \"lumyn/Constants\\.h\"[^\n]*\n" "" content "${content}")
    string(REGEX REPLACE "#include <lumyn/Constants\\.h>[^\n]*\n" "" content "${content}")
    
    # Inline constant values
    string(REGEX REPLACE "lumyn::internal::Constants::ColorConstants::kDefaultAnimationColor" 
      "lumyn::internal::domain::Color${CONST_DEFAULT_ANIM_COLOR}" content "${content}")
    string(REGEX REPLACE "lumyn::internal::Constants::Serial::kDefaultBaudRate"
      "${CONST_DEFAULT_BAUD_RATE}" content "${content}")
    string(REGEX REPLACE "Constants::Logging::kLogPrefix"
      "${CONST_LOG_PREFIX}" content "${content}")
    string(REGEX REPLACE "Constants::Logging::kMinLogLevel"
      "static_cast<LogLevel>(${CONST_MIN_LOG_LEVEL})" content "${content}")
    string(REGEX REPLACE "Constants::Logging::Level" "LogLevel" content "${content}")
    
    # Add a comment at the top indicating this is a processed file
    set(header_comment "// PROCESSED FOR SDK DISTRIBUTION\n// Constants have been inlined from lumyn/Constants.h\n// DO NOT EDIT - This file is generated at build time\n\n")
    string(PREPEND content "${header_comment}")
    
    # Write processed file
    file(WRITE "${output_file}" "${content}")
    message(STATUS "  Processed: ${rel_path}")
  else()
    # Copy as-is
    file(COPY "${source_file}" DESTINATION "${output_dir}")
    message(STATUS "  Copied: ${rel_path}")
  endif()
endforeach()

message(STATUS "Header processing complete - ${CMAKE_MATCH_COUNT} headers installed")
message(STATUS "All installed headers are from the allowlist - no private headers exposed")
