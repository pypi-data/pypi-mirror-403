#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <lumyn/domain/request/Request.h>
#include <lumyn/domain/request/RequestType.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_request_bindings(py::module &m)
  {
    // Request namespace and types
    auto request_m = m.def_submodule("request", "Request related types");

    py::enum_<lumyn::internal::Request::RequestType>(request_m, "RequestType")
        .value("Handshake", lumyn::internal::Request::RequestType::Handshake)
        .value("Status", lumyn::internal::Request::RequestType::Status)
        .value("ProductSKU", lumyn::internal::Request::RequestType::ProductSKU)
        .value("ProductSerialNumber", lumyn::internal::Request::RequestType::ProductSerialNumber)
        .value("ConfigHash", lumyn::internal::Request::RequestType::ConfigHash)
        .value("AssignedId", lumyn::internal::Request::RequestType::AssignedId)
        .value("Faults", lumyn::internal::Request::RequestType::Faults)
        .value("ModuleStatus", lumyn::internal::Request::RequestType::ModuleStatus)
        .value("ModuleData", lumyn::internal::Request::RequestType::ModuleData)
        .value("LEDChannelStatus", lumyn::internal::Request::RequestType::LEDChannelStatus)
        .value("LEDZoneStatus", lumyn::internal::Request::RequestType::LEDZoneStatus)
        .value("LatestEvent", lumyn::internal::Request::RequestType::LatestEvent)
        .value("EventFlags", lumyn::internal::Request::RequestType::EventFlags)
        .value("ConfigFull", lumyn::internal::Request::RequestType::ConfigFull)
        .export_values();

    py::enum_<lumyn::internal::Request::HostConnectionSource>(request_m, "HostConnectionSource")
        .value("Unknown", lumyn::internal::Request::HostConnectionSource::Unknown)
        .value("Studio", lumyn::internal::Request::HostConnectionSource::Studio)
        .value("Roborio", lumyn::internal::Request::HostConnectionSource::Roborio)
        .value("LumynSDK", lumyn::internal::Request::HostConnectionSource::LumynSDK)
        .export_values();

    // Request info structs
    py::class_<lumyn::internal::Request::RequestHandshakeInfo>(request_m, "RequestHandshakeInfo")
        .def(py::init<>())
        .def_readwrite("hostSource", &lumyn::internal::Request::RequestHandshakeInfo::hostSource);

    py::class_<lumyn::internal::Request::RequestStatusInfo>(request_m, "RequestStatusInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestProductSKUInfo>(request_m, "RequestProductSKUInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestProductSerialNumberInfo>(request_m, "RequestProductSerialNumberInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestConfigHashInfo>(request_m, "RequestConfigHashInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestAssignedIdInfo>(request_m, "RequestAssignedIdInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestFaultsInfo>(request_m, "RequestFaultsInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestModuleStatusInfo>(request_m, "RequestModuleStatusInfo")
        .def(py::init<>())
        .def_readwrite("moduleId", &lumyn::internal::Request::RequestModuleStatusInfo::moduleId);

    py::class_<lumyn::internal::Request::RequestModuleDataInfo>(request_m, "RequestModuleDataInfo")
        .def(py::init<>())
        .def_readwrite("moduleId", &lumyn::internal::Request::RequestModuleDataInfo::moduleId);

    py::class_<lumyn::internal::Request::RequestLEDChannelStatusInfo>(request_m, "RequestLEDChannelStatusInfo")
        .def(py::init<>())
        .def_readwrite("channelId", &lumyn::internal::Request::RequestLEDChannelStatusInfo::channelId);

    py::class_<lumyn::internal::Request::RequestLEDZoneStatusInfo>(request_m, "RequestLEDZoneStatusInfo")
        .def(py::init<>())
        .def_readwrite("zoneId", &lumyn::internal::Request::RequestLEDZoneStatusInfo::zoneId);

    py::class_<lumyn::internal::Request::RequestLatestEventInfo>(request_m, "RequestLatestEventInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestEventFlagsInfo>(request_m, "RequestEventFlagsInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Request::RequestConfigFullInfo>(request_m, "RequestConfigFullInfo")
        .def(py::init<>());

    // RequestData union
    py::class_<lumyn::internal::Request::RequestData>(request_m, "RequestData")
        .def(py::init<>())
        .def_property("handshake", [](const lumyn::internal::Request::RequestData &self)
                      { return self.handshake; }, [](lumyn::internal::Request::RequestData &self, const lumyn::internal::Request::RequestHandshakeInfo &v)
                      { self.handshake = v; })
        .def_property("moduleStatus", [](const lumyn::internal::Request::RequestData &self)
                      { return self.moduleStatus; }, [](lumyn::internal::Request::RequestData &self, const lumyn::internal::Request::RequestModuleStatusInfo &v)
                      { self.moduleStatus = v; })
        .def_property("moduleData", [](const lumyn::internal::Request::RequestData &self)
                      { return self.moduleData; }, [](lumyn::internal::Request::RequestData &self, const lumyn::internal::Request::RequestModuleDataInfo &v)
                      { self.moduleData = v; })
        .def_property("ledChannelStatus", [](const lumyn::internal::Request::RequestData &self)
                      { return self.ledChannelStatus; }, [](lumyn::internal::Request::RequestData &self, const lumyn::internal::Request::RequestLEDChannelStatusInfo &v)
                      { self.ledChannelStatus = v; })
        .def_property("ledZoneStatus", [](const lumyn::internal::Request::RequestData &self)
                      { return self.ledZoneStatus; }, [](lumyn::internal::Request::RequestData &self, const lumyn::internal::Request::RequestLEDZoneStatusInfo &v)
                      { self.ledZoneStatus = v; });

    // RequestHeader struct
    py::class_<lumyn::internal::Request::RequestHeader>(request_m, "RequestHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Request::RequestHeader::type)
        .def_readwrite("id", &lumyn::internal::Request::RequestHeader::id);

    // Request struct
    py::class_<lumyn::internal::Request::Request>(request_m, "Request")
        .def(py::init<>())
        .def_readwrite("header", &lumyn::internal::Request::Request::header)
        .def_readwrite("data", &lumyn::internal::Request::Request::data);
  }
}