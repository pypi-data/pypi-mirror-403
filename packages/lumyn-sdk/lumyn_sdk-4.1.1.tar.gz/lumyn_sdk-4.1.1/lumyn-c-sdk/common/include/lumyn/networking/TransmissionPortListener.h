#pragma once

#include "lumyn/domain/command/Command.h"
#include "lumyn/domain/response/Response.h"
#include "lumyn/domain/request/Request.h"
#include "lumyn/domain/event/Event.h"
#include "lumyn/domain/module/ModuleData.h"
#include "lumyn/domain/transmission/Transmission.h"
#include "lumyn/util/serial/COBSEncoder.h"
#include "lumyn/util/serial/LumynTP.h"
#include "lumyn/networking/ILumynTransmissionHandler.h"
#include "lumyn/networking/ITransmissionPortListener.h"

#include <iostream>
#include <functional>
#include <condition_variable>
#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <unordered_map>
#include <vector>

namespace lumyn::internal
{
  class TransmissionPortListener : public ITransmissionPortListener
  {
  public:
    TransmissionPortListener(ILumynTransmissionHandler &handler);
    virtual ~TransmissionPortListener() override;

    using WriteBytesCallback = std::function<void(const uint8_t*, size_t)>;

    // ITransmissionPortListener implementation
    void Init() override;
    void SendCommand(const Command::CommandHeader &header, const void *payload, size_t payloadLen) override;
    void SendRawCommand(const uint8_t *data, size_t length) override;
    std::optional<Response::Response> SendRequest(Request::Request &request, int timeoutMs = 10000) override;
    void SendFile(Files::FileType type, const uint8_t *data, uint32_t length, const char *path = nullptr) override;

    void ingressBytes(const uint8_t *data, size_t length)
    {
      if (_serial)
      {
        _serial->processReadData(data, length);
      }
    }

    void setWriteCallback(WriteBytesCallback callback)
    {
      this->writeBytes = callback;
      if (_serial)
      {
        _serial->setWriteCallback(callback);
      }
    }

    // Drain buffered module data payloads for a specific module ID (hashed via IDCreator).
    bool TryPopModuleDataRaw(uint16_t moduleId, std::vector<std::vector<uint8_t>> &out);

    // Get config full data for a specific request ID
    // Returns true if data was found and copied to out
    bool GetConfigFullData(uint32_t requestId, std::vector<uint8_t> &out);

  private:
    using TransmissionClass = ::lumyn::internal::Transmission::Transmission;
    void HandleTransmission(const TransmissionClass &transmission);
    void ReadDataStream();
    uint32_t GenerateRequestId();
    bool WaitForResponse(int timeoutMs);
    void OnResponse(const Response::Response &response);

    std::unique_ptr<lumyn::internal::StandardPacketSerial> _serial;
    std::unique_ptr<lumyn::internal::StandardLumynTP> _lumynTp;
    std::thread _readThread;
    std::atomic<bool> _running;
    std::mutex _responseMutex;
    std::condition_variable _responseCondition;
    std::unordered_map<int, Response::Response> _pendingResponses;
    COBSEncoder _encoder;

    ILumynTransmissionHandler &_handler;
    std::unordered_map<int, std::function<void(const Response::Response &)>> _pendingRequests;

    WriteBytesCallback writeBytes;

    // Module data buffering
    std::mutex _moduleDataMutex;
    // Map hashed module ID -> list of raw payloads
    std::unordered_map<uint16_t, std::vector<std::vector<uint8_t>>> _moduleDataRawBuffers;

    // Config full data buffering (keyed by request ID)
    std::mutex _configFullMutex;
    std::unordered_map<uint32_t, std::vector<uint8_t>> _configFullBuffers;
  };
} // namespace lumyn::internal
