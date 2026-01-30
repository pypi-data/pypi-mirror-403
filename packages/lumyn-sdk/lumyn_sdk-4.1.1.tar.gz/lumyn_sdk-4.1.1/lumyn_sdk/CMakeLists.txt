cmake_minimum_required(VERSION 3.15)
project(lumyn_python_bindings)

# Force C++20 for all targets
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(PYBIND11_FINDPYTHON ON)

# Find pybind11 dynamically using Python
execute_process(
    COMMAND ${Python_EXECUTABLE} -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE PYBIND11_RESULT
)

if(NOT PYBIND11_RESULT EQUAL 0)
    # Fallback: try to find pybind11 without setting pybind11_DIR
    message(STATUS "Could not get pybind11 cmake dir from Python, trying system find_package")
endif()

# Find pybind11
find_package(pybind11 REQUIRED)
message(STATUS "CMAKE_SOURCE_DIR: ${CMAKE_SOURCE_DIR}")

# Lumyn C++ SDK location (submodule at repo root)
set(LUMYN_C_SDK_DIR "${CMAKE_SOURCE_DIR}/../lumyn-c-sdk")

# Verify SDK exists
if(NOT EXISTS "${LUMYN_C_SDK_DIR}/CMakeLists.txt")
    message(FATAL_ERROR 
        "Lumyn C++ SDK not found at ${LUMYN_C_SDK_DIR}\n"
        "Please initialize submodule:\n"
        "  git submodule update --init --recursive"
    )
endif()

message(STATUS "Using Lumyn C++ SDK from: ${LUMYN_C_SDK_DIR}")

# Build the C++ SDK (static library for Python bindings)
# This also builds the C SDK and includes common transitively
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build static for Python" FORCE)
add_subdirectory(${LUMYN_C_SDK_DIR} ${CMAKE_BINARY_DIR}/lumyn-c-sdk)

# Ensure SDK static library has PIC for our shared module
set_target_properties(lumyn_sdk_cpp PROPERTIES POSITION_INDEPENDENT_CODE ON)
set_target_properties(lumyn_sdk_c_static PROPERTIES POSITION_INDEPENDENT_CODE ON)

# Force lumyn_sdk_cpp DLL to be output to the package directory
# This is critical on Windows with multi-config generators (Visual Studio)
set_target_properties(lumyn_sdk_cpp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}"
)

# On macOS, set install name to @rpath so delocate-wheel can find and bundle the library
# This is critical for wheel repair - delocate searches by install name, not env vars
if(APPLE)
    set_target_properties(lumyn_sdk_cpp PROPERTIES
        MACOSX_RPATH ON
        INSTALL_NAME_DIR "@rpath"
        BUILD_WITH_INSTALL_RPATH TRUE
    )
endif()

# Include the SDK headers
# Include C++ SDK public includes and common headers (needed for Constants.h)
# The binding .cpp files include Constants.h first to define the namespace
include_directories(
    ${LUMYN_C_SDK_DIR}/include
    ${LUMYN_C_SDK_DIR}/common/include
    ${CMAKE_SOURCE_DIR}/src
)

# Create the pybind11 module
# Named _bindings_ext (not _bindings) to avoid conflict with _bindings/ package directory
pybind11_add_module(_bindings_ext
    src/bindings.cpp
    src/bindings/config_bindings.cpp
    src/bindings/connectorx_bindings.cpp
    src/bindings/command_bindings.cpp
    src/bindings/event_bindings.cpp
    src/bindings/module_bindings.cpp
    src/bindings/util_bindings.cpp
    src/bindings/led_bindings.cpp
    # Low-level bindings still disabled:
    # src/bindings/file_bindings.cpp
    # src/bindings/packet_bindings.cpp
    # src/bindings/request_bindings.cpp
    # src/bindings/response_bindings.cpp
    # src/bindings/transmission_bindings.cpp
    # src/bindings/serial_bindings.cpp
)

# Link against the C++ SDK shared library AND the common library (LumynSDK)
# The common library provides SerializeConfigToJson, CommandBuilder, and other internal functions
# This requires bundling lumyn_sdk_cpp.dll with the package
target_link_libraries(_bindings_ext PRIVATE lumyn_sdk_cpp LumynSDK)

# Set RPATH so the module can find shared libraries in the same directory
# This is critical for Linux/macOS to find liblumyn_sdk_cpp.so at runtime
if(UNIX)
    set_target_properties(_bindings_ext PROPERTIES
        BUILD_WITH_INSTALL_RPATH TRUE
        INSTALL_RPATH "$ORIGIN"
    )
    if(APPLE)
        set_target_properties(_bindings_ext PROPERTIES
            INSTALL_RPATH "@loader_path"
        )
    endif()
endif()

# Set the output directory to be the Python package directory
# Force output to package root, not build subdirectories
set_target_properties(_bindings_ext PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}"
)

# For PyPI distribution: copy required runtime DLLs to package directory
if(WIN32)
    # Copy lumyn_sdk_cpp.dll to the package directory
    add_custom_command(TARGET _bindings_ext POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:lumyn_sdk_cpp>
            "${CMAKE_SOURCE_DIR}"
        COMMENT "Copying lumyn_sdk_cpp.dll to package directory for distribution"
    )
else()
    # On Linux/Mac, copy .so/.dylib files AND all symlinks to the same directory as _bindings_ext
    # The library has SOVERSION so we need to copy the real file and create symlinks
    add_custom_command(TARGET _bindings_ext POST_BUILD
        # Copy the actual library file (e.g., liblumyn_sdk_cpp.so.4.1.4)
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:lumyn_sdk_cpp>
            "${CMAKE_SOURCE_DIR}/"
        # Copy the SONAME symlink (e.g., liblumyn_sdk_cpp.so.4)
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_SONAME_FILE:lumyn_sdk_cpp>
            "${CMAKE_SOURCE_DIR}/"
        # Create the unversioned symlink (liblumyn_sdk_cpp.so -> liblumyn_sdk_cpp.so.4)
        COMMAND ${CMAKE_COMMAND} -E create_symlink
            $<TARGET_SONAME_FILE_NAME:lumyn_sdk_cpp>
            "${CMAKE_SOURCE_DIR}/$<TARGET_LINKER_FILE_NAME:lumyn_sdk_cpp>"
        COMMENT "Copying lumyn_sdk_cpp shared library and symlinks to package directory"
    )
endif()