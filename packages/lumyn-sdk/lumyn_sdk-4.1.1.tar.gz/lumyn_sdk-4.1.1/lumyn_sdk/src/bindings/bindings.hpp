#pragma once
#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_command_bindings(py::module &m);
  void register_config_bindings(py::module &m);
  void register_event_bindings(py::module &m);
  void register_file_bindings(py::module &m);
  void register_led_bindings(py::module &m);
  void register_module_bindings(py::module &m);
  void register_packet_bindings(py::module &m);
  void register_request_bindings(py::module &m);
  void register_response_bindings(py::module &m);
  void register_serial_bindings(py::module &m);
  void register_transmission_bindings(py::module &m);
  void register_device_bindings(py::module &m);
  void register_util_bindings(py::module &m);
  void register_connectorx_bindings(py::module &m);
}