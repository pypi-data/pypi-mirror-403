#include "lumyn/Constants.h"
#include "lumyn/networking/TransmissionPortListener.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <future>
#include <random>
#include <vector>

#include "lumyn/domain/file/Files.h"
#include "lumyn/domain/file/FilesBuilder.h"
#include "lumyn/domain/request/RequestBuilder.h"
#include "lumyn/util/logging/ConsoleLogger.h"
#include "lumyn/util/serial/RLECompressor.h"
#include "lumyn/version.h"

using namespace lumyn::internal;

TransmissionPortListener::TransmissionPortListener(
    ILumynTransmissionHandler &handler)
    : _running{false}, _handler{handler}
{
  ConsoleLogger::getInstance().logVerbose("TransmissionPortListener",
                                          "Creating TransmissionPortListener");
}

TransmissionPortListener::~TransmissionPortListener()
{
  _running = false;
  if (_readThread.joinable())
  {
    _readThread.join();
  }
}

void TransmissionPortListener::Init()
{
  _serial = std::make_unique<lumyn::internal::StandardPacketSerial>(&_encoder);

  // Pass the writeBytes callback to PacketSerial
  if (writeBytes)
  {
    _serial->setWriteCallback(writeBytes);
  }

  _lumynTp = std::make_unique<lumyn::internal::StandardLumynTP>(*_serial);
  _lumynTp->setOnNewTransmission(
      [this](lumyn::internal::Transmission::Transmission *transmission)
      {
        HandleTransmission(*transmission);
        transmission->unref();
      });

  _running = true;
  ReadDataStream();
}

void TransmissionPortListener::ReadDataStream() { _lumynTp->start(); }

void TransmissionPortListener::HandleTransmission(
    const TransmissionClass &transmission)
{
  // Decompress if needed (matching firmware NetworkingService::rxTask)
  TransmissionClass *tx = const_cast<TransmissionClass *>(&transmission);
  tx->ref(); // Take ownership for decompress
  tx = RLECompressor::decompress(tx);

  if (!tx)
  {
    ConsoleLogger::getInstance().logError(
        "TransmissionPortListener",
        "HandleTransmission: Failed to decompress transmission");
    return;
  }

  if (tx->getHeader()->version != LUMYN_VERSION_MAJOR)
  {
    ConsoleLogger::getInstance().logWarning(
        "TransmissionPortListener",
        "HandleTransmission: Dropping transmission with unsupported version "
        "%u (Host = %u). Visit "
        "https://docs.lumynlabs.com/"
        "drivers-and-firmware.html#updating-firmware to update firmware.",
        tx->getHeader()->version, LUMYN_VERSION_MAJOR);
    tx->unref();
    return;
  }

  // Notify handler of decompressed transmission
  _handler.HandleTransmission(*tx);

  const auto *txHeader = tx->getHeader();
  if (!txHeader)
  {
    ConsoleLogger::getInstance().logError(
        "TransmissionPortListener",
        "HandleTransmission: Invalid transmission header");
    tx->unref();
    return;
  }

  if (txHeader->type ==
      lumyn::internal::Transmission::TransmissionType::Event)
  {
    // Rebuild Event from header + optional extra bytes (firmware style: memcpy
    // header, then copy extra)
    const auto *evtHeader =
        tx->getPayload<lumyn::internal::Eventing::EventHeader>();
    if (!evtHeader)
    {
      tx->unref();
      return;
    }

    // Create event and copy header using memcpy (like firmware)
    lumyn::internal::Eventing::Event evt;
    std::memcpy(&evt.header, evtHeader,
                sizeof(lumyn::internal::Eventing::EventHeader));
    evt.extraMsg = nullptr;

    // Copy extra message data if present
    const size_t extraSize =
        tx->getVariableDataSize<lumyn::internal::Eventing::EventHeader>();
    if (extraSize > 0)
    {
      const uint8_t *extra =
          tx->getVariableData<lumyn::internal::Eventing::EventHeader>();
      if (extra)
      {
        evt.setExtraMessage(extra, static_cast<uint16_t>(extraSize));
      }
    }
    _handler.HandleEvent(evt);
  }
  else if (txHeader->type ==
           lumyn::internal::Transmission::TransmissionType::Response)
  {
    // Parse ResponseHeader from the start of payload
    const auto *respHeader =
        tx->getPayload<lumyn::internal::Response::ResponseHeader>();
    if (!respHeader)
    {
      ConsoleLogger::getInstance().logError(
          "TransmissionPortListener",
          "HandleTransmission: Invalid Response header");
      tx->unref();
      return;
    }

    // Build Response struct by copying header and parsing variable data
    lumyn::internal::Response::Response resp;
    std::memcpy(&resp.header, respHeader,
                sizeof(lumyn::internal::Response::ResponseHeader));

    // Get the response body (data after ResponseHeader)
    const uint8_t *bodyData =
        tx->getVariableData<lumyn::internal::Response::ResponseHeader>();
    size_t bodySize =
        tx->getVariableDataSize<lumyn::internal::Response::ResponseHeader>();

    // Handle different response types
    if (resp.header.type == lumyn::internal::Request::RequestType::ConfigFull)
    {
      // ConfigFull: firmware sends [ResponseHeader][raw config bytes]
      // Store the raw config data directly
      if (bodyData && bodySize > 0)
      {
        std::vector<uint8_t> configBytes;
        configBytes.assign(bodyData, bodyData + bodySize);

        std::lock_guard<std::mutex> lock(_configFullMutex);
        _configFullBuffers[resp.header.id] = std::move(configBytes);
      }
    }
    else if (bodyData && bodySize > 0)
    {
      // For other response types, copy the response data union
      // Only copy up to the size of ResponseData to avoid buffer overrun
      size_t copySize =
          std::min(bodySize, sizeof(lumyn::internal::Response::ResponseData));
      std::memcpy(&resp.data, bodyData, copySize);
    }

    OnResponse(resp);
  }
  else if (txHeader->type ==
           lumyn::internal::Transmission::TransmissionType::ModuleData)
  {
    const auto *mdHeader =
        tx->getPayload<lumyn::internal::ModuleData::ModuleDataHeader>();
    if (!mdHeader)
    {
      ConsoleLogger::getInstance().logError(
          "TransmissionPortListener",
          "HandleTransmission: Invalid ModuleData header");
      tx->unref();
      return;
    }

    // The first entry's id and len are embedded in the ModuleDataHeader's union
    const uint16_t firstId = mdHeader->data.dataUnit.id;
    const uint16_t firstLen = mdHeader->data.dataUnit.len;

    const uint8_t *cursor =
        tx->getVariableData<lumyn::internal::ModuleData::ModuleDataHeader>();
    size_t remaining = tx->getVariableDataSize<
        lumyn::internal::ModuleData::ModuleDataHeader>();

    std::lock_guard<std::mutex> lock(_moduleDataMutex);

    // Process the first entry (header contains id/len, variable data starts with payload)
    if (cursor && remaining >= firstLen)
    {
      std::vector<uint8_t> payload;
      if (firstLen > 0)
      {
        payload.assign(cursor, cursor + firstLen);
      }
      _moduleDataRawBuffers[firstId].emplace_back(std::move(payload));

      cursor += firstLen;
      remaining -= firstLen;
    }

    // Process any additional entries (each has its own ModuleDataUnitHeader + payload)
    while (remaining >=
           sizeof(lumyn::internal::ModuleData::ModuleDataUnitHeader))
    {
      const auto *unit = reinterpret_cast<
          const lumyn::internal::ModuleData::ModuleDataUnitHeader *>(cursor);
      const size_t needed =
          sizeof(lumyn::internal::ModuleData::ModuleDataUnitHeader) + unit->len;
      if (remaining < needed)
      {
        break;
      }

      const uint8_t *dataStart =
          cursor + sizeof(lumyn::internal::ModuleData::ModuleDataUnitHeader);
      std::vector<uint8_t> payload;
      if (unit->len > 0)
      {
        payload.assign(dataStart, dataStart + unit->len);
      }

      _moduleDataRawBuffers[unit->id].emplace_back(std::move(payload));

      cursor += needed;
      remaining -= needed;
    }
  }

  tx->unref();
}

bool TransmissionPortListener::TryPopModuleDataRaw(
    uint16_t moduleId, std::vector<std::vector<uint8_t>> &out)
{
  std::lock_guard<std::mutex> lock(_moduleDataMutex);
  auto it = _moduleDataRawBuffers.find(moduleId);
  if (it == _moduleDataRawBuffers.end() || it->second.empty())
  {
    return false;
  }

  out.swap(it->second);
  _moduleDataRawBuffers.erase(it);
  return true;
}

bool TransmissionPortListener::GetConfigFullData(uint32_t requestId,
                                                 std::vector<uint8_t> &out)
{
  std::lock_guard<std::mutex> lock(_configFullMutex);
  auto it = _configFullBuffers.find(requestId);
  if (it != _configFullBuffers.end())
  {
    out = it->second;
    _configFullBuffers.erase(it);
    return true;
  }
  return false;
}

void TransmissionPortListener::SendCommand(const Command::CommandHeader &header,
                                           const void *payload,
                                           size_t payloadLen)
{
  if (!_lumynTp)
  {
    return;
  }
  std::vector<uint8_t> buffer;
  buffer.reserve(sizeof(Command::CommandHeader) + payloadLen);
  buffer.assign(reinterpret_cast<const uint8_t *>(&header),
                reinterpret_cast<const uint8_t *>(&header) +
                    sizeof(Command::CommandHeader));
  if (payload && payloadLen > 0)
  {
    buffer.insert(buffer.end(), reinterpret_cast<const uint8_t *>(payload),
                  reinterpret_cast<const uint8_t *>(payload) + payloadLen);
  }
  _lumynTp->sendTransmission(
      buffer.data(), buffer.size(),
      lumyn::internal::Transmission::TransmissionType::Command);
}

void TransmissionPortListener::SendRawCommand(const uint8_t *data,
                                              size_t length)
{
  if (!_lumynTp || !data || length == 0)
  {
    return;
  }
  _lumynTp->sendTransmission(
      data, length,
      lumyn::internal::Transmission::TransmissionType::Command);
}

void TransmissionPortListener::SendFile(Files::FileType type,
                                        const uint8_t *data, uint32_t length,
                                        const char *path)
{
  if (!_lumynTp)
  {
    return;
  }

  std::vector<uint8_t> buffer;
  switch (type)
  {
  case Files::FileType::Transfer:
    if (!path)
    {
      ConsoleLogger::getInstance().logError(
          "TransmissionPortListener", "Path required for Transfer file type");
      return;
    }
    buffer = Files::FilesBuilder::buildTransfer(path, data, length);
    break;
  case Files::FileType::SendConfig:
    buffer = Files::FilesBuilder::buildSendConfig(data, length);
    break;
  case Files::FileType::SetPixelBuffer:
    ConsoleLogger::getInstance().logError(
        "TransmissionPortListener",
        "Use sendPixelBuffer() for SetPixelBuffer type");
    return;
  default:
    ConsoleLogger::getInstance().logError("TransmissionPortListener",
                                          "Unknown file type: %d",
                                          static_cast<int>(type));
    return;
  }

  _lumynTp->sendTransmission(
      buffer.data(), buffer.size(),
      lumyn::internal::Transmission::TransmissionType::File);
}

uint32_t TransmissionPortListener::GenerateRequestId()
{
  std::random_device rd;
  std::uniform_int_distribution<uint32_t> dist(0, 4294967295);
  return dist(rd);
}

bool TransmissionPortListener::WaitForResponse(int timeoutMs)
{
  std::unique_lock<std::mutex> lock(_responseMutex);
  return _responseCondition.wait_for(
      lock, std::chrono::milliseconds(timeoutMs),
      [this]
      { return !_pendingRequests.empty(); });
}

void TransmissionPortListener::OnResponse(const Response::Response &response)
{
  std::lock_guard<std::mutex> lock(_responseMutex);
  auto it = _pendingRequests.find(response.header.id);
  if (it != _pendingRequests.end())
  {
    it->second(response);
    _pendingRequests.erase(it);
    _responseCondition.notify_all(); // Add this line!
  }
  else
  {
    ConsoleLogger::getInstance().logWarning(
        "TransmissionPortListener",
        "Received response for unknown request ID: %d", response.header.id);
  }
}

std::optional<Response::Response> TransmissionPortListener::SendRequest(
    Request::Request &request, int timeoutMs)
{
  uint32_t requestId = GenerateRequestId();
  request.header.id = requestId;
  request.header.type = request.header.type; // leave as set by caller

  ConsoleLogger::getInstance().logInfo(
      "TransmissionPortListener", "Sending request with ID: %d with type %d",
      requestId, static_cast<int>(request.header.type));

  // Use shared_ptr to avoid lifetime issues with Python bindings
  auto promise = std::make_shared<std::promise<Response::Response>>();
  std::future<Response::Response> future = promise->get_future();

  {
    std::lock_guard<std::mutex> lock(_responseMutex);
    _pendingRequests[requestId] =
        [promise](const Response::Response &response)
    {
      promise->set_value(response);
    };
  }

  try
  {
    if (!_lumynTp)
    {
      ConsoleLogger::getInstance().logError("TransmissionPortListener",
                                            "LumynTP is not initialized!");
      std::lock_guard<std::mutex> lock(_responseMutex);
      _pendingRequests.erase(requestId);
      return std::nullopt;
    }

    // Build request buffer based on type using RequestBuilder
    std::vector<uint8_t> requestBuffer;
    switch (request.header.type)
    {
    case lumyn::internal::Request::RequestType::Handshake:
      requestBuffer = Request::RequestBuilder::buildHandshake(
          requestId, request.data.handshake.hostSource);
      break;
    case lumyn::internal::Request::RequestType::Status:
      requestBuffer = Request::RequestBuilder::buildStatus(requestId);
      break;
    case lumyn::internal::Request::RequestType::ProductSKU:
      requestBuffer = Request::RequestBuilder::buildProductSKU(requestId);
      break;
    case lumyn::internal::Request::RequestType::ProductSerialNumber:
      requestBuffer =
          Request::RequestBuilder::buildProductSerialNumber(requestId);
      break;
    case lumyn::internal::Request::RequestType::ConfigHash:
      requestBuffer = Request::RequestBuilder::buildConfigHash(requestId);
      break;
    case lumyn::internal::Request::RequestType::AssignedId:
      requestBuffer = Request::RequestBuilder::buildAssignedId(requestId);
      break;
    case lumyn::internal::Request::RequestType::Faults:
      requestBuffer = Request::RequestBuilder::buildFaults(requestId);
      break;
    case lumyn::internal::Request::RequestType::ConfigFull:
      requestBuffer = Request::RequestBuilder::buildConfigFull(requestId);
      break;
    case lumyn::internal::Request::RequestType::ModuleStatus:
      requestBuffer = Request::RequestBuilder::buildModuleStatus(
          requestId, request.data.moduleStatus.moduleId);
      break;
    case lumyn::internal::Request::RequestType::ModuleData:
      requestBuffer = Request::RequestBuilder::buildModuleData(
          requestId, request.data.moduleData.moduleId);
      break;
    case lumyn::internal::Request::RequestType::LEDChannelStatus:
      requestBuffer = Request::RequestBuilder::buildLEDChannelStatus(
          requestId, request.data.ledChannelStatus.channelId);
      break;
    case lumyn::internal::Request::RequestType::LEDZoneStatus:
      requestBuffer = Request::RequestBuilder::buildLEDZoneStatus(
          requestId, request.data.ledZoneStatus.zoneId);
      break;
    case lumyn::internal::Request::RequestType::LatestEvent:
      requestBuffer = Request::RequestBuilder::buildLatestEvent(requestId);
      break;
    case lumyn::internal::Request::RequestType::EventFlags:
      requestBuffer = Request::RequestBuilder::buildEventFlags(requestId);
      break;
    default:
      ConsoleLogger::getInstance().logError(
          "TransmissionPortListener", "Unknown request type: %d",
          static_cast<int>(request.header.type));
      std::lock_guard<std::mutex> lock(_responseMutex);
      _pendingRequests.erase(requestId);
      return std::nullopt;
    }

    _lumynTp->sendTransmission(
        requestBuffer.data(), requestBuffer.size(),
        lumyn::internal::Transmission::TransmissionType::Request);

    ConsoleLogger::getInstance().logInfo("TransmissionPortListener",
                                         "Request sent with ID: %d", requestId);

    // Wait directly on the future with timeout
    if (future.wait_for(std::chrono::milliseconds(timeoutMs)) ==
        std::future_status::ready)
    {
      return future.get();
    }
    else
    {
      ConsoleLogger::getInstance().logError("TransmissionPortListener",
                                            "Request timed out! Request ID: %d",
                                            requestId);

      // Clean up pending request on timeout
      std::lock_guard<std::mutex> lock(_responseMutex);
      _pendingRequests.erase(requestId);
      return std::nullopt;
    }
  }
  catch (const std::exception &e)
  {
    ConsoleLogger::getInstance().logError(
        "TransmissionPortListener", "Failed to send request: %s", e.what());

    // Clean up on exception
    std::lock_guard<std::mutex> lock(_responseMutex);
    _pendingRequests.erase(requestId);
    return std::nullopt;
  }
}
