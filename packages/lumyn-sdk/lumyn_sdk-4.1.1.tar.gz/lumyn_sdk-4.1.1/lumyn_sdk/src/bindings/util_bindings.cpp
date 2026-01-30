#include <lumyn/Constants.h> // Required for common headers that reference Constants namespace
#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <lumyn/util/CircularBuffer.h>
#include <lumyn/util/logging/ILogger.h>
#include <lumyn/util/logging/ConsoleLogger.h>
#include <lumyn/util/hashing/MD5.h>
#include <lumyn/util/hashing/IDCreator.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_util_bindings(py::module &m)
  {
    // Utility namespace and types
    auto util_m = m.def_submodule("util", "Utility classes");

    // CircularBuffer
    py::class_<lumyn::internal::CircularBuffer<uint8_t>>(util_m, "CircularBuffer")
        .def(py::init<size_t>())
        .def("push", [](lumyn::internal::CircularBuffer<uint8_t> &self, py::bytes data)
             {
                std::string str_data = data;
                for (char c : str_data) {
                    self.push(static_cast<uint8_t>(c));
                } })
        .def("pop", &lumyn::internal::CircularBuffer<uint8_t>::pop)
        .def("front", &lumyn::internal::CircularBuffer<uint8_t>::front)
        .def("size", &lumyn::internal::CircularBuffer<uint8_t>::size)
        .def("capacity", &lumyn::internal::CircularBuffer<uint8_t>::capacity);

    // Logging namespace - commenting out until proper header files are available
    // auto logging_m = util_m.def_submodule("logging", "Logging utilities");

    // Hashing namespace
    auto hashing_m = util_m.def_submodule("hashing", "Hashing utilities");

    py::class_<MD5>(hashing_m, "MD5")
        .def_static("hash", [](py::bytes data) -> py::bytes
                    {
                std::string str_data = data;
                uint8_t hash[16];
                MD5::Hash(
                    reinterpret_cast<const void*>(str_data.c_str()), 
                    str_data.size(), 
                    hash);
                return py::bytes(reinterpret_cast<const char*>(hash), 16); });

    py::class_<lumyn::internal::IDCreator>(hashing_m, "IDCreator")
        .def_static("createId", [](const std::string &input) -> uint16_t
                    { return lumyn::internal::IDCreator::createId(input); });
  }
}