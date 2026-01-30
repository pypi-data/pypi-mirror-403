#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "bindings/bindings.hpp"

#include <lumyn/version.h>

namespace py = pybind11;

// Module name matches CMakeLists.txt: pybind11_add_module(_bindings_ext, ...)
// Named _bindings_ext to avoid conflict with _bindings/ package directory
PYBIND11_MODULE(_bindings_ext, m)
{
  m.doc() = "Lumyn SDK Python bindings";

  // Add version info
  m.attr("__version__") = "1.0.0";

  // Version constants from the SDK (use LUMYN_VERSION from common)
  m.attr("DRIVER_VERSION_MAJOR") = LUMYN_VERSION_MAJOR;
  m.attr("DRIVER_VERSION_MINOR") = LUMYN_VERSION_MINOR;
  m.attr("DRIVER_VERSION_PATCH") = LUMYN_VERSION_PATCH;

  // Register high-level C++ SDK bindings
  lumyn_bindings::register_connectorx_bindings(m);
  lumyn_bindings::register_config_bindings(m);

  // Register required bindings for tests (using internal common headers)
  lumyn_bindings::register_command_bindings(m); // Exposes _command submodule
  lumyn_bindings::register_event_bindings(m);   // Exposes _event submodule
  lumyn_bindings::register_module_bindings(m);  // Exposes _module submodule
  lumyn_bindings::register_util_bindings(m);    // Exposes _util submodule
  lumyn_bindings::register_led_bindings(m);     // Exposes _led submodule (for DirectLED)

  // Low-level bindings still disabled:
  // lumyn_bindings::register_file_bindings(m);
  // lumyn_bindings::register_request_bindings(m);
  // lumyn_bindings::register_response_bindings(m);
  // lumyn_bindings::register_packet_bindings(m);
  // lumyn_bindings::register_transmission_bindings(m);
  // lumyn_bindings::register_serial_bindings(m);
}