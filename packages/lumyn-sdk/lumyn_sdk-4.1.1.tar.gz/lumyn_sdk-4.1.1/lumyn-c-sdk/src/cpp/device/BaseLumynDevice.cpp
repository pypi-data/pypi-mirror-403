#include <lumyn/Constants.h> // Required for ILogger.h (included via ConsoleLogger.h)

#include "lumyn/cpp/device/BaseLumynDevice.hpp"

#include "lumyn/util/timing/CurrentTimestamp.h"
#include "lumyn/version.h"
#include <mutex>
#include <vector>

#include "lumyn/domain/file/FileType.h"
#include "lumyn/domain/request/RequestBuilder.h"
#include "lumyn/domain/command/system/SystemCommand.h"
#include "lumyn/networking/TransmissionPortListener.h"
#include "lumyn/domain/event/Event.h"
#include "lumyn/domain/response/Response.h"
#include "lumyn/util/logging/ConsoleLogger.h"
#include "lumyn/util/serial/ISerialIO.h"
#include "lumyn/cpp/ConfigManager.h"
#include "lumyn/cpp/EventManager.h"
#include "lumyn/util/hashing/IDCreator.h"

using namespace lumyn::internal;

struct BaseLumynDevice::Impl
{
  std::unique_ptr<TransmissionPortListener> portListener;
  std::unique_ptr<ILumynTransmissionHandler> internal_handler;
  std::unique_ptr<ISerialIO> serialIO;
  std::unique_ptr<Response::ResponseHandshakeInfo> latestHandshake;
  std::unique_ptr<Eventing::Event> latestEvent;
  std::mutex events_mutex;
  std::vector<Eventing::Event> event_queue;

  struct HeartbeatData
  {
    Eventing::HeartBeatInfo info;
    int64_t timestamp;
  };
  std::unique_ptr<HeartbeatData> latestHeartbeat;
  int64_t lastHandshakeMs{0};
};

/**
 * @brief Internal class to handle transmissions without exposing networking headers
 */
class BaseLumynDeviceHandler : public ILumynTransmissionHandler
{
public:
  BaseLumynDeviceHandler(BaseLumynDevice *parent) : parent_(parent) {}
  void HandleEvent(const Eventing::Event &event) override { parent_->HandleEvent(event); }
  void HandleTransmission(const Transmission::Transmission &transmission) override
  {
    (void)transmission; // Suppress unused parameter warning
  }

private:
  BaseLumynDevice *parent_;
};

BaseLumynDevice::BaseLumynDevice() : _impl(std::make_unique<Impl>()) {}

lumyn::internal::BaseLumynDevice::~BaseLumynDevice() = default;

bool BaseLumynDevice::Connect(ISerialIO *serial)
{
  if (!_impl->portListener)
  {
    // Lazy initialize port listener if not ready
    auto handler = std::make_unique<BaseLumynDeviceHandler>(this);
    _impl->portListener = std::make_unique<TransmissionPortListener>(*handler);
    _impl->internal_handler = std::move(handler);
  }

  _impl->serialIO.reset(serial);

  _impl->serialIO->setReadCallback([this](const uint8_t *data, size_t length)
                                   {
    if (_impl->portListener) {
      _impl->portListener->ingressBytes(data, length);
    } });

  _impl->portListener->setWriteCallback([this](const uint8_t *data, size_t length)
                                        { _impl->serialIO->writeBytes(data, length); });

  _impl->portListener->Init();

  bool success = Initialize();
  if (!success)
  {
    // Connection failed (handshake failed), clean up
    Disconnect();
  }
  return success;
}

void BaseLumynDevice::Disconnect(void)
{
  // Clear read callback to stop processing incoming data
  if (_impl->serialIO)
  {
    _impl->serialIO->setReadCallback(nullptr);
  }

  // Clear write callback on port listener
  if (_impl->portListener)
  {
    _impl->portListener->setWriteCallback(nullptr);
  }

  // Reset serial IO (will call destructor and close the port)
  _impl->serialIO.reset();

  // Clear state
  _impl->latestHandshake.reset();
  _impl->latestEvent.reset();
  _impl->latestHeartbeat.reset();
}

bool BaseLumynDevice::IsConnected(void) const
{
  const int64_t now = util::timing::CurrentTimestamp::GetCurrentTimestampMs();
  if (_impl->lastHandshakeMs > 0 && now - _impl->lastHandshakeMs <= 5000)
  {
    return true; // grace window after handshake
  }
  if (!_impl->latestHeartbeat)
    return false;

  // Read the last received heartbeat timestamp; if within range, it is still connected
  return now - _impl->latestHeartbeat->timestamp <= 5000;
}

void BaseLumynDevice::Restart(uint32_t delay_ms)
{
  if (!_impl->portListener)
  {
    return;
  }

  // Create restart command
  Command::CommandHeader header{};
  header.type = Command::CommandType::System;
  header.systemType = Command::System::SystemCommandType::RestartDevice;

  Command::System::RestartDeviceData restartData{};
  restartData.delayMs = delay_ms > UINT16_MAX ? UINT16_MAX : static_cast<uint16_t>(delay_ms);

  _impl->portListener->SendCommand(header, &restartData, sizeof(restartData));
}

Eventing::Status BaseLumynDevice::GetCurrentStatus(void)
{
  if (!_impl->latestHeartbeat)
    return Eventing::Status::Unknown;
  return _impl->latestHeartbeat->info.status;
}

const Eventing::Event *BaseLumynDevice::GetLatestEvent(void) const
{
  return _impl->latestEvent.get();
}

const Response::ResponseHandshakeInfo *BaseLumynDevice::GetLatestHandshake(void) const
{
  return _impl->latestHandshake.get();
}

bool BaseLumynDevice::RequestConfig(std::string &outConfigJson, int timeoutMs)
{
  outConfigJson.clear();

  if (!_impl->portListener)
  {
    return false;
  }

  Request::Request request{};
  request.header.type = Request::RequestType::ConfigFull;

  auto response = _impl->portListener->SendRequest(request, timeoutMs);
  if (!response.has_value())
  {
    return false;
  }

  if (response->header.type != Request::RequestType::ConfigFull)
  {
    return false;
  }

  std::vector<uint8_t> configData;
  if (!_impl->portListener->GetConfigFullData(response->header.id, configData))
  {
    return false;
  }

  outConfigJson.assign(reinterpret_cast<const char *>(configData.data()), configData.size());
  return true;
}

bool BaseLumynDevice::Initialize(void)
{
  bool success = Handshake();

  if (!success)
  {
    ConsoleLogger::getInstance().logError("BaseLumynDevice", "Received unsuccessful handshake");
    return false;
  }

  return true;
}

void BaseLumynDevice::SendConfiguration(const uint8_t *data, uint32_t length)
{
  if (_impl->portListener)
  {
    _impl->portListener->SendFile(Files::FileType::SendConfig, data, length, nullptr);
  }
}

std::optional<lumyn::internal::Response::Response> BaseLumynDevice::SendRequestInternal(lumyn::internal::Request::Request &request, int timeoutMs)
{
  if (!_impl->portListener)
    return std::nullopt;
  return _impl->portListener->SendRequest(request, timeoutMs);
}

void BaseLumynDevice::SendCommandInternal(const lumyn::internal::Command::CommandHeader &header, const void *data, size_t length)
{
  if (_impl->portListener)
  {
    _impl->portListener->SendCommand(header, data, length);
  }
}

bool BaseLumynDevice::TryPopModuleDataRawInternal(uint16_t moduleId, std::vector<std::vector<uint8_t>> &out)
{
  if (!_impl->portListener)
    return false;
  return _impl->portListener->TryPopModuleDataRaw(moduleId, out);
}

void BaseLumynDevice::HandleEvent(const Eventing::Event &event)
{
  {
    std::lock_guard<std::mutex> lock(_impl->events_mutex);
    _impl->event_queue.push_back(event);
    constexpr size_t kMaxBufferedEvents = 128;
    if (_impl->event_queue.size() > kMaxBufferedEvents)
    {
      _impl->event_queue.erase(_impl->event_queue.begin(), _impl->event_queue.begin() + (_impl->event_queue.size() - kMaxBufferedEvents));
    }
  }

  _impl->latestEvent = std::make_unique<Eventing::Event>(event);

  if (event.header.type == Eventing::EventType::HeartBeat)
  {
    // If it's a Heartbeat, update the timestamp for use in IsConnected()
    _impl->latestHeartbeat = std::make_unique<Impl::HeartbeatData>(Impl::HeartbeatData{event.header.data.heartBeat, util::timing::CurrentTimestamp::GetCurrentTimestampMs()});
  }

  OnEvent(event);
}

std::vector<lumyn::internal::Eventing::Event> BaseLumynDevice::DrainEvents()
{
  std::lock_guard<std::mutex> lock(_impl->events_mutex);
  std::vector<lumyn::internal::Eventing::Event> out;
  out.swap(_impl->event_queue);
  return out;
}

bool BaseLumynDevice::Handshake()
{
  Request::Request handshake{};
  handshake.header.type = Request::RequestType::Handshake;
  handshake.data.handshake.hostSource = Request::HostConnectionSource::Roborio;

  auto res = _impl->portListener->SendRequest(handshake, 5000);
  if (!res.has_value())
  {
    ConsoleLogger::getInstance().logError("BaseLumynDevice", "Handshake not received!");
    return false;
  }

  if (res->data.handshake.version.major != LUMYN_VERSION_MAJOR)
  {
    ConsoleLogger::getInstance().logError("BaseLumynDevice", "Device version mismatch! Device version: %d, Driver version: %d",
                                          res->data.handshake.version.major, LUMYN_VERSION_MAJOR);
    return false;
  }

  _impl->latestHandshake = std::make_unique<Response::ResponseHandshakeInfo>(res.value().data.handshake);
  ConsoleLogger::getInstance().logInfo("BaseLumynDevice", "Successfully handshook with device which has ID=%s and version=%d.%d.%d",
                                       _impl->latestHandshake->assignedId.id,
                                       _impl->latestHandshake->version.major,
                                       _impl->latestHandshake->version.minor,
                                       _impl->latestHandshake->version.patch);

  Eventing::HeartBeatInfo syntheticHb{};
  syntheticHb.status = _impl->latestHandshake->status.status;
  _impl->latestHeartbeat = std::make_unique<Impl::HeartbeatData>(Impl::HeartbeatData{syntheticHb, util::timing::CurrentTimestamp::GetCurrentTimestampMs()});
  _impl->lastHandshakeMs = util::timing::CurrentTimestamp::GetCurrentTimestampMs();

  return true;
}

lumyn::managers::ConfigManager &BaseLumynDevice::GetConfigManager()
{
  if (!config_manager_)
  {
    config_manager_ = std::make_unique<lumyn::managers::ConfigManager>(static_cast<cx_base_t *>(GetBasePtr()));
  }
  return *config_manager_;
}

lumyn::managers::EventManager &BaseLumynDevice::GetEventManager()
{
  if (!event_manager_)
  {
    event_manager_ = std::make_unique<lumyn::managers::EventManager>(static_cast<cx_base_t *>(GetBasePtr()));
  }
  return *event_manager_;
}

bool BaseLumynDevice::GetModuleDataByHash(uint16_t moduleId, std::vector<std::vector<uint8_t>> &out)
{
  return TryPopModuleDataRawInternal(moduleId, out);
}

bool BaseLumynDevice::GetModuleDataByName(std::string_view moduleId, std::vector<std::vector<uint8_t>> &out)
{
  const uint16_t moduleHash = lumyn::internal::IDCreator::createId(moduleId);
  return GetModuleDataByHash(moduleHash, out);
}

std::optional<Response::Response> BaseLumynDevice::SendRequest(Request::Request &request, int timeoutMs)
{
  return SendRequestInternal(request, timeoutMs);
}

void BaseLumynDevice::SendCommand(const Command::CommandHeader &header, const void *payload, size_t payloadLen)
{
  SendCommandInternal(header, payload, payloadLen);
}

void BaseLumynDevice::SendRawCommand(const uint8_t *data, size_t length)
{
  if (_impl->portListener && data && length > 0)
  {
    _impl->portListener->SendRawCommand(data, length);
  }
}
