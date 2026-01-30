#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstring>

#include <lumyn/domain/response/Response.h>
#include <lumyn/domain/module/ModuleData.h>
#include <lumyn/domain/event/Event.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_response_bindings(py::module &m)
  {
    // Response namespace and types
    auto response_m = m.def_submodule("response", "Response related types");

    py::class_<lumyn::internal::Response::ResponseStatusInfo>(response_m, "ResponseStatusInfo")
        .def(py::init<>())
        .def_readwrite("status", &lumyn::internal::Response::ResponseStatusInfo::status);

    py::class_<lumyn::internal::Response::ResponseProductSKUInfo>(response_m, "ResponseProductSKUInfo")
        .def(py::init<>())
        .def_readwrite("sku", &lumyn::internal::Response::ResponseProductSKUInfo::sku);

    py::class_<lumyn::internal::Response::ResponseProductSerialNumberInfo>(response_m, "ResponseProductSerialNumberInfo")
        .def(py::init<>())
        .def_readwrite("serialNumber", &lumyn::internal::Response::ResponseProductSerialNumberInfo::serialNumber);

    py::class_<lumyn::internal::Response::ResponseConfigHashInfo>(response_m, "ResponseConfigHashInfo")
        .def(py::init<>())
        .def_property("hash", [](const lumyn::internal::Response::ResponseConfigHashInfo &info)
                      { return py::bytes(reinterpret_cast<const char *>(info.hash), 16); }, [](lumyn::internal::Response::ResponseConfigHashInfo &info, const py::bytes &bytes)
                      {
                    std::string str = bytes;
                    size_t len = std::min(str.size(), size_t(16));
                    std::memcpy(info.hash, str.data(), len); });

    py::class_<lumyn::internal::Response::ResponseAssignedIdInfo>(response_m, "ResponseAssignedIdInfo")
        .def(py::init<>())
        .def_readwrite("valid", &lumyn::internal::Response::ResponseAssignedIdInfo::valid)
        .def_property("id", [](const lumyn::internal::Response::ResponseAssignedIdInfo &info)
                      { return std::string(info.id, strnlen(info.id, 24)); }, [](lumyn::internal::Response::ResponseAssignedIdInfo &info, const std::string &id)
                      {
                    size_t len = std::min(id.size(), size_t(23));
                    std::strncpy(info.id, id.c_str(), len);
                    info.id[len] = '\0'; });

    py::class_<lumyn::internal::Response::ResponseVersionInfo>(response_m, "ResponseVersionInfo")
        .def(py::init<>())
        .def_readwrite("major", &lumyn::internal::Response::ResponseVersionInfo::major)
        .def_readwrite("minor", &lumyn::internal::Response::ResponseVersionInfo::minor)
        .def_readwrite("patch", &lumyn::internal::Response::ResponseVersionInfo::patch);

    py::class_<lumyn::internal::Response::ResponseHandshakeInfo>(response_m, "ResponseHandshakeInfo")
        .def(py::init<>())
        .def_readwrite("status", &lumyn::internal::Response::ResponseHandshakeInfo::status)
        .def_readwrite("sku", &lumyn::internal::Response::ResponseHandshakeInfo::sku)
        .def_readwrite("serNumber", &lumyn::internal::Response::ResponseHandshakeInfo::serNumber)
        .def_readwrite("configHash", &lumyn::internal::Response::ResponseHandshakeInfo::configHash)
        .def_readwrite("assignedId", &lumyn::internal::Response::ResponseHandshakeInfo::assignedId)
        .def_readwrite("version", &lumyn::internal::Response::ResponseHandshakeInfo::version);

    py::class_<lumyn::internal::Response::ResponseFaultsInfo>(response_m, "ResponseFaultsInfo")
        .def(py::init<>())
        .def_readwrite("faultFlags", &lumyn::internal::Response::ResponseFaultsInfo::faultFlags);

    py::class_<lumyn::internal::Response::ResponseModuleStatusInfo>(response_m, "ResponseModuleStatusInfo")
        .def(py::init<>())
        .def_readwrite("moduleId", &lumyn::internal::Response::ResponseModuleStatusInfo::moduleId)
        .def_readwrite("status", &lumyn::internal::Response::ResponseModuleStatusInfo::status);

    py::class_<lumyn::internal::Response::ResponseLEDChannelStatusInfo>(response_m, "ResponseLEDChannelStatusInfo")
        .def(py::init<>())
        .def_readwrite("channelId", &lumyn::internal::Response::ResponseLEDChannelStatusInfo::channelId);

    py::class_<lumyn::internal::Response::ResponseLEDZoneStatusInfo>(response_m, "ResponseLEDZoneStatusInfo")
        .def(py::init<>())
        .def_readwrite("zoneId", &lumyn::internal::Response::ResponseLEDZoneStatusInfo::zoneId);

    py::class_<lumyn::internal::Response::ResponseLatestEventInfo>(response_m, "ResponseLatestEventInfo")
        .def(py::init<>())
        .def_readwrite("eventType", &lumyn::internal::Response::ResponseLatestEventInfo::eventType);

    py::class_<lumyn::internal::Response::ResponseEventFlagsInfo>(response_m, "ResponseEventFlagsInfo")
        .def(py::init<>())
        .def_readwrite("eventFlags", &lumyn::internal::Response::ResponseEventFlagsInfo::eventFlags);

    // ResponseHeader
    py::class_<lumyn::internal::Response::ResponseHeader>(response_m, "ResponseHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Response::ResponseHeader::type)
        .def_readwrite("id", &lumyn::internal::Response::ResponseHeader::id);

    // ResponseData union
    py::class_<lumyn::internal::Response::ResponseData>(response_m, "ResponseData")
        .def(py::init<>())
        .def_property("handshake", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.handshake; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseHandshakeInfo &info)
                      { data.handshake = info; })
        .def_property("status", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.status; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseStatusInfo &info)
                      { data.status = info; })
        .def_property("productSku", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.productSku; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseProductSKUInfo &info)
                      { data.productSku = info; })
        .def_property("productSerialNumber", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.productSerialNumber; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseProductSerialNumberInfo &info)
                      { data.productSerialNumber = info; })
        .def_property("configHash", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.configHash; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseConfigHashInfo &info)
                      { data.configHash = info; })
        .def_property("assignedId", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.assignedId; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseAssignedIdInfo &info)
                      { data.assignedId = info; })
        .def_property("faults", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.faults; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseFaultsInfo &info)
                      { data.faults = info; })
        .def_property("moduleStatus", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.moduleStatus; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseModuleStatusInfo &info)
                      { data.moduleStatus = info; })
        .def_property("moduleData", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.moduleData; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::ModuleData::ModuleDataUnitHeader &info)
                      { data.moduleData = info; })
        .def_property("ledChannelStatus", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.ledChannelStatus; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseLEDChannelStatusInfo &info)
                      { data.ledChannelStatus = info; })
        .def_property("ledZoneStatus", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.ledZoneStatus; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseLEDZoneStatusInfo &info)
                      { data.ledZoneStatus = info; })
        .def_property("latestEvent", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.latestEvent; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseLatestEventInfo &info)
                      { data.latestEvent = info; })
        .def_property("eventFlags", [](const lumyn::internal::Response::ResponseData &data)
                      { return data.eventFlags; }, [](lumyn::internal::Response::ResponseData &data, const lumyn::internal::Response::ResponseEventFlagsInfo &info)
                      { data.eventFlags = info; });

    // Main Response structure
    py::class_<lumyn::internal::Response::Response>(response_m, "Response")
        .def(py::init<>())
        .def_readwrite("header", &lumyn::internal::Response::Response::header)
        .def_readwrite("data", &lumyn::internal::Response::Response::data);
  }
}
