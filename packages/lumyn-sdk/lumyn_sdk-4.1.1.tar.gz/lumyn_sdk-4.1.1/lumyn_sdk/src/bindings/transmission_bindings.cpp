#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include <lumyn/domain/transmission/TransmissionType.h>
#include <lumyn/domain/transmission/Transmission.h>
#include <lumyn/domain/file/FileType.h>
#include <lumyn/networking/ILumynTransmissionHandler.h>
#include <lumyn/networking/TransmissionPortListener.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  // Forward declare to avoid ambiguity on MSVC
  using TransmissionClass = ::lumyn::internal::Transmission::Transmission;

  // Trampoline class for ILumynTransmissionHandler
  class PyLumynTransmissionHandler : public lumyn::internal::ILumynTransmissionHandler
  {
  public:
    using lumyn::internal::ILumynTransmissionHandler::ILumynTransmissionHandler;

    void HandleEvent(const lumyn::internal::Eventing::Event &event) override
    {
      PYBIND11_OVERRIDE_PURE(
          void,
          lumyn::internal::ILumynTransmissionHandler,
          HandleEvent,
          event);
    }

    void HandleTransmission(const TransmissionClass &transmission) override
    {
      // Transmission is non-copyable (pool-managed), so we need to pass by pointer/reference
      // Use std::ref to avoid copying
      PYBIND11_OVERRIDE_PURE(
          void,
          lumyn::internal::ILumynTransmissionHandler,
          HandleTransmission,
          std::ref(transmission));
    }
  };

  void register_transmission_bindings(py::module &m)
  {
    // Transmission namespace and types
    auto transmission_m = m.def_submodule("transmission", "Transmission related types");

    py::enum_<lumyn::internal::Transmission::TransmissionType>(transmission_m, "TransmissionType")
        .value("Request", lumyn::internal::Transmission::TransmissionType::Request)
        .value("Response", lumyn::internal::Transmission::TransmissionType::Response)
        .value("Event", lumyn::internal::Transmission::TransmissionType::Event)
        .value("Command", lumyn::internal::Transmission::TransmissionType::Command)
        .value("File", lumyn::internal::Transmission::TransmissionType::File)
        .value("ModuleData", lumyn::internal::Transmission::TransmissionType::ModuleData)
        .export_values();

    // TransmissionHeaderFlags
    py::class_<lumyn::internal::Transmission::TransmissionHeaderFlags>(transmission_m, "TransmissionHeaderFlags")
        .def(py::init<>())
        .def_property("compressed", [](const lumyn::internal::Transmission::TransmissionHeaderFlags &flags)
                      { return static_cast<bool>(flags.compressed); }, [](lumyn::internal::Transmission::TransmissionHeaderFlags &flags, bool value)
                      { flags.compressed = value ? 1 : 0; });

    // TransmissionHeader
    py::class_<lumyn::internal::Transmission::TransmissionHeader>(transmission_m, "TransmissionHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Transmission::TransmissionHeader::type)
        .def_readwrite("dataLength", &lumyn::internal::Transmission::TransmissionHeader::dataLength)
        .def_readwrite("packetCount", &lumyn::internal::Transmission::TransmissionHeader::packetCount)
        .def_readwrite("flags", &lumyn::internal::Transmission::TransmissionHeader::flags);

    // Transmission class (RefCounted, pool-backed) - exposed read-only since it's managed by the pool
    py::class_<TransmissionClass, std::unique_ptr<TransmissionClass, py::nodelete>>(transmission_m, "Transmission")
        .def("getHeader", &TransmissionClass::getHeader, py::return_value_policy::reference)
        .def("getBuffer", [](const TransmissionClass &t)
             { return py::bytes(reinterpret_cast<const char *>(t.getBuffer()), t.getTotalSize()); })
        .def("getTotalSize", &TransmissionClass::getTotalSize)
        .def("getPayloadBytes", [](const TransmissionClass &t)
             {
                auto* header = t.getHeader();
                if (!header) return py::bytes();
                return py::bytes(reinterpret_cast<const char*>(t.getPayloadBytes()), header->dataLength); })
        .def("setPacketCount", &TransmissionClass::setPacketCount);

    // Packet constants from Transmission.h
    transmission_m.attr("kMaxPacketSize") = lumyn::internal::Transmission::kMaxPacketSize;
    transmission_m.attr("kMaxPacketBodySize") = lumyn::internal::Transmission::kMaxPacketBodySize;

    // ILumynTransmissionHandler interface
    py::class_<lumyn::internal::ILumynTransmissionHandler, PyLumynTransmissionHandler>(transmission_m, "ILumynTransmissionHandler")
        .def(py::init<>())
        .def("HandleEvent", &lumyn::internal::ILumynTransmissionHandler::HandleEvent)
        .def("HandleTransmission", &lumyn::internal::ILumynTransmissionHandler::HandleTransmission);

    // TransmissionPortListener
    py::class_<lumyn::internal::TransmissionPortListener>(transmission_m, "TransmissionPortListener")
        .def(py::init<lumyn::internal::ILumynTransmissionHandler &>())
        .def("Init", &lumyn::internal::TransmissionPortListener::Init)
        .def("SendCommand", [](lumyn::internal::TransmissionPortListener &self,
                               const lumyn::internal::Command::CommandHeader &header,
                               py::bytes payload)
             {
                std::string str = payload;
                self.SendCommand(header, str.data(), str.size()); })
        .def("SendRequest", [](lumyn::internal::TransmissionPortListener &self, lumyn::internal::Request::Request &request, int timeoutMs) -> py::object
             {
                py::object result;
                {
                    py::gil_scoped_release release;
                    auto cpp_result = self.SendRequest(request, timeoutMs);
                    if (cpp_result.has_value()) {
                        py::gil_scoped_acquire acquire;
                        result = py::cast(cpp_result.value());
                    } else {
                        py::gil_scoped_acquire acquire;
                        result = py::none();
                    }
                }
                return result; }, py::arg("request"), py::arg("timeoutMs") = 10000)
        .def("ingressBytes", [](lumyn::internal::TransmissionPortListener &self, py::bytes data)
             {
                std::string str_data = data;
                {
                    py::gil_scoped_release release;
                    self.ingressBytes(reinterpret_cast<const uint8_t*>(str_data.c_str()), str_data.size());
                } })
        .def("setWriteCallback", [](lumyn::internal::TransmissionPortListener &self, py::function callback)
             { self.setWriteCallback(
                   [callback](const uint8_t *data, size_t length)
                   {
                     py::gil_scoped_acquire acquire;
                     py::bytes data_bytes(reinterpret_cast<const char *>(data), length);
                     callback(data_bytes);
                   }); })
        .def("SendFile", [](lumyn::internal::TransmissionPortListener &self, lumyn::internal::Files::FileType type, py::bytes data, py::object path)
             {
                    std::string str_data = data;
                    const char* cpath = nullptr;
                    std::string path_storage;
                    if (!path.is_none()) {
                        path_storage = py::cast<std::string>(path);
                        cpath = path_storage.c_str();
                    }
                    {
                        py::gil_scoped_release release;
                        self.SendFile(type, reinterpret_cast<const uint8_t*>(str_data.c_str()), static_cast<uint32_t>(str_data.size()), cpath);
                    } }, py::arg("type"), py::arg("data"), py::arg("path") = py::none())
        .def("TryPopModuleDataRaw", [](lumyn::internal::TransmissionPortListener &self, uint16_t moduleId)
             {
                std::vector<std::vector<uint8_t>> out;
                bool result = self.TryPopModuleDataRaw(moduleId, out);
                if (!result) return py::list();
                py::list py_out;
                for (auto& vec : out) {
                    py_out.append(py::bytes(reinterpret_cast<const char*>(vec.data()), vec.size()));
                }
                return py_out; })
        .def("GetConfigFullData", [](lumyn::internal::TransmissionPortListener &self, uint32_t requestId)
             {
                std::vector<uint8_t> out;
                bool result = self.GetConfigFullData(requestId, out);
                if (!result) return py::none().cast<py::object>();
                return py::bytes(reinterpret_cast<const char*>(out.data()), out.size()).cast<py::object>(); });
  }
}
