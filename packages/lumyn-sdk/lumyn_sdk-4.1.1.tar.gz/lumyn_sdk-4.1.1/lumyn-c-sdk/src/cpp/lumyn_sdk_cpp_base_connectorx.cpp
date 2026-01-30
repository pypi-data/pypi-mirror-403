#include "lumyn/Constants.h" // Required for BuiltInAnimations.h (included via BaseConnectorXVariant.hpp -> AnimationBuilder.hpp)
#include "lumyn/cpp/connectorXVariant/BaseConnectorXVariant.hpp"

// Internal headers
#include "lumyn/cpp/util/SerialIOAdapter.hpp"
#include "lumyn/cpp/util/EventConversion.hpp"
#include <lumyn/domain/command/Command.h>
#include <lumyn/util/hashing/IDCreator.h>
#include <lumyn/util/serial/ISerialIO.h>
#include <lumyn/domain/Color.h>
#include <lumyn/domain/command/led/LEDCommand.h>
#include <lumyn/domain/event/EventType.h>
#include <lumyn/led/Animation.h>
#include <lumyn/domain/event/Event.h>
#include <lumyn/cpp/EventManager.h>
#include <lumyn/cpp/ConfigManager.h>

#include <stdexcept>
#include <cstring>
#include <chrono>
#include <thread>
#include <vector>
#include <climits>
#include <fstream>
#include <iterator>

namespace
{
  /**
   * @brief Convert an internal::Eventing::Event to a lumyn_event_t C struct
   *
   * This allows events from the pure C++ BaseLumynDevice::DrainEvents() to be
   * converted to the C API format used by lumyn::Event.
   */
  lumyn_event_t convert_internal_event_to_c(const lumyn::internal::Eventing::Event &evt)
  {
    lumyn_event_t c_evt{};
    c_evt.type = static_cast<lumyn_event_type_t>(evt.header.type);

    // Convert data union based on event type
    using lumyn::internal::Eventing::EventType;
    switch (evt.header.type)
    {
    case EventType::Disabled:
      c_evt.data.disabled.cause = static_cast<lumyn_disabled_cause_t>(evt.header.data.disabled.cause);
      break;
    case EventType::Connected:
      c_evt.data.connected.type = static_cast<lumyn_connection_type_t>(evt.header.data.connected.type);
      break;
    case EventType::Disconnected:
      c_evt.data.disconnected.type = static_cast<lumyn_connection_type_t>(evt.header.data.disconnected.type);
      break;
    case EventType::Error:
      c_evt.data.error.type = static_cast<lumyn_error_type_t>(evt.header.data.error.type);
      std::strncpy(c_evt.data.error.message, evt.header.data.error.message,
                   sizeof(c_evt.data.error.message) - 1);
      c_evt.data.error.message[sizeof(c_evt.data.error.message) - 1] = '\0';
      break;
    case EventType::FatalError:
      c_evt.data.fatal_error.type = static_cast<lumyn_fatal_error_type_t>(evt.header.data.fatalError.type);
      std::strncpy(c_evt.data.fatal_error.message, evt.header.data.fatalError.message,
                   sizeof(c_evt.data.fatal_error.message) - 1);
      c_evt.data.fatal_error.message[sizeof(c_evt.data.fatal_error.message) - 1] = '\0';
      break;
    case EventType::RegisteredEntity:
      c_evt.data.registered_entity.id = static_cast<int32_t>(evt.header.data.registeredEntity.id);
      break;
    case EventType::Custom:
      c_evt.data.custom.type = evt.header.data.custom.type;
      c_evt.data.custom.length = evt.header.data.custom.length;
      std::memcpy(c_evt.data.custom.data, evt.header.data.custom.data,
                  sizeof(c_evt.data.custom.data));
      break;
    case EventType::PinInterrupt:
      c_evt.data.pin_interrupt.pin = evt.header.data.pinInterrupt.pin;
      break;
    case EventType::HeartBeat:
      c_evt.data.heartbeat.status = static_cast<lumyn_status_t>(evt.header.data.heartBeat.status);
      c_evt.data.heartbeat.enabled = evt.header.data.heartBeat.enabled;
      c_evt.data.heartbeat.connected_usb = evt.header.data.heartBeat.connectedUSB;
      c_evt.data.heartbeat.can_ok = evt.header.data.heartBeat.canOK;
      break;
    default:
      // BeginInitialization, FinishInitialization, Enabled, OTA, Module - no data
      break;
    }

    // Handle extra message (lumyn::Event will make a copy)
    c_evt.extra_message = nullptr;
    if (evt.hasExtraMessage())
    {
      // Note: lumyn::Event constructor will copy this, so we can use the pointer directly
      // But lumyn_event_t expects caller to free, so we need to duplicate
      const char *msg = evt.getExtraMessageStr();
      if (msg)
      {
        size_t len = std::strlen(msg) + 1;
        c_evt.extra_message = static_cast<char *>(std::malloc(len));
        if (c_evt.extra_message)
        {
          std::memcpy(c_evt.extra_message, msg, len);
        }
      }
    }

    return c_evt;
  }
} // anonymous namespace

namespace lumyn::device
{

  BaseConnectorXVariant::BaseConnectorXVariant()
      : internal::BaseLEDDevice(),
        internal::BaseLumynDevice()
  {
    // Initialize LED commanders for BaseLEDDevice
    InitializeLEDCommanders([this](internal::Command::LED::LEDCommand &cmd)
                            { SendLEDCommand(&cmd, sizeof(cmd)); });
  }

  BaseConnectorXVariant::~BaseConnectorXVariant()
  {
    poll_events_ = false;
    if (event_thread_.joinable())
      event_thread_.join();
  }

  void BaseConnectorXVariant::SendLEDCommand(const void *data, uint32_t length)
  {
    if (!data || length == 0)
      return;
    const auto *led = static_cast<const internal::Command::LED::LEDCommand *>(data);
    internal::Command::CommandHeader header{};
    header.type = internal::Command::CommandType::LED;
    header.ledType = led->type;

    // Match Python SDK: send only the payload struct for the specific LED command
    const void *payload = nullptr;
    uint32_t payload_len = 0;
    using internal::Command::LED::LEDCommandType;
    switch (led->type)
    {
    case LEDCommandType::SetAnimation:
      payload = &led->data.setAnimation;
      payload_len = sizeof(led->data.setAnimation);
      break;
    case LEDCommandType::SetAnimationGroup:
      payload = &led->data.setAnimationGroup;
      payload_len = sizeof(led->data.setAnimationGroup);
      break;
    case LEDCommandType::SetColor:
      payload = &led->data.setColor;
      payload_len = sizeof(led->data.setColor);
      break;
    case LEDCommandType::SetColorGroup:
      payload = &led->data.setColorGroup;
      payload_len = sizeof(led->data.setColorGroup);
      break;
    case LEDCommandType::SetAnimationSequence:
      payload = &led->data.setAnimationSequence;
      payload_len = sizeof(led->data.setAnimationSequence);
      break;
    case LEDCommandType::SetAnimationSequenceGroup:
      payload = &led->data.setAnimationSequenceGroup;
      payload_len = sizeof(led->data.setAnimationSequenceGroup);
      break;
    case LEDCommandType::SetBitmap:
      payload = &led->data.setBitmap;
      payload_len = sizeof(led->data.setBitmap);
      break;
    case LEDCommandType::SetBitmapGroup:
      payload = &led->data.setBitmapGroup;
      payload_len = sizeof(led->data.setBitmapGroup);
      break;
    case LEDCommandType::SetMatrixText:
      payload = &led->data.setMatrixText;
      payload_len = sizeof(led->data.setMatrixText);
      break;
    case LEDCommandType::SetMatrixTextGroup:
      payload = &led->data.setMatrixTextGroup;
      payload_len = sizeof(led->data.setMatrixTextGroup);
      break;
    case LEDCommandType::SetDirectBuffer:
      payload = &led->data.setDirectBuffer;
      payload_len = sizeof(led->data.setDirectBuffer);
      break;
    default:
      payload = data;
      payload_len = length;
      break;
    }

    SendCommand(header, payload, payload_len);
  }

  lumyn_error_t BaseConnectorXVariant::SendDirectBuffer(std::string_view zone_id, const uint8_t *data, size_t length, bool delta)
  {
    auto zone_hash = internal::IDCreator::createId(zone_id);
    return SendDirectBuffer(zone_hash, data, length, delta);
  }

  lumyn_error_t BaseConnectorXVariant::SendDirectBuffer(uint16_t zone_hash, const uint8_t *data, size_t length, bool delta)
  {
    if (!data || length == 0 || length > UINT16_MAX)
      return LUMYN_ERR_INVALID_ARGUMENT;
    internal::Command::CommandHeader header{};
    header.type = internal::Command::CommandType::LED;
    header.ledType = internal::Command::LED::LEDCommandType::SetDirectBuffer;

    internal::Command::LED::SetDirectBufferData meta{};
    meta.zoneId = zone_hash;
    meta.bufferLength = static_cast<uint16_t>(length);
    meta.flags.delta = delta ? 1 : 0;
    meta.flags.reserved = 0;

    std::vector<uint8_t> payload(sizeof(meta) + length);
    std::memcpy(payload.data(), &meta, sizeof(meta));
    std::memcpy(payload.data() + sizeof(meta), data, length);

    SendCommand(header, payload.data(), payload.size());
    return LUMYN_OK;
  }

  void BaseConnectorXVariant::SendRawCommand(const uint8_t *data, size_t length)
  {
    // Forward to the protected BaseLumynDevice::SendRawCommand
    internal::BaseLumynDevice::SendRawCommand(data, length);
  }

  void BaseConnectorXVariant::StartEventPolling()
  {
    if (auto_poll_events_ && c_base_ptr_ && !poll_events_)
    {
      poll_events_ = true;
      event_thread_ = std::thread([this]()
                                  {
        while (poll_events_) {
          try {
            GetEvents();
            std::this_thread::sleep_for(std::chrono::milliseconds(22));
          } catch (...) {
          }
        } });
    }
  }

  void BaseConnectorXVariant::StopEventPolling()
  {
    poll_events_ = false;
    if (event_thread_.joinable())
      event_thread_.join();
  }

  lumyn_error_t BaseConnectorXVariant::Connect(const lumyn_serial_io_t &io)
  {
    auto adapter = std::make_unique<internal::SerialIOAdapter>(io);
    if (BaseLumynDevice::Connect(adapter.release()))
    {
      StartEventPolling();
      return LUMYN_OK;
    }
    return LUMYN_ERR_IO;
  }

  lumyn_error_t BaseConnectorXVariant::Connect(const std::string &port, std::optional<int> baud)
  {
    lumyn_serial_io_cfg_t cfg = LUMYN_SERIAL_CFG_DEFAULT;
    cfg.path = port.c_str();
    cfg.baud = baud.value_or(115200);

    lumyn_serial_io_t io{};
    auto err = lumyn_serial_open(&cfg, &io);
    if (err != LUMYN_OK)
      return err;
    err = Connect(io);
    if (err != LUMYN_OK)
    {
      lumyn_serial_io_close(&io);
    }
    return err;
  }

  void BaseConnectorXVariant::Disconnect()
  {
    BaseLumynDevice::Disconnect();
    StopEventPolling();
    OnDisconnect(); // Hook for derived class cleanup
  }

  bool BaseConnectorXVariant::IsConnected() const
  {
    return BaseLumynDevice::IsConnected();
  }

  lumyn::ConnectionStatus BaseConnectorXVariant::GetCurrentStatus() const
  {
    if (!c_base_ptr_)
    {
      // Pure C++ usage - get status from base device
      return lumyn::ConnectionStatus{IsConnected(), IsConnected()};
    }
    auto c_status = lumyn_GetCurrentStatus(const_cast<cx_base_t *>(c_base_ptr_));
    return lumyn::ConnectionStatus{c_status.connected, c_status.enabled};
  }

  lumyn::Status BaseConnectorXVariant::GetDeviceHealth() const
  {
    if (!c_base_ptr_)
    {
      return static_cast<lumyn::Status>(LUMYN_STATUS_UNKNOWN);
    }
    return static_cast<lumyn::Status>(lumyn_GetDeviceHealth(const_cast<cx_base_t *>(c_base_ptr_)));
  }

  lumyn_error_t BaseConnectorXVariant::AddEventHandler(std::function<void(const lumyn::Event &)> handler)
  {
    if (!handler)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!c_base_ptr_)
      return LUMYN_ERR_NOT_SUPPORTED;
    // Convert lumyn::Event handler to lumyn_event_t handler for EventManager
    return GetEventManager().AddEventHandler([handler = std::move(handler)](const lumyn_event_t &c_evt)
                                             { handler(internal::from_c_event(c_evt)); });
  }

  lumyn_error_t BaseConnectorXVariant::GetLatestEvent(lumyn_event_t &out_event)
  {
    if (!c_base_ptr_)
      return LUMYN_ERR_NOT_SUPPORTED;
    return GetEventManager().GetLatestEvent(out_event);
  }

  std::optional<lumyn::Event> BaseConnectorXVariant::GetLatestEvent()
  {
    if (!c_base_ptr_)
      return std::nullopt;
    auto c_evt = GetEventManager().GetLatestEvent();
    if (!c_evt.has_value())
      return std::nullopt;
    return internal::from_c_event(c_evt.value());
  }

  std::vector<lumyn::Event> BaseConnectorXVariant::GetEvents()
  {
    // If using the C API (c_base_ptr_ is set), use the EventManager
    if (c_base_ptr_)
    {
      auto c_events = GetEventManager().GetEvents();
      std::vector<lumyn::Event> events;
      events.reserve(c_events.size());
      for (const auto &c_evt : c_events)
      {
        events.push_back(internal::from_c_event(c_evt));
      }
      return events;
    }

    // For pure C++ usage, drain events from BaseLumynDevice's queue
    auto raw_events = BaseLumynDevice::DrainEvents();
    std::vector<lumyn::Event> events;
    events.reserve(raw_events.size());
    for (const auto &evt : raw_events)
    {
      // Convert internal event to C struct, then wrap in lumyn::Event
      lumyn_event_t c_evt = convert_internal_event_to_c(evt);
      events.push_back(lumyn::Event(c_evt));
      // lumyn::Event makes a copy of extra_message, so we can free the temporary
      if (c_evt.extra_message)
      {
        std::free(c_evt.extra_message);
      }
    }
    return events;
  }

  void BaseConnectorXVariant::SetAutoPollEvents(bool enabled)
  {
    auto_poll_events_ = enabled;
    if (!enabled)
    {
      StopEventPolling();
    }
    else if (!poll_events_ && IsConnected() && c_base_ptr_)
    {
      StartEventPolling();
    }
  }

  void BaseConnectorXVariant::PollEvents()
  {
    (void)GetEvents();
  }

  lumyn_error_t BaseConnectorXVariant::RequestConfig(std::string &out_json, uint32_t timeout_ms)
  {
    if (!c_base_ptr_)
    {
      bool ok = BaseLumynDevice::RequestConfig(out_json, static_cast<int>(timeout_ms));
      return ok ? LUMYN_OK : LUMYN_ERR_TIMEOUT;
    }
    return GetConfigManager().RequestConfig(out_json, timeout_ms);
  }

  bool BaseConnectorXVariant::ApplyConfigurationJson(const std::string &json)
  {
    if (json.empty())
      return false;
    if (!c_base_ptr_)
    {
      if (!IsConnected())
        return false;
      BaseLumynDevice::SendConfiguration(reinterpret_cast<const uint8_t *>(json.data()),
                                         static_cast<uint32_t>(json.size()));
      return true;
    }
    return lumyn_ApplyConfig(c_base_ptr_, json.data(), json.size()) == LUMYN_OK;
  }

  bool BaseConnectorXVariant::LoadConfigurationFromFile(const std::string &path)
  {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open())
      return false;
    std::string contents((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    return ApplyConfigurationJson(contents);
  }

  void BaseConnectorXVariant::SetColor(std::string_view zone_id, ::lumyn_color_t color) const
  {
    if (!c_base_ptr_)
      return; // Pure C++ usage - LED commands need C API
    lumyn_SetColor(const_cast<cx_base_t *>(c_base_ptr_), std::string(zone_id).c_str(), color);
  }

  void BaseConnectorXVariant::SetGroupColor(std::string_view group_id, ::lumyn_color_t color) const
  {
    if (!c_base_ptr_)
      return; // Pure C++ usage - LED commands need C API
    lumyn_SetGroupColor(const_cast<cx_base_t *>(c_base_ptr_), std::string(group_id).c_str(), color);
  }

  AnimationBuilder BaseConnectorXVariant::SetAnimation(lumyn::led::Animation animation)
  {
    return AnimationBuilder(*this, animation);
  }

  ImageSequenceBuilder BaseConnectorXVariant::SetImageSequence(std::string_view sequence_id)
  {
    return ImageSequenceBuilder(*this, sequence_id);
  }

  void BaseConnectorXVariant::SetAnimationSequence(std::string_view zone_id, std::string_view sequence_id)
  {
    GetLEDCommander().SetAnimationSequence(zone_id, sequence_id);
  }

  void BaseConnectorXVariant::SetGroupAnimationSequence(std::string_view group_id, std::string_view sequence_id)
  {
    GetLEDCommander().SetGroupAnimationSequence(group_id, sequence_id);
  }

  MatrixTextBuilder BaseConnectorXVariant::SetText(std::string_view text)
  {
    return MatrixTextBuilder(*this, text);
  }

  DirectLED BaseConnectorXVariant::CreateDirectLED(std::string_view zone_id, size_t num_leds, int full_refresh_interval_ms)
  {
    if (c_base_ptr_)
    {
      return DirectLED(c_base_ptr_, zone_id, num_leds, full_refresh_interval_ms);
    }
    return DirectLED(
        [this](uint16_t zone_hash, const uint8_t *data, size_t length, bool delta)
        {
          return this->SendDirectBuffer(zone_hash, data, length, delta);
        },
        zone_id, num_leds, full_refresh_interval_ms);
  }

} // namespace lumyn::device
