#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <lumyn/Constants.h>
#include <lumyn/led/DirectLEDBuffer.h>
#include <lumyn/led/DirectBufferManager.h>
#include <lumyn/led/BuiltInAnimations.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_led_bindings(py::module &m)
  {
    auto led_m = m.def_submodule("led", "LED related types");

    // Built-in animation defaults (sourced from common)
    led_m.def(
        "builtin_animation_default_delay_ms",
        [](int animation_value) -> int
        {
          const auto &anims = lumyn::internal::Animation::BuiltInAnimations;
          if (animation_value < 0 || static_cast<size_t>(animation_value) >= anims.size())
          {
            throw std::out_of_range("animation_value out of range");
          }
          return static_cast<int>(anims[static_cast<size_t>(animation_value)].defaultDelay);
        },
        py::arg("animation_value"),
        "Get the built-in animation default delay in milliseconds for an Animation enum value.");

    led_m.def(
        "builtin_animation_default_color_rgb",
        [](int animation_value) -> std::vector<int>
        {
          const auto &anims = lumyn::internal::Animation::BuiltInAnimations;
          if (animation_value < 0 || static_cast<size_t>(animation_value) >= anims.size())
          {
            throw std::out_of_range("animation_value out of range");
          }
          const auto &c = anims[static_cast<size_t>(animation_value)].defaultColor;
          return {static_cast<int>(c.r), static_cast<int>(c.g), static_cast<int>(c.b)};
        },
        py::arg("animation_value"),
        "Get the built-in animation default color as [r,g,b] for an Animation enum value.");

    // DirectLEDBuffer - low-level buffer with delta compression
    py::class_<lumyn::internal::DirectLEDBuffer>(led_m, "DirectLEDBuffer")
        .def(py::init<std::string_view, size_t>(),
             py::arg("zone_id"), py::arg("length"),
             "Construct a DirectLEDBuffer for a specific zone with expected buffer length")
        .def(py::init<uint16_t, size_t>(),
             py::arg("zone_id"), py::arg("length"),
             "Construct a DirectLEDBuffer with a pre-computed zone ID and expected buffer length")
        .def("update", [](lumyn::internal::DirectLEDBuffer &self, py::bytes data, bool useDelta) -> py::bytes
             {
               std::string data_str = data;
               auto result = self.update(
                   reinterpret_cast<const uint8_t*>(data_str.c_str()),
                   data_str.size(),
                   useDelta);
               return py::bytes(reinterpret_cast<const char*>(result.data()), result.size()); }, py::arg("data"), py::arg("use_delta") = true, "Update the LED buffer and generate command bytes (empty if length mismatch)")
        .def("force_full_update", [](lumyn::internal::DirectLEDBuffer &self, py::bytes data) -> py::bytes
             {
               std::string data_str = data;
               auto result = self.forceFullUpdate(
                   reinterpret_cast<const uint8_t*>(data_str.c_str()),
                   data_str.size());
               return py::bytes(reinterpret_cast<const char*>(result.data()), result.size()); }, py::arg("data"), "Force a full buffer update (no delta compression)")
        .def("reset", &lumyn::internal::DirectLEDBuffer::reset, "Reset the buffer state, forcing next update to be full")
        .def_property_readonly("zone_id", &lumyn::internal::DirectLEDBuffer::zoneId, "Get the zone ID (hashed)")
        .def_property_readonly("buffer_length", &lumyn::internal::DirectLEDBuffer::bufferLength, "Get the expected buffer length")
        .def_property_readonly("padded_length", &lumyn::internal::DirectLEDBuffer::paddedLength, "Get the padded buffer length (4-byte aligned)")
        .def("has_previous_buffer", &lumyn::internal::DirectLEDBuffer::hasPreviousBuffer, "Check if we have a previous buffer stored")
        .def_property_readonly("previous_buffer_size", &lumyn::internal::DirectLEDBuffer::previousBufferSize, "Get the size of the previous buffer (0 if none)");

    // DirectBufferManager - higher-level manager with automatic periodic full refreshes
    py::class_<lumyn::internal::DirectBufferManager>(led_m, "DirectBufferManager")
        .def(py::init<std::string_view, size_t, int>(),
             py::arg("zone_id"), py::arg("length"), py::arg("full_refresh_interval") = 100,
             "Construct a manager for a zone with expected buffer length and optional refresh interval")
        .def(py::init<uint16_t, size_t, int>(),
             py::arg("zone_id"), py::arg("length"), py::arg("full_refresh_interval") = 100,
             "Construct with pre-computed zone ID, buffer length, and refresh interval")
        .def("update", [](lumyn::internal::DirectBufferManager &self, py::bytes data) -> py::bytes
             {
               std::string data_str = data;
               auto result = self.update(
                   reinterpret_cast<const uint8_t*>(data_str.c_str()),
                   data_str.size());
               return py::bytes(reinterpret_cast<const char*>(result.data()), result.size()); }, py::arg("data"), "Update LED buffer, automatically using delta or full based on frame count")
        .def("force_full_update", [](lumyn::internal::DirectBufferManager &self, py::bytes data) -> py::bytes
             {
               std::string data_str = data;
               auto result = self.forceFullUpdate(
                   reinterpret_cast<const uint8_t*>(data_str.c_str()),
                   data_str.size());
               return py::bytes(reinterpret_cast<const char*>(result.data()), result.size()); }, py::arg("data"), "Force a full buffer update and reset frame counter")
        .def("reset", &lumyn::internal::DirectBufferManager::reset, "Reset state, forcing next update to be full")
        .def_property_readonly("buffer_length", &lumyn::internal::DirectBufferManager::bufferLength, "Get the expected buffer length")
        .def_property("full_refresh_interval", &lumyn::internal::DirectBufferManager::fullRefreshInterval, &lumyn::internal::DirectBufferManager::setFullRefreshInterval, "Get/set the full refresh interval")
        .def_property_readonly("frame_count", &lumyn::internal::DirectBufferManager::frameCount, "Get current frame count since last full refresh");
  }
}
