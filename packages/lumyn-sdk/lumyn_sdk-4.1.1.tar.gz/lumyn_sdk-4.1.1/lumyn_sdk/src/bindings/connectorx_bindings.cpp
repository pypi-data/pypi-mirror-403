#include <lumyn/Constants.h> // Required for common headers that reference Constants namespace
#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/types.hpp>
#include <lumyn/cpp/device/builder/AnimationBuilder.hpp>
#include <lumyn/cpp/device/builder/ImageSequenceBuilder.hpp>
#include <lumyn/cpp/device/builder/MatrixTextBuilder.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/types/color.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_connectorx_bindings(py::module &m)
  {
    auto cx_m = m.def_submodule("connectorx", "ConnectorX device types");

    // Animation enum (from C SDK types, aliased in lumyn namespace via types.hpp)
    py::enum_<lumyn_animation_t>(cx_m, "Animation")
        .value("None_", LUMYN_ANIMATION_NONE)
        .value("Fill", LUMYN_ANIMATION_FILL)
        .value("Blink", LUMYN_ANIMATION_BLINK)
        .value("Breathe", LUMYN_ANIMATION_BREATHE)
        .value("RainbowRoll", LUMYN_ANIMATION_RAINBOW_ROLL)
        .value("SineRoll", LUMYN_ANIMATION_SINE_ROLL)
        .value("Chase", LUMYN_ANIMATION_CHASE)
        .value("FadeIn", LUMYN_ANIMATION_FADE_IN)
        .value("FadeOut", LUMYN_ANIMATION_FADE_OUT)
        .value("RainbowCycle", LUMYN_ANIMATION_RAINBOW_CYCLE)
        .value("AlternateBreathe", LUMYN_ANIMATION_ALTERNATE_BREATHE)
        .value("GrowingBreathe", LUMYN_ANIMATION_GROWING_BREATHE)
        .value("Comet", LUMYN_ANIMATION_COMET)
        .value("Sparkle", LUMYN_ANIMATION_SPARKLE)
        .value("Fire", LUMYN_ANIMATION_FIRE)
        .value("Scanner", LUMYN_ANIMATION_SCANNER)
        .value("TheaterChase", LUMYN_ANIMATION_THEATER_CHASE)
        .value("Twinkle", LUMYN_ANIMATION_TWINKLE)
        .value("Meteor", LUMYN_ANIMATION_METEOR)
        .value("Wave", LUMYN_ANIMATION_WAVE)
        .value("Pulse", LUMYN_ANIMATION_PULSE)
        .value("Larson", LUMYN_ANIMATION_LARSON)
        .value("Ripple", LUMYN_ANIMATION_RIPPLE)
        .value("Confetti", LUMYN_ANIMATION_CONFETTI)
        .value("Lava", LUMYN_ANIMATION_LAVA)
        .value("Plasma", LUMYN_ANIMATION_PLASMA)
        .value("Heartbeat", LUMYN_ANIMATION_HEARTBEAT)
        .export_values();

    // Matrix text enums
    py::enum_<lumyn_matrix_text_scroll_direction_t>(cx_m, "MatrixTextScrollDirection")
        .value("LEFT", LUMYN_MATRIX_TEXT_SCROLL_LEFT)
        .value("RIGHT", LUMYN_MATRIX_TEXT_SCROLL_RIGHT)
        .export_values();

    py::enum_<lumyn_matrix_text_font_t>(cx_m, "MatrixTextFont")
        .value("BUILTIN", LUMYN_MATRIX_TEXT_FONT_BUILTIN)
        .value("TINY_3X3", LUMYN_MATRIX_TEXT_FONT_TINY_3X3)
        .value("PICOPIXEL", LUMYN_MATRIX_TEXT_FONT_PICOPIXEL)
        .value("TOM_THUMB", LUMYN_MATRIX_TEXT_FONT_TOM_THUMB)
        .value("ORG_01", LUMYN_MATRIX_TEXT_FONT_ORG_01)
        .value("FREE_MONO_9", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_9)
        .value("FREE_MONO_BOLD_9", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_BOLD_9)
        .value("FREE_SANS_9", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_9)
        .value("FREE_SANS_BOLD_9", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_BOLD_9)
        .value("FREE_SERIF_9", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_9)
        .value("FREE_SERIF_BOLD_9", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_BOLD_9)
        .value("FREE_MONO_12", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_12)
        .value("FREE_MONO_BOLD_12", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_BOLD_12)
        .value("FREE_SANS_12", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_12)
        .value("FREE_SANS_BOLD_12", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_BOLD_12)
        .value("FREE_SERIF_12", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_12)
        .value("FREE_SERIF_BOLD_12", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_BOLD_12)
        .value("FREE_MONO_18", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_18)
        .value("FREE_MONO_BOLD_18", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_BOLD_18)
        .value("FREE_SANS_18", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_18)
        .value("FREE_SANS_BOLD_18", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_BOLD_18)
        .value("FREE_SERIF_18", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_18)
        .value("FREE_SERIF_BOLD_18", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_BOLD_18)
        .value("FREE_MONO_24", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_24)
        .value("FREE_MONO_BOLD_24", LUMYN_MATRIX_TEXT_FONT_FREE_MONO_BOLD_24)
        .value("FREE_SANS_24", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_24)
        .value("FREE_SANS_BOLD_24", LUMYN_MATRIX_TEXT_FONT_FREE_SANS_BOLD_24)
        .value("FREE_SERIF_24", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_24)
        .value("FREE_SERIF_BOLD_24", LUMYN_MATRIX_TEXT_FONT_FREE_SERIF_BOLD_24)
        .export_values();

    py::enum_<lumyn_matrix_text_align_t>(cx_m, "MatrixTextAlign")
        .value("LEFT", LUMYN_MATRIX_TEXT_ALIGN_LEFT)
        .value("CENTER", LUMYN_MATRIX_TEXT_ALIGN_CENTER)
        .value("RIGHT", LUMYN_MATRIX_TEXT_ALIGN_RIGHT)
        .export_values();

    // Color type - bind lumyn_color struct with automatic tuple conversion
    py::class_<lumyn_color>(cx_m, "Color")
        .def(py::init<uint8_t, uint8_t, uint8_t>(), py::arg("r"), py::arg("g"), py::arg("b"), "Create color from RGB values")
        .def(py::init([](py::tuple t)
                      {
            if (t.size() != 3) throw std::runtime_error("Color requires 3 values (r, g, b)");
            return lumyn_color{t[0].cast<uint8_t>(), t[1].cast<uint8_t>(), t[2].cast<uint8_t>()}; }),
             py::arg("rgb"), "Create color from tuple (r, g, b)")
        .def_readwrite("r", &lumyn_color::r)
        .def_readwrite("g", &lumyn_color::g)
        .def_readwrite("b", &lumyn_color::b);

    // Implicit conversion from tuple to lumyn_color
    py::implicitly_convertible<py::tuple, lumyn_color>();

    // AnimationBuilder
    py::class_<lumyn::device::AnimationBuilder>(cx_m, "AnimationBuilder")
        .def("ForZone", &lumyn::device::AnimationBuilder::ForZone, py::arg("zone_id"), py::return_value_policy::reference, "Set the zone for this animation")
        .def("ForGroup", &lumyn::device::AnimationBuilder::ForGroup, py::arg("group_id"), py::return_value_policy::reference, "Set the group for this animation")
        .def("WithColor", &lumyn::device::AnimationBuilder::WithColor, py::arg("color"), py::return_value_policy::reference, "Set the animation color")
        .def("WithDelay", py::overload_cast<uint32_t>(&lumyn::device::AnimationBuilder::WithDelay), py::arg("delay_ms"), py::return_value_policy::reference, "Set the animation delay in milliseconds")
        .def("Reverse", &lumyn::device::AnimationBuilder::Reverse, py::arg("reversed"), py::return_value_policy::reference, "Set whether to reverse the animation")
        .def("RunOnce", &lumyn::device::AnimationBuilder::RunOnce, py::arg("one_shot") = true, py::return_value_policy::reference, "Execute the animation once")
        .def("execute", &lumyn::device::AnimationBuilder::execute, "Execute the animation (continuous loop)")
        // Add snake_case aliases for Python style
        .def("for_zone", &lumyn::device::AnimationBuilder::ForZone, py::arg("zone_id"), py::return_value_policy::reference, "Set the zone for this animation")
        .def("for_group", &lumyn::device::AnimationBuilder::ForGroup, py::arg("group_id"), py::return_value_policy::reference, "Set the group for this animation")
        .def("with_color", &lumyn::device::AnimationBuilder::WithColor, py::arg("color"), py::return_value_policy::reference, "Set the animation color")
        .def("with_delay", py::overload_cast<uint32_t>(&lumyn::device::AnimationBuilder::WithDelay), py::arg("delay_ms"), py::return_value_policy::reference, "Set the animation delay in milliseconds")
        .def("reverse", &lumyn::device::AnimationBuilder::Reverse, py::arg("reversed"), py::return_value_policy::reference, "Set whether to reverse the animation")
        .def("run_once", &lumyn::device::AnimationBuilder::RunOnce, py::arg("one_shot") = true, py::return_value_policy::reference, "Execute the animation once")
        // Expose internal state as readonly properties for testing
        .def_property_readonly("_color", [](const lumyn::device::AnimationBuilder &self)
                               { 
            auto color = self.GetColor();
            return py::make_tuple(color.r, color.g, color.b); })
        .def_property_readonly("_delay_ms", &lumyn::device::AnimationBuilder::GetDelayMs)
        .def_property_readonly("_zone_id", [](const lumyn::device::AnimationBuilder &self) -> py::object
                               { 
            const auto& zone_id = self.GetZoneId();
            return zone_id ? py::cast(*zone_id) : py::none(); })
        .def_property_readonly("_group_id", [](const lumyn::device::AnimationBuilder &self) -> py::object
                               { 
            const auto& group_id = self.GetGroupId();
            return group_id ? py::cast(*group_id) : py::none(); })
        .def_property_readonly("_reversed", &lumyn::device::AnimationBuilder::IsReversed)
        .def_property_readonly("_one_shot", &lumyn::device::AnimationBuilder::IsOneShot)
        .def_property_readonly("_executed", &lumyn::device::AnimationBuilder::isExecuted);

    // ImageSequenceBuilder
    py::class_<lumyn::device::ImageSequenceBuilder>(cx_m, "ImageSequenceBuilder")
        .def("ForZone", &lumyn::device::ImageSequenceBuilder::ForZone, py::arg("zone_id"), py::return_value_policy::reference, "Set the zone for this sequence")
        .def("ForGroup", &lumyn::device::ImageSequenceBuilder::ForGroup, py::arg("group_id"), py::return_value_policy::reference, "Set the group for this sequence")
        .def("WithColor", &lumyn::device::ImageSequenceBuilder::WithColor, py::arg("color"), py::return_value_policy::reference, "Set the sequence color")
        .def("SetColor", &lumyn::device::ImageSequenceBuilder::SetColor, py::arg("set_color"), py::return_value_policy::reference, "Set whether to apply color to the sequence")
        .def("RunOnce", &lumyn::device::ImageSequenceBuilder::RunOnce, py::arg("one_shot") = true, py::return_value_policy::reference, "Execute the sequence once")
        .def("execute", &lumyn::device::ImageSequenceBuilder::execute, "Execute the sequence (continuous loop)")
        // Add snake_case aliases for Python style
        .def("for_zone", &lumyn::device::ImageSequenceBuilder::ForZone, py::arg("zone_id"), py::return_value_policy::reference, "Set the zone for this sequence")
        .def("for_group", &lumyn::device::ImageSequenceBuilder::ForGroup, py::arg("group_id"), py::return_value_policy::reference, "Set the group for this sequence")
        .def("with_color", &lumyn::device::ImageSequenceBuilder::WithColor, py::arg("color"), py::return_value_policy::reference, "Set the sequence color")
        .def("set_color", &lumyn::device::ImageSequenceBuilder::SetColor, py::arg("set_color"), py::return_value_policy::reference, "Set whether to apply color to the sequence")
        .def("run_once", &lumyn::device::ImageSequenceBuilder::RunOnce, py::arg("one_shot") = true, py::return_value_policy::reference, "Execute the sequence once")
        // Expose internal state as readonly properties for testing
        .def_property_readonly("_sequence_id", [](const lumyn::device::ImageSequenceBuilder &self)
                               { return std::string(self.GetSequenceId()); })
        .def_property_readonly("_color", [](const lumyn::device::ImageSequenceBuilder &self)
                               { 
            auto color = self.GetColor();
            return py::make_tuple(color.r, color.g, color.b); })
        .def_property_readonly("_set_color", &lumyn::device::ImageSequenceBuilder::GetSetColor)
        .def_property_readonly("_zone_id", [](const lumyn::device::ImageSequenceBuilder &self) -> py::object
                               { 
            const auto& zone_id = self.GetZoneId();
            return zone_id ? py::cast(*zone_id) : py::none(); })
        .def_property_readonly("_group_id", [](const lumyn::device::ImageSequenceBuilder &self) -> py::object
                               { 
            const auto& group_id = self.GetGroupId();
            return group_id ? py::cast(*group_id) : py::none(); })
        .def_property_readonly("_one_shot", &lumyn::device::ImageSequenceBuilder::IsOneShot)
        .def_property_readonly("_executed", &lumyn::device::ImageSequenceBuilder::isExecuted);

    // MatrixTextBuilder
    py::class_<lumyn::device::MatrixTextBuilder>(cx_m, "MatrixTextBuilder")
        .def("ForZone", &lumyn::device::MatrixTextBuilder::ForZone, py::arg("zone_id"), py::return_value_policy::reference, "Set the zone for this text")
        .def("ForGroup", &lumyn::device::MatrixTextBuilder::ForGroup, py::arg("group_id"), py::return_value_policy::reference, "Set the group for this text")
        .def("WithColor", &lumyn::device::MatrixTextBuilder::WithColor, py::arg("color"), py::return_value_policy::reference, "Set the text color")
        .def("WithDelay", py::overload_cast<uint32_t>(&lumyn::device::MatrixTextBuilder::WithDelay), py::arg("delay_ms"), py::return_value_policy::reference, "Set the scroll delay in milliseconds")
        .def("WithDirection", &lumyn::device::MatrixTextBuilder::WithDirection, py::arg("direction"), py::return_value_policy::reference, "Set the scroll direction")
        .def("WithBackgroundColor", &lumyn::device::MatrixTextBuilder::WithBackgroundColor, py::arg("color"), py::return_value_policy::reference, "Set the background color")
        .def("WithFont", &lumyn::device::MatrixTextBuilder::WithFont, py::arg("font"), py::return_value_policy::reference, "Set the font")
        .def("WithAlign", &lumyn::device::MatrixTextBuilder::WithAlign, py::arg("align"), py::return_value_policy::reference, "Set the text alignment")
        .def("SmoothScroll", &lumyn::device::MatrixTextBuilder::SmoothScroll, py::arg("enabled"), py::return_value_policy::reference, "Enable smooth scrolling")
        .def("ShowBackground", &lumyn::device::MatrixTextBuilder::ShowBackground, py::arg("enabled"), py::return_value_policy::reference, "Show background color")
        .def("PingPong", &lumyn::device::MatrixTextBuilder::PingPong, py::arg("enabled"), py::return_value_policy::reference, "Enable ping-pong scrolling")
        .def("NoScroll", &lumyn::device::MatrixTextBuilder::NoScroll, py::arg("enabled"), py::return_value_policy::reference, "Disable scrolling (static text)")
        .def("WithYOffset", &lumyn::device::MatrixTextBuilder::WithYOffset, py::arg("y_offset"), py::return_value_policy::reference, "Set Y offset for text")
        .def("RunOnce", &lumyn::device::MatrixTextBuilder::RunOnce, py::arg("one_shot") = true, py::return_value_policy::reference, "Execute the text once")
        .def("execute", &lumyn::device::MatrixTextBuilder::execute, "Execute the text (continuous display)")
        // Add snake_case aliases for Python style
        .def("for_zone", &lumyn::device::MatrixTextBuilder::ForZone, py::arg("zone_id"), py::return_value_policy::reference, "Set the zone for this text")
        .def("for_group", &lumyn::device::MatrixTextBuilder::ForGroup, py::arg("group_id"), py::return_value_policy::reference, "Set the group for this text")
        .def("with_color", &lumyn::device::MatrixTextBuilder::WithColor, py::arg("color"), py::return_value_policy::reference, "Set the text color")
        .def("with_delay", py::overload_cast<uint32_t>(&lumyn::device::MatrixTextBuilder::WithDelay), py::arg("delay_ms"), py::return_value_policy::reference, "Set the scroll delay in milliseconds")
        .def("with_direction", &lumyn::device::MatrixTextBuilder::WithDirection, py::arg("direction"), py::return_value_policy::reference, "Set the scroll direction")
        .def("with_background_color", &lumyn::device::MatrixTextBuilder::WithBackgroundColor, py::arg("color"), py::return_value_policy::reference, "Set the background color")
        .def("with_font", &lumyn::device::MatrixTextBuilder::WithFont, py::arg("font"), py::return_value_policy::reference, "Set the font")
        .def("with_align", &lumyn::device::MatrixTextBuilder::WithAlign, py::arg("align"), py::return_value_policy::reference, "Set the text alignment")
        .def("smooth_scroll", &lumyn::device::MatrixTextBuilder::SmoothScroll, py::arg("enabled"), py::return_value_policy::reference, "Enable smooth scrolling")
        .def("show_background", &lumyn::device::MatrixTextBuilder::ShowBackground, py::arg("enabled"), py::return_value_policy::reference, "Show background color")
        .def("ping_pong", &lumyn::device::MatrixTextBuilder::PingPong, py::arg("enabled"), py::return_value_policy::reference, "Enable ping-pong scrolling")
        .def("no_scroll", &lumyn::device::MatrixTextBuilder::NoScroll, py::arg("enabled"), py::return_value_policy::reference, "Disable scrolling (static text)")
        .def("with_y_offset", &lumyn::device::MatrixTextBuilder::WithYOffset, py::arg("y_offset"), py::return_value_policy::reference, "Set Y offset for text")
        .def("run_once", &lumyn::device::MatrixTextBuilder::RunOnce, py::arg("one_shot") = true, py::return_value_policy::reference, "Execute the text once")
        // Expose internal state as readonly properties for testing
        .def_property_readonly("_text", [](const lumyn::device::MatrixTextBuilder &self)
                               { return std::string(self.GetText()); })
        .def_property_readonly("_color", [](const lumyn::device::MatrixTextBuilder &self)
                               { 
            auto color = self.GetColor();
            return py::make_tuple(color.r, color.g, color.b); })
        .def_property_readonly("_delay_ms", &lumyn::device::MatrixTextBuilder::GetDelayMs)
        .def_property_readonly("_direction", &lumyn::device::MatrixTextBuilder::GetDirection)
        .def_property_readonly("_bg_color", [](const lumyn::device::MatrixTextBuilder &self)
                               { 
            auto color = self.GetBgColor();
            return py::make_tuple(color.r, color.g, color.b); })
        .def_property_readonly("_font", &lumyn::device::MatrixTextBuilder::GetFont)
        .def_property_readonly("_align", &lumyn::device::MatrixTextBuilder::GetAlign)
        .def_property_readonly("_y_offset", &lumyn::device::MatrixTextBuilder::GetYOffset)
        .def_property_readonly("_zone_id", [](const lumyn::device::MatrixTextBuilder &self) -> py::object
                               { 
            const auto& zone_id = self.GetZoneId();
            return zone_id ? py::cast(*zone_id) : py::none(); })
        .def_property_readonly("_group_id", [](const lumyn::device::MatrixTextBuilder &self) -> py::object
                               { 
            const auto& group_id = self.GetGroupId();
            return group_id ? py::cast(*group_id) : py::none(); })
        .def_property_readonly("_one_shot", &lumyn::device::MatrixTextBuilder::IsOneShot)
        .def_property_readonly("_executed", &lumyn::device::MatrixTextBuilder::isExecuted);

    // ConnectorX device (from lumyn::device namespace)
    // Inherits LED control methods from BaseConnectorXVariant
    py::class_<lumyn::device::ConnectorX>(cx_m, "ConnectorXInternal")
        .def(py::init<>())
        // Connection management - wrap to return bool instead of lumyn_error_t
        .def("Connect", [](lumyn::device::ConnectorX &self, const std::string &port, std::optional<int> baud_rate) -> bool
             {
               lumyn_error_t result = self.Connect(port, baud_rate);
               if (result != LUMYN_OK) {
                 throw std::runtime_error(std::string("Failed to connect: ") + Lumyn_ErrorString(result));
               }
               return true; }, py::arg("port"), py::arg("baud_rate") = std::nullopt, "Connect to ConnectorX device via serial port")
        .def("Disconnect", &lumyn::device::ConnectorX::Disconnect, "Disconnect from ConnectorX device")
        .def("IsConnected", &lumyn::device::ConnectorX::IsConnected, "Check if connected to device")
        // Event handling
        .def("GetEvents", [](lumyn::device::ConnectorX &self) -> py::list
             {
               // Get events from the device
               auto events = self.GetEvents();
               
               // Convert lumyn::Event to Python-compatible format
               // We return a list of dicts that can be processed by convert_cpp_event_to_python
               py::list result;
               for (const auto& evt : events) {
                 // Create a Python dict representing the event
                 py::dict event_dict;
                 event_dict["type"] = static_cast<int>(evt.getType());
                 
                 // Add data based on type
                 py::dict data_dict;
                 const auto& data = evt.getData();
                 
                 switch (evt.getType()) {
                   case LUMYN_EVENT_DISABLED:
                     data_dict["cause"] = static_cast<int>(data.disabled.cause);
                     break;
                   case LUMYN_EVENT_CONNECTED:
                     data_dict["connection_type"] = static_cast<int>(data.connected.type);
                     break;
                   case LUMYN_EVENT_DISCONNECTED:
                     data_dict["connection_type"] = static_cast<int>(data.disconnected.type);
                     break;
                   case LUMYN_EVENT_ERROR:
                     data_dict["error_type"] = static_cast<int>(data.error.type);
                     data_dict["message"] = std::string(data.error.message, strnlen(data.error.message, sizeof(data.error.message)));
                     break;
                   case LUMYN_EVENT_FATAL_ERROR:
                     data_dict["fatal_error_type"] = static_cast<int>(data.fatal_error.type);
                     data_dict["message"] = std::string(data.fatal_error.message, strnlen(data.fatal_error.message, sizeof(data.fatal_error.message)));
                     break;
                   case LUMYN_EVENT_REGISTERED_ENTITY:
                     data_dict["entity_id"] = data.registered_entity.id;
                     break;
                   case LUMYN_EVENT_CUSTOM:
                     data_dict["custom_type"] = data.custom.type;
                     data_dict["custom_data"] = py::bytes(reinterpret_cast<const char*>(data.custom.data), data.custom.length);
                     break;
                   case LUMYN_EVENT_HEARTBEAT:
                     data_dict["status"] = static_cast<int>(data.heartbeat.status);
                     data_dict["enabled"] = data.heartbeat.enabled;
                     data_dict["connected_usb"] = data.heartbeat.connected_usb;
                     data_dict["can_ok"] = data.heartbeat.can_ok;
                     break;
                   default:
                     // BeginInitialization, FinishInitialization, Enabled, OTA, Module, PinInterrupt - no extra data
                     break;
                 }
                 event_dict["data"] = data_dict;
                 
                 // Add extra message if present
                 const char* extra_msg = evt.getExtraMessage();
                 if (extra_msg) {
                   event_dict["extra_message"] = std::string(extra_msg);
                 }
                 
                 result.append(event_dict);
               }
               return result; }, "Get all events from device as a list of dicts")
        .def("SetAutoPollEvents", &lumyn::device::ConnectorX::SetAutoPollEvents, py::arg("enabled"), "Enable/disable automatic event polling")
        .def("PollEvents", &lumyn::device::ConnectorX::PollEvents, "Manually poll for events")
        // Configuration
        .def("LoadConfigurationFromFile", &lumyn::device::ConnectorX::LoadConfigurationFromFile, py::arg("config_path"), "Load configuration from JSON file")
        .def("ApplyConfigurationJson", &lumyn::device::ConnectorX::ApplyConfigurationJson, py::arg("config_json"), "Apply configuration from JSON string")
        .def("RequestConfig", [](lumyn::device::ConnectorX &self, int timeoutMs)
             {
               std::string configJson;
               auto result = self.RequestConfig(configJson, timeoutMs);
               if (result != LUMYN_OK) return py::none().cast<py::object>();
               return py::str(configJson).cast<py::object>(); }, py::arg("timeout_ms") = 5000, "Request configuration from device")
        // Module data access
        .def("GetLatestModuleData", [](lumyn::device::ConnectorX &self, const std::string &moduleId)
             {
               std::vector<uint8_t> data;
               auto result = self.GetLatestModuleData(moduleId, data);
               if (result != LUMYN_OK) return py::bytes();
               return py::bytes(reinterpret_cast<const char*>(data.data()), data.size()); }, py::arg("module_id"), "Get latest module data as bytes")
        // LED control (from BaseConnectorXVariant)
        .def("SetColor", &lumyn::device::ConnectorX::SetColor, py::arg("zone_id"), py::arg("color"), "Set solid color on zone")
        .def("SetGroupColor", &lumyn::device::ConnectorX::SetGroupColor, py::arg("group_id"), py::arg("color"), "Set solid color on group")
        .def("SetAnimation", &lumyn::device::ConnectorX::SetAnimation, py::arg("animation"), py::return_value_policy::move, "Create an animation builder for the given animation")
        .def("SetImageSequence", &lumyn::device::ConnectorX::SetImageSequence, py::arg("sequence_id"), py::return_value_policy::move, "Create an image sequence builder for the given sequence ID")
        .def("SetText", &lumyn::device::ConnectorX::SetText, py::arg("text"), py::return_value_policy::move, "Create a matrix text builder for the given text")
        .def("SetAnimationSequence", &lumyn::device::ConnectorX::SetAnimationSequence, py::arg("zone_id"), py::arg("sequence_id"), "Play a predefined animation sequence on a zone")
        .def("SetGroupAnimationSequence", &lumyn::device::ConnectorX::SetGroupAnimationSequence, py::arg("group_id"), py::arg("sequence_id"), "Play a predefined animation sequence on a group")
        .def("SendDirectBuffer", py::overload_cast<std::string_view, const uint8_t *, size_t, bool>(&lumyn::device::ConnectorX::SendDirectBuffer), py::arg("zone_id"), py::arg("data"), py::arg("length"), py::arg("delta"), "Send direct LED buffer to zone")
        .def("SendLEDCommand", [](lumyn::device::ConnectorX &self, py::bytes data)
             {
                std::string data_str = data;
                self.SendLEDCommand(data_str.data(), data_str.size()); }, py::arg("data"), py::call_guard<py::gil_scoped_release>(), "Send raw LED command bytes to device")
        .def("SendRawCommand", [](lumyn::device::ConnectorX &self, py::bytes data)
             {
                std::string data_str = data;
                self.SendRawCommand(reinterpret_cast<const uint8_t*>(data_str.data()), data_str.size()); }, py::arg("data"), py::call_guard<py::gil_scoped_release>(), "Send pre-built raw command bytes directly to device")
        // Use RequestConfig() instead of GetConfigManager (which is protected)
        ;
  }
} // namespace lumyn_bindings
