#include <lumyn/Constants.h> // Required for common headers that reference Constants namespace
#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstring>

#include <lumyn/domain/command/Command.h>
#include <lumyn/domain/command/CommandType.h>
#include <lumyn/domain/command/CommandBuilder.h>
#include <lumyn/domain/command/led/LEDCommand.h>
#include <lumyn/domain/command/led/LEDCommandType.h>
#include <lumyn/domain/command/system/SystemCommand.h>
#include <lumyn/domain/command/system/SystemCommandType.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_command_bindings(py::module &m)
  {
    // Command namespace and types
    auto command_m = m.def_submodule("command", "Command related types");

    // CommandType enum (formerly APIGroupType)
    py::enum_<lumyn::internal::Command::CommandType>(command_m, "CommandType")
        .value("System", lumyn::internal::Command::CommandType::System)
        .value("LED", lumyn::internal::Command::CommandType::LED)
        .value("Device", lumyn::internal::Command::CommandType::Device)
        .export_values();

    // LED Command types
    py::enum_<lumyn::internal::Command::LED::LEDCommandType>(command_m, "LEDCommandType")
        .value("SetAnimation", lumyn::internal::Command::LED::LEDCommandType::SetAnimation)
        .value("SetAnimationGroup", lumyn::internal::Command::LED::LEDCommandType::SetAnimationGroup)
        .value("SetColor", lumyn::internal::Command::LED::LEDCommandType::SetColor)
        .value("SetColorGroup", lumyn::internal::Command::LED::LEDCommandType::SetColorGroup)
        .value("SetAnimationSequence", lumyn::internal::Command::LED::LEDCommandType::SetAnimationSequence)
        .value("SetAnimationSequenceGroup", lumyn::internal::Command::LED::LEDCommandType::SetAnimationSequenceGroup)
        .value("SetBitmap", lumyn::internal::Command::LED::LEDCommandType::SetBitmap)
        .value("SetBitmapGroup", lumyn::internal::Command::LED::LEDCommandType::SetBitmapGroup)
        .value("SetMatrixText", lumyn::internal::Command::LED::LEDCommandType::SetMatrixText)
        .value("SetMatrixTextGroup", lumyn::internal::Command::LED::LEDCommandType::SetMatrixTextGroup)
        .value("SetDirectBuffer", lumyn::internal::Command::LED::LEDCommandType::SetDirectBuffer)
        .export_values();

    // System Command types
    py::enum_<lumyn::internal::Command::System::SystemCommandType>(command_m, "SystemCommandType")
        .value("ClearStatusFlag", lumyn::internal::Command::System::SystemCommandType::ClearStatusFlag)
        .value("SetAssignedId", lumyn::internal::Command::System::SystemCommandType::SetAssignedId)
        .value("RestartDevice", lumyn::internal::Command::System::SystemCommandType::RestartDevice)
        .export_values();

    // Matrix Text Scroll Direction
    py::enum_<lumyn::internal::Command::LED::MatrixTextScrollDirection>(command_m, "MatrixTextScrollDirection")
        .value("LEFT", lumyn::internal::Command::LED::MatrixTextScrollDirection::LEFT)
        .value("RIGHT", lumyn::internal::Command::LED::MatrixTextScrollDirection::RIGHT)
        .export_values();

    // Matrix Text Font
    py::enum_<lumyn::internal::Command::LED::MatrixTextFont>(command_m, "MatrixTextFont")
        .value("BUILTIN", lumyn::internal::Command::LED::MatrixTextFont::BUILTIN)
        .value("TINY_3X3", lumyn::internal::Command::LED::MatrixTextFont::TINY_3X3)
        .value("PICOPIXEL", lumyn::internal::Command::LED::MatrixTextFont::PICOPIXEL)
        .value("TOM_THUMB", lumyn::internal::Command::LED::MatrixTextFont::TOM_THUMB)
        .value("ORG_01", lumyn::internal::Command::LED::MatrixTextFont::ORG_01)
        .value("FREE_MONO_9", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_9)
        .value("FREE_MONO_BOLD_9", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_BOLD_9)
        .value("FREE_SANS_9", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_9)
        .value("FREE_SANS_BOLD_9", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_BOLD_9)
        .value("FREE_SERIF_9", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_9)
        .value("FREE_SERIF_BOLD_9", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_BOLD_9)
        .value("FREE_MONO_12", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_12)
        .value("FREE_MONO_BOLD_12", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_BOLD_12)
        .value("FREE_SANS_12", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_12)
        .value("FREE_SANS_BOLD_12", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_BOLD_12)
        .value("FREE_SERIF_12", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_12)
        .value("FREE_SERIF_BOLD_12", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_BOLD_12)
        .value("FREE_MONO_18", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_18)
        .value("FREE_MONO_BOLD_18", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_BOLD_18)
        .value("FREE_SANS_18", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_18)
        .value("FREE_SANS_BOLD_18", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_BOLD_18)
        .value("FREE_SERIF_18", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_18)
        .value("FREE_SERIF_BOLD_18", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_BOLD_18)
        .value("FREE_MONO_24", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_24)
        .value("FREE_MONO_BOLD_24", lumyn::internal::Command::LED::MatrixTextFont::FREE_MONO_BOLD_24)
        .value("FREE_SANS_24", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_24)
        .value("FREE_SANS_BOLD_24", lumyn::internal::Command::LED::MatrixTextFont::FREE_SANS_BOLD_24)
        .value("FREE_SERIF_24", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_24)
        .value("FREE_SERIF_BOLD_24", lumyn::internal::Command::LED::MatrixTextFont::FREE_SERIF_BOLD_24)
        .export_values();

    // Matrix Text Align
    py::enum_<lumyn::internal::Command::LED::MatrixTextAlign>(command_m, "MatrixTextAlign")
        .value("LEFT", lumyn::internal::Command::LED::MatrixTextAlign::LEFT)
        .value("CENTER", lumyn::internal::Command::LED::MatrixTextAlign::CENTER)
        .value("RIGHT", lumyn::internal::Command::LED::MatrixTextAlign::RIGHT)
        .export_values();

    // Matrix Text Flags structure
    py::class_<lumyn::internal::Command::LED::MatrixTextFlags>(command_m, "MatrixTextFlags")
        .def(py::init<>())
        .def_property("smoothScroll", [](const lumyn::internal::Command::LED::MatrixTextFlags &self)
                      { return static_cast<bool>(self.smoothScroll); }, [](lumyn::internal::Command::LED::MatrixTextFlags &self, bool value)
                      { self.smoothScroll = value ? 1 : 0; })
        .def_property("showBackground", [](const lumyn::internal::Command::LED::MatrixTextFlags &self)
                      { return static_cast<bool>(self.showBackground); }, [](lumyn::internal::Command::LED::MatrixTextFlags &self, bool value)
                      { self.showBackground = value ? 1 : 0; })
        .def_property("pingPong", [](const lumyn::internal::Command::LED::MatrixTextFlags &self)
                      { return static_cast<bool>(self.pingPong); }, [](lumyn::internal::Command::LED::MatrixTextFlags &self, bool value)
                      { self.pingPong = value ? 1 : 0; })
        .def_property("noScroll", [](const lumyn::internal::Command::LED::MatrixTextFlags &self)
                      { return static_cast<bool>(self.noScroll); }, [](lumyn::internal::Command::LED::MatrixTextFlags &self, bool value)
                      { self.noScroll = value ? 1 : 0; })
        .def_property_readonly("reserved", [](const lumyn::internal::Command::LED::MatrixTextFlags &self)
                               { return static_cast<uint8_t>(self.reserved); });

    // LED AnimationColor structure
    py::class_<lumyn::internal::Command::LED::AnimationColor>(command_m, "AnimationColor")
        .def(py::init<>())
        .def_readwrite("r", &lumyn::internal::Command::LED::AnimationColor::r)
        .def_readwrite("g", &lumyn::internal::Command::LED::AnimationColor::g)
        .def_readwrite("b", &lumyn::internal::Command::LED::AnimationColor::b);

    // LED SetAnimationData structure
    py::class_<lumyn::internal::Command::LED::SetAnimationData>(command_m, "SetAnimationData")
        .def(py::init<>())
        .def_readwrite("zoneId", &lumyn::internal::Command::LED::SetAnimationData::zoneId)
        .def_readwrite("animationId", &lumyn::internal::Command::LED::SetAnimationData::animationId)
        .def_readwrite("delay", &lumyn::internal::Command::LED::SetAnimationData::delay)
        .def_readwrite("color", &lumyn::internal::Command::LED::SetAnimationData::color)
        .def_property("reversed", [](const lumyn::internal::Command::LED::SetAnimationData &self)
                      { return static_cast<bool>(self.reversed); }, [](lumyn::internal::Command::LED::SetAnimationData &self, bool value)
                      { self.reversed = value ? 1 : 0; })
        .def_property("oneShot", [](const lumyn::internal::Command::LED::SetAnimationData &self)
                      { return static_cast<bool>(self.oneShot); }, [](lumyn::internal::Command::LED::SetAnimationData &self, bool value)
                      { self.oneShot = value ? 1 : 0; });

    // SetColorData struct
    py::class_<lumyn::internal::Command::LED::SetColorData>(command_m, "SetColorData")
        .def(py::init<>())
        .def_readwrite("zoneId", &lumyn::internal::Command::LED::SetColorData::zoneId)
        .def_readwrite("color", &lumyn::internal::Command::LED::SetColorData::color);

    // Matrix text data structs
    py::class_<lumyn::internal::Command::LED::SetMatrixTextData>(command_m, "SetMatrixTextData")
        .def(py::init<>())
        .def_readwrite("zoneId", &lumyn::internal::Command::LED::SetMatrixTextData::zoneId)
        .def_readwrite("oneShot", &lumyn::internal::Command::LED::SetMatrixTextData::oneShot)
        .def_readwrite("color", &lumyn::internal::Command::LED::SetMatrixTextData::color)
        .def_readwrite("dir", &lumyn::internal::Command::LED::SetMatrixTextData::dir)
        .def_property("text", [](const lumyn::internal::Command::LED::SetMatrixTextData &self)
                      { return std::string(self.text, strnlen(self.text, 24)); }, [](lumyn::internal::Command::LED::SetMatrixTextData &self, const std::string &text)
                      { strncpy(self.text, text.c_str(), 24); })
        .def_readwrite("length", &lumyn::internal::Command::LED::SetMatrixTextData::length)
        .def_readwrite("delay", &lumyn::internal::Command::LED::SetMatrixTextData::delay)
        .def_readwrite("bgColor", &lumyn::internal::Command::LED::SetMatrixTextData::bgColor)
        .def_readwrite("font", &lumyn::internal::Command::LED::SetMatrixTextData::font)
        .def_readwrite("align", &lumyn::internal::Command::LED::SetMatrixTextData::align)
        .def_readwrite("flags", &lumyn::internal::Command::LED::SetMatrixTextData::flags)
        .def_readwrite("yOffset", &lumyn::internal::Command::LED::SetMatrixTextData::yOffset);

    py::class_<lumyn::internal::Command::LED::SetMatrixTextGroupData>(command_m, "SetMatrixTextGroupData")
        .def(py::init<>())
        .def_readwrite("groupId", &lumyn::internal::Command::LED::SetMatrixTextGroupData::groupId)
        .def_readwrite("oneShot", &lumyn::internal::Command::LED::SetMatrixTextGroupData::oneShot)
        .def_readwrite("color", &lumyn::internal::Command::LED::SetMatrixTextGroupData::color)
        .def_readwrite("dir", &lumyn::internal::Command::LED::SetMatrixTextGroupData::dir)
        .def_property("text", [](const lumyn::internal::Command::LED::SetMatrixTextGroupData &self)
                      { return std::string(self.text, strnlen(self.text, 24)); }, [](lumyn::internal::Command::LED::SetMatrixTextGroupData &self, const std::string &text)
                      { strncpy(self.text, text.c_str(), 24); })
        .def_readwrite("length", &lumyn::internal::Command::LED::SetMatrixTextGroupData::length)
        .def_readwrite("delay", &lumyn::internal::Command::LED::SetMatrixTextGroupData::delay)
        .def_readwrite("bgColor", &lumyn::internal::Command::LED::SetMatrixTextGroupData::bgColor)
        .def_readwrite("font", &lumyn::internal::Command::LED::SetMatrixTextGroupData::font)
        .def_readwrite("align", &lumyn::internal::Command::LED::SetMatrixTextGroupData::align)
        .def_readwrite("flags", &lumyn::internal::Command::LED::SetMatrixTextGroupData::flags)
        .def_readwrite("yOffset", &lumyn::internal::Command::LED::SetMatrixTextGroupData::yOffset);

    // LED Command Data union
    py::class_<lumyn::internal::Command::LED::LEDCommandData>(command_m, "LEDCommandData")
        .def(py::init<>())
        .def_property("setAnimation", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setAnimation; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetAnimationData &data)
                      { self.setAnimation = data; })
        .def_property("setColor", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setColor; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetColorData &data)
                      { self.setColor = data; })
        .def_property("setMatrixText", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setMatrixText; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetMatrixTextData &data)
                      { self.setMatrixText = data; })
        .def_property("setMatrixTextGroup", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setMatrixTextGroup; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetMatrixTextGroupData &data)
                      { self.setMatrixTextGroup = data; })
        .def_property("setBitmap", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setBitmap; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetBitmapData &data)
                      { self.setBitmap = data; })
        .def_property("setBitmapGroup", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setBitmapGroup; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetBitmapGroupData &data)
                      { self.setBitmapGroup = data; })
        .def_property("setAnimationGroup", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setAnimationGroup; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetAnimationGroupData &data)
                      { self.setAnimationGroup = data; })
        .def_property("setAnimationSequence", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setAnimationSequence; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetAnimationSequenceData &data)
                      { self.setAnimationSequence = data; })
        .def_property("setAnimationSequenceGroup", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setAnimationSequenceGroup; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetAnimationSequenceGroupData &data)
                      { self.setAnimationSequenceGroup = data; })
        .def_property("setDirectBuffer", [](const lumyn::internal::Command::LED::LEDCommandData &self)
                      { return self.setDirectBuffer; }, [](lumyn::internal::Command::LED::LEDCommandData &self, const lumyn::internal::Command::LED::SetDirectBufferData &data)
                      { self.setDirectBuffer = data; });

    // LED Command structure
    py::class_<lumyn::internal::Command::LED::LEDCommand>(command_m, "LEDCommand")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Command::LED::LEDCommand::type)
        .def_readwrite("data", &lumyn::internal::Command::LED::LEDCommand::data);

    // System Command Data structs
    py::class_<lumyn::internal::Command::System::ClearStatusFlagData>(command_m, "ClearStatusFlagData")
        .def(py::init<>())
        .def_readwrite("mask", &lumyn::internal::Command::System::ClearStatusFlagData::mask);

    py::class_<lumyn::internal::Command::System::SetAssignedIdData>(command_m, "SetAssignedIdData")
        .def(py::init<>())
        .def_property("id", [](const lumyn::internal::Command::System::SetAssignedIdData &self)
                      { return std::string(self.id, strnlen(self.id, 24)); }, [](lumyn::internal::Command::System::SetAssignedIdData &self, const std::string &id)
                      { strncpy(self.id, id.c_str(), 24); });

    py::class_<lumyn::internal::Command::System::RestartDeviceData>(command_m, "RestartDeviceData")
        .def(py::init<>())
        .def_readwrite("delayMs", &lumyn::internal::Command::System::RestartDeviceData::delayMs);

    // System Command Data union
    py::class_<lumyn::internal::Command::System::SystemCommandData>(command_m, "SystemCommandData")
        .def(py::init<>())
        .def_property("clearStatusFlag", [](const lumyn::internal::Command::System::SystemCommandData &self)
                      { return self.clearStatusFlag; }, [](lumyn::internal::Command::System::SystemCommandData &self, const lumyn::internal::Command::System::ClearStatusFlagData &d)
                      { self.clearStatusFlag = d; })
        .def_property("assignedId", [](const lumyn::internal::Command::System::SystemCommandData &self)
                      { return self.assignedId; }, [](lumyn::internal::Command::System::SystemCommandData &self, const lumyn::internal::Command::System::SetAssignedIdData &d)
                      { self.assignedId = d; })
        .def_property("restartDevice", [](const lumyn::internal::Command::System::SystemCommandData &self)
                      { return self.restartDevice; }, [](lumyn::internal::Command::System::SystemCommandData &self, const lumyn::internal::Command::System::RestartDeviceData &d)
                      { self.restartDevice = d; });

    // System Command structure
    py::class_<lumyn::internal::Command::System::SystemCommand>(command_m, "SystemCommand")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Command::System::SystemCommand::type)
        .def_readwrite("data", &lumyn::internal::Command::System::SystemCommand::data);

    // CommandHeader structure
    py::class_<lumyn::internal::Command::CommandHeader>(command_m, "CommandHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Command::CommandHeader::type)
        .def_property("ledType", [](const lumyn::internal::Command::CommandHeader &self)
                      { return self.ledType; }, [](lumyn::internal::Command::CommandHeader &self, lumyn::internal::Command::LED::LEDCommandType t)
                      { self.ledType = t; })
        .def_property("systemType", [](const lumyn::internal::Command::CommandHeader &self)
                      { return self.systemType; }, [](lumyn::internal::Command::CommandHeader &self, lumyn::internal::Command::System::SystemCommandType t)
                      { self.systemType = t; });

    // CommandBuilder - for building command buffers to verify serialization
    py::class_<lumyn::internal::Command::CommandBuilder>(command_m, "CommandBuilder")
        .def_static("build", [](const lumyn::internal::Command::CommandHeader &header, py::bytes body) -> py::bytes
                    {
                std::string body_str = body;
                auto result = lumyn::internal::Command::CommandBuilder::build(
                    header, body_str.data(), body_str.size());
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("header"), py::arg("body") = py::bytes())
        .def_static("buildSetAnimation", [](uint16_t zoneId, uint16_t animationId, lumyn::internal::Command::LED::AnimationColor color, uint16_t delay, bool reversed, bool oneShot) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetAnimation(
                    zoneId, animationId, color, delay, reversed, oneShot);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("zone_id"), py::arg("animation_id"), py::arg("color"), py::arg("delay") = 250, py::arg("reversed") = false, py::arg("one_shot") = false)
        .def_static("buildSetAnimationGroup", [](uint16_t groupId, uint16_t animationId, lumyn::internal::Command::LED::AnimationColor color, uint16_t delay, bool reversed, bool oneShot) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetAnimationGroup(
                    groupId, animationId, color, delay, reversed, oneShot);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("group_id"), py::arg("animation_id"), py::arg("color"), py::arg("delay") = 250, py::arg("reversed") = false, py::arg("one_shot") = false)
        .def_static("buildSetColor", [](uint16_t zoneId, lumyn::internal::Command::LED::AnimationColor color) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetColor(zoneId, color);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("zone_id"), py::arg("color"))
        .def_static("buildSetColorGroup", [](uint16_t groupId, lumyn::internal::Command::LED::AnimationColor color) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetColorGroup(groupId, color);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("group_id"), py::arg("color"))
        .def_static("buildSetAnimationSequence", [](uint16_t zoneId, uint16_t sequenceId) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetAnimationSequence(zoneId, sequenceId);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("zone_id"), py::arg("sequence_id"))
        .def_static("buildSetAnimationSequenceGroup", [](uint16_t groupId, uint16_t sequenceId) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetAnimationSequenceGroup(groupId, sequenceId);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("group_id"), py::arg("sequence_id"))
        .def_static("buildSetBitmap", [](uint16_t zoneId, uint16_t bitmapId, lumyn::internal::Command::LED::AnimationColor color, bool setColor, bool oneShot) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetBitmap(
                    zoneId, bitmapId, color, setColor, oneShot);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("zone_id"), py::arg("bitmap_id"), py::arg("color"), py::arg("set_color") = false, py::arg("one_shot") = false)
        .def_static("buildSetBitmapGroup", [](uint16_t groupId, uint16_t bitmapId, lumyn::internal::Command::LED::AnimationColor color, bool setColor, bool oneShot) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetBitmapGroup(
                    groupId, bitmapId, color, setColor, oneShot);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("group_id"), py::arg("bitmap_id"), py::arg("color"), py::arg("set_color") = false, py::arg("one_shot") = false)
        .def_static("buildSetMatrixText", [](uint16_t zoneId, const std::string &text, lumyn::internal::Command::LED::AnimationColor color, lumyn::internal::Command::LED::MatrixTextScrollDirection dir, uint16_t delay, bool oneShot, lumyn::internal::Command::LED::AnimationColor bgColor, lumyn::internal::Command::LED::MatrixTextFont font, lumyn::internal::Command::LED::MatrixTextAlign align, lumyn::internal::Command::LED::MatrixTextFlags flags, int8_t yOffset) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetMatrixText(
                    zoneId, text, color, dir, delay, oneShot, bgColor, font, align, flags, yOffset);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("zone_id"), py::arg("text"), py::arg("color"), py::arg("direction") = lumyn::internal::Command::LED::MatrixTextScrollDirection::LEFT, py::arg("delay") = 500, py::arg("one_shot") = false, py::arg("bg_color") = lumyn::internal::Command::LED::AnimationColor(), py::arg("font") = lumyn::internal::Command::LED::MatrixTextFont::BUILTIN, py::arg("align") = lumyn::internal::Command::LED::MatrixTextAlign::LEFT, py::arg("flags") = lumyn::internal::Command::LED::MatrixTextFlags{}, py::arg("y_offset") = 0)
        .def_static("buildSetMatrixTextGroup", [](uint16_t groupId, const std::string &text, lumyn::internal::Command::LED::AnimationColor color, lumyn::internal::Command::LED::MatrixTextScrollDirection dir, uint16_t delay, bool oneShot, lumyn::internal::Command::LED::AnimationColor bgColor, lumyn::internal::Command::LED::MatrixTextFont font, lumyn::internal::Command::LED::MatrixTextAlign align, lumyn::internal::Command::LED::MatrixTextFlags flags, int8_t yOffset) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetMatrixTextGroup(
                    groupId, text, color, dir, delay, oneShot, bgColor, font, align, flags, yOffset);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("group_id"), py::arg("text"), py::arg("color"), py::arg("direction") = lumyn::internal::Command::LED::MatrixTextScrollDirection::LEFT, py::arg("delay") = 500, py::arg("one_shot") = false, py::arg("bg_color") = lumyn::internal::Command::LED::AnimationColor(), py::arg("font") = lumyn::internal::Command::LED::MatrixTextFont::BUILTIN, py::arg("align") = lumyn::internal::Command::LED::MatrixTextAlign::LEFT, py::arg("flags") = lumyn::internal::Command::LED::MatrixTextFlags{}, py::arg("y_offset") = 0)
        .def_static("buildSetDirectBuffer", [](uint16_t zoneId, py::bytes data, uint16_t length, bool isDelta) -> py::bytes
                    {
                std::string data_str = data;
                auto result = lumyn::internal::Command::CommandBuilder::buildSetDirectBuffer(
                    zoneId, reinterpret_cast<const uint8_t*>(data_str.c_str()), length, isDelta);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("zone_id"), py::arg("data"), py::arg("length"), py::arg("is_delta"))
        .def_static("buildClearStatusFlag", [](uint32_t flags) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildClearStatusFlag(flags);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("flags"))
        .def_static("buildSetAssignedId", [](const std::string &assignedId) -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildSetAssignedId(assignedId);
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); }, py::arg("assigned_id"))
        .def_static("buildRestartDevice", []() -> py::bytes
                    {
                auto result = lumyn::internal::Command::CommandBuilder::buildRestartDevice();
                return py::bytes(reinterpret_cast<const char *>(result.data()), result.size()); });
  }
}
