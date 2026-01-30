#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstring>

#include <lumyn/domain/event/Event.h>
#include <lumyn/domain/event/EventType.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_event_bindings(py::module &m)
  {
    // Event namespace and types
    auto event_m = m.def_submodule("event", "Event related types");

    py::enum_<lumyn::internal::Eventing::EventType>(event_m, "EventType")
        .value("BeginInitialization", lumyn::internal::Eventing::EventType::BeginInitialization)
        .value("FinishInitialization", lumyn::internal::Eventing::EventType::FinishInitialization)
        .value("Enabled", lumyn::internal::Eventing::EventType::Enabled)
        .value("Disabled", lumyn::internal::Eventing::EventType::Disabled)
        .value("Connected", lumyn::internal::Eventing::EventType::Connected)
        .value("Disconnected", lumyn::internal::Eventing::EventType::Disconnected)
        .value("Error", lumyn::internal::Eventing::EventType::Error)
        .value("FatalError", lumyn::internal::Eventing::EventType::FatalError)
        .value("RegisteredEntity", lumyn::internal::Eventing::EventType::RegisteredEntity)
        .value("Custom", lumyn::internal::Eventing::EventType::Custom)
        .value("PinInterrupt", lumyn::internal::Eventing::EventType::PinInterrupt)
        .value("HeartBeat", lumyn::internal::Eventing::EventType::HeartBeat)
        .export_values();

    py::enum_<lumyn::internal::Eventing::Status>(event_m, "Status")
        .value("Unknown", lumyn::internal::Eventing::Status::Unknown)
        .value("Booting", lumyn::internal::Eventing::Status::Booting)
        .value("Active", lumyn::internal::Eventing::Status::Active)
        .value("Error", lumyn::internal::Eventing::Status::Error)
        .value("Fatal", lumyn::internal::Eventing::Status::Fatal)
        .export_values();

    py::enum_<lumyn::internal::Eventing::DisabledCause>(event_m, "DisabledCause")
        .value("NoHeartbeat", lumyn::internal::Eventing::DisabledCause::NoHeartbeat)
        .value("Manual", lumyn::internal::Eventing::DisabledCause::Manual)
        .value("EStop", lumyn::internal::Eventing::DisabledCause::EStop)
        .value("Restart", lumyn::internal::Eventing::DisabledCause::Restart)
        .export_values();

    py::enum_<lumyn::internal::Eventing::ConnectionType>(event_m, "ConnectionType")
        .value("USB", lumyn::internal::Eventing::ConnectionType::USB)
        .value("WebUSB", lumyn::internal::Eventing::ConnectionType::WebUSB)
        .value("I2C", lumyn::internal::Eventing::ConnectionType::I2C)
        .value("CAN", lumyn::internal::Eventing::ConnectionType::CAN)
        .value("UART", lumyn::internal::Eventing::ConnectionType::UART)
        .export_values();

    py::enum_<lumyn::internal::Eventing::ErrorType>(event_m, "ErrorType")
        .value("FileNotFound", lumyn::internal::Eventing::ErrorType::FileNotFound)
        .value("InvalidFile", lumyn::internal::Eventing::ErrorType::InvalidFile)
        .value("EntityNotFound", lumyn::internal::Eventing::ErrorType::EntityNotFound)
        .value("DeviceMalfunction", lumyn::internal::Eventing::ErrorType::DeviceMalfunction)
        .value("QueueFull", lumyn::internal::Eventing::ErrorType::QueueFull)
        .value("LedStrip", lumyn::internal::Eventing::ErrorType::LedStrip)
        .value("LedMatrix", lumyn::internal::Eventing::ErrorType::LedMatrix)
        .value("InvalidAnimationSequence", lumyn::internal::Eventing::ErrorType::InvalidAnimationSequence)
        .value("InvalidChannel", lumyn::internal::Eventing::ErrorType::InvalidChannel)
        .value("DuplicateID", lumyn::internal::Eventing::ErrorType::DuplicateID)
        .value("InvalidConfigUpload", lumyn::internal::Eventing::ErrorType::InvalidConfigUpload)
        .value("ModuleError", lumyn::internal::Eventing::ErrorType::ModuleError)
        .export_values();

    py::enum_<lumyn::internal::Eventing::FatalErrorType>(event_m, "FatalErrorType")
        .value("InitError", lumyn::internal::Eventing::FatalErrorType::InitError)
        .value("BadConfig", lumyn::internal::Eventing::FatalErrorType::BadConfig)
        .value("StartTask", lumyn::internal::Eventing::FatalErrorType::StartTask)
        .value("CreateQueue", lumyn::internal::Eventing::FatalErrorType::CreateQueue)
        .export_values();

    // Event info structures
    py::class_<lumyn::internal::Eventing::BeginInitInfo>(event_m, "BeginInitInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Eventing::FinishInitInfo>(event_m, "FinishInitInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Eventing::EnabledInfo>(event_m, "EnabledInfo")
        .def(py::init<>());

    py::class_<lumyn::internal::Eventing::DisabledInfo>(event_m, "DisabledInfo")
        .def(py::init<>())
        .def_readwrite("cause", &lumyn::internal::Eventing::DisabledInfo::cause);

    py::class_<lumyn::internal::Eventing::ConnectedInfo>(event_m, "ConnectedInfo")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Eventing::ConnectedInfo::type);

    py::class_<lumyn::internal::Eventing::DisconnectedInfo>(event_m, "DisconnectedInfo")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Eventing::DisconnectedInfo::type);

    py::class_<lumyn::internal::Eventing::ErrorInfo>(event_m, "ErrorInfo")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Eventing::ErrorInfo::type)
        .def_property("message", [](const lumyn::internal::Eventing::ErrorInfo &info)
                      { return std::string(info.message, strnlen(info.message, 16)); }, [](lumyn::internal::Eventing::ErrorInfo &info, const std::string &message)
                      {
                    size_t len = std::min(message.size(), size_t(15));
                    std::strncpy(info.message, message.c_str(), len);
                    info.message[len] = '\0'; });

    py::class_<lumyn::internal::Eventing::FatalErrorInfo>(event_m, "FatalErrorInfo")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Eventing::FatalErrorInfo::type)
        .def_property("message", [](const lumyn::internal::Eventing::FatalErrorInfo &info)
                      { return std::string(info.message, strnlen(info.message, 16)); }, [](lumyn::internal::Eventing::FatalErrorInfo &info, const std::string &message)
                      {
                    size_t len = std::min(message.size(), size_t(15));
                    std::strncpy(info.message, message.c_str(), len);
                    info.message[len] = '\0'; });

    py::class_<lumyn::internal::Eventing::RegisteredEntityInfo>(event_m, "RegisteredEntityInfo")
        .def(py::init<>())
        .def_readwrite("id", &lumyn::internal::Eventing::RegisteredEntityInfo::id);

    py::class_<lumyn::internal::Eventing::CustomInfo>(event_m, "CustomInfo")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Eventing::CustomInfo::type)
        .def_readwrite("length", &lumyn::internal::Eventing::CustomInfo::length)
        .def_property("data", [](const lumyn::internal::Eventing::CustomInfo &info)
                      { return py::bytes(reinterpret_cast<const char *>(info.data), info.length); }, [](lumyn::internal::Eventing::CustomInfo &info, const py::bytes &bytes)
                      {
                    std::string str = bytes;
                    size_t len = std::min(str.size(), size_t(16));
                    std::memcpy(info.data, str.data(), len);
                    info.length = static_cast<uint8_t>(len); });

    py::class_<lumyn::internal::Eventing::PinInterruptInfo>(event_m, "PinInterruptInfo")
        .def(py::init<>())
        .def_readwrite("pin", &lumyn::internal::Eventing::PinInterruptInfo::pin);

    py::class_<lumyn::internal::Eventing::HeartBeatInfo>(event_m, "HeartBeatInfo")
        .def(py::init<>())
        .def_readwrite("status", &lumyn::internal::Eventing::HeartBeatInfo::status)
        .def_readwrite("enabled", &lumyn::internal::Eventing::HeartBeatInfo::enabled)
        .def_readwrite("connectedUSB", &lumyn::internal::Eventing::HeartBeatInfo::connectedUSB)
        .def_readwrite("canOK", &lumyn::internal::Eventing::HeartBeatInfo::canOK);

    py::class_<lumyn::internal::Eventing::ErrorFlags>(event_m, "ErrorFlags")
        .def(py::init<>())
        .def("raiseError", py::overload_cast<lumyn::internal::Eventing::ErrorType>(&lumyn::internal::Eventing::ErrorFlags::raiseError))
        .def("raiseError", py::overload_cast<lumyn::internal::Eventing::FatalErrorType>(&lumyn::internal::Eventing::ErrorFlags::raiseError))
        .def("clearError", py::overload_cast<lumyn::internal::Eventing::ErrorType>(&lumyn::internal::Eventing::ErrorFlags::clearError))
        .def("clearError", py::overload_cast<lumyn::internal::Eventing::FatalErrorType>(&lumyn::internal::Eventing::ErrorFlags::clearError))
        .def("clearError", py::overload_cast<uint32_t>(&lumyn::internal::Eventing::ErrorFlags::clearError))
        .def("isErrorSet", py::overload_cast<lumyn::internal::Eventing::ErrorType>(&lumyn::internal::Eventing::ErrorFlags::isErrorSet, py::const_))
        .def("isErrorSet", py::overload_cast<lumyn::internal::Eventing::FatalErrorType>(&lumyn::internal::Eventing::ErrorFlags::isErrorSet, py::const_))
        .def_property_readonly("errors", [](const lumyn::internal::Eventing::ErrorFlags &flags)
                               { return flags.errors; })
        .def_property_readonly("nonFatalErrors", [](const lumyn::internal::Eventing::ErrorFlags &flags)
                               { return flags.nonFatalErrors; })
        .def_property_readonly("fatalErrors", [](const lumyn::internal::Eventing::ErrorFlags &flags)
                               { return flags.fatalErrors; });

    // EventData union
    py::class_<lumyn::internal::Eventing::EventData>(event_m, "EventData")
        .def(py::init<>())
        .def_property("beginInit", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.beginInit; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::BeginInitInfo &info)
                      { data.beginInit = info; })
        .def_property("finishInit", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.finishInit; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::FinishInitInfo &info)
                      { data.finishInit = info; })
        .def_property("enabled", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.enabled; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::EnabledInfo &info)
                      { data.enabled = info; })
        .def_property("disabled", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.disabled; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::DisabledInfo &info)
                      { data.disabled = info; })
        .def_property("connected", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.connected; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::ConnectedInfo &info)
                      { data.connected = info; })
        .def_property("disconnected", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.disconnected; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::DisconnectedInfo &info)
                      { data.disconnected = info; })
        .def_property("error", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.error; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::ErrorInfo &info)
                      { data.error = info; })
        .def_property("fatalError", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.fatalError; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::FatalErrorInfo &info)
                      { data.fatalError = info; })
        .def_property("registeredEntity", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.registeredEntity; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::RegisteredEntityInfo &info)
                      { data.registeredEntity = info; })
        .def_property("custom", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.custom; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::CustomInfo &info)
                      { data.custom = info; })
        .def_property("pinInterrupt", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.pinInterrupt; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::PinInterruptInfo &info)
                      { data.pinInterrupt = info; })
        .def_property("heartBeat", [](const lumyn::internal::Eventing::EventData &data)
                      { return data.heartBeat; }, [](lumyn::internal::Eventing::EventData &data, const lumyn::internal::Eventing::HeartBeatInfo &info)
                      { data.heartBeat = info; });

    // EventHeader structure
    py::class_<lumyn::internal::Eventing::EventHeader>(event_m, "EventHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Eventing::EventHeader::type)
        .def_readwrite("data", &lumyn::internal::Eventing::EventHeader::data);

    // Main Event structure
    py::class_<lumyn::internal::Eventing::Event>(event_m, "Event")
        .def(py::init<>())
        .def(py::init<lumyn::internal::Eventing::EventHeader>())
        .def(py::init<lumyn::internal::Eventing::EventHeader, const char *>())
        .def_readwrite("header", &lumyn::internal::Eventing::Event::header)
        .def("setExtraMessage",
             py::overload_cast<const char *>(&lumyn::internal::Eventing::Event::setExtraMessage))
        .def("getExtraMessage", [](const lumyn::internal::Eventing::Event &evt)
             {
                auto* msg = evt.getExtraMessage();
                if (!msg) return py::bytes();
                return py::bytes(reinterpret_cast<const char*>(msg), evt.getExtraMessageLength()); })
        .def("getExtraMessageStr", [](const lumyn::internal::Eventing::Event &evt)
             {
                auto* str = evt.getExtraMessageStr();
                return str ? std::string(str, evt.getExtraMessageLength()) : std::string(); })
        .def("getExtraMessageLength", &lumyn::internal::Eventing::Event::getExtraMessageLength)
        .def("hasExtraMessage", &lumyn::internal::Eventing::Event::hasExtraMessage);
  }
}