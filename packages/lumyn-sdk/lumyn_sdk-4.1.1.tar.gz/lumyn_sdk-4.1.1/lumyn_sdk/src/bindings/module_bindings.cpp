#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <lumyn/domain/module/ModuleData.h>
#include <lumyn/domain/module/ModuleDataType.h>
#include <lumyn/domain/module/ModuleInfo.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_module_bindings(py::module &m)
  {
    // Module namespace and types
    auto module_m = m.def_submodule("module", "Module related types");

    // ModuleDataType enum
    py::enum_<lumyn::internal::ModuleData::ModuleDataType>(module_m, "ModuleDataType")
        .value("NewData", lumyn::internal::ModuleData::ModuleDataType::NewData)
        .value("PushData", lumyn::internal::ModuleData::ModuleDataType::PushData)
        .export_values();

    // ModuleConnectionType enum (renamed from SensorConnectionType)
    py::enum_<lumyn::internal::ModuleInfo::ModuleConnectionType>(module_m, "ModuleConnectionType")
        .value("I2C", lumyn::internal::ModuleInfo::ModuleConnectionType::LUMYN_MODULE_CONNECTION_I2C)
        .value("SPI", lumyn::internal::ModuleInfo::ModuleConnectionType::LUMYN_MODULE_CONNECTION_SPI)
        .value("UART", lumyn::internal::ModuleInfo::ModuleConnectionType::LUMYN_MODULE_CONNECTION_UART)
        .value("DIO", lumyn::internal::ModuleInfo::ModuleConnectionType::LUMYN_MODULE_CONNECTION_DIO)
        .value("AIO", lumyn::internal::ModuleInfo::ModuleConnectionType::LUMYN_MODULE_CONNECTION_AIO)
        .export_values();

    // ModuleDataUnitHeader struct
    py::class_<lumyn::internal::ModuleData::ModuleDataUnitHeader>(module_m, "ModuleDataUnitHeader")
        .def(py::init<>())
        .def_readwrite("id", &lumyn::internal::ModuleData::ModuleDataUnitHeader::id)
        .def_readwrite("len", &lumyn::internal::ModuleData::ModuleDataUnitHeader::len);

    // ModulePushData struct
    py::class_<lumyn::internal::ModuleData::ModulePushData>(module_m, "ModulePushData")
        .def(py::init<>())
        .def_readwrite("id", &lumyn::internal::ModuleData::ModulePushData::id)
        .def_readwrite("len", &lumyn::internal::ModuleData::ModulePushData::len);

    // ModuleDataUnion
    py::class_<lumyn::internal::ModuleData::ModuleDataUnion>(module_m, "ModuleDataUnion")
        .def(py::init<>())
        .def_property("dataUnit", [](const lumyn::internal::ModuleData::ModuleDataUnion &u)
                      { return u.dataUnit; }, [](lumyn::internal::ModuleData::ModuleDataUnion &u, const lumyn::internal::ModuleData::ModuleDataUnitHeader &v)
                      { u.dataUnit = v; })
        .def_property("pushData", [](const lumyn::internal::ModuleData::ModuleDataUnion &u)
                      { return u.pushData; }, [](lumyn::internal::ModuleData::ModuleDataUnion &u, const lumyn::internal::ModuleData::ModulePushData &v)
                      { u.pushData = v; });

    // ModuleDataHeader struct
    py::class_<lumyn::internal::ModuleData::ModuleDataHeader>(module_m, "ModuleDataHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::ModuleData::ModuleDataHeader::type)
        .def_readwrite("data", &lumyn::internal::ModuleData::ModuleDataHeader::data);

    // NewData alias for compatibility (points to ModuleDataUnitHeader)
    module_m.attr("NewData") = module_m.attr("ModuleDataUnitHeader");
  }
}