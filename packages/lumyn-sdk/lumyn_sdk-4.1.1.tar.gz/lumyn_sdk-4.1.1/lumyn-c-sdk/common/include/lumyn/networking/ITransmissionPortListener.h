#pragma once

#include "lumyn/domain/command/Command.h"
#include "lumyn/domain/response/Response.h"
#include "lumyn/domain/request/Request.h"
#include "lumyn/domain/file/FileType.h"
#include <optional>

namespace lumyn::internal
{
  class ITransmissionPortListener
  {
  public:
    virtual ~ITransmissionPortListener() {}

    // Initialize the lumynTP and begin reading
    virtual void Init() = 0;

    // Send a command (fire and forget): header + payload bytes
    virtual void SendCommand(const Command::CommandHeader &header, const void *payload, size_t payloadLen) = 0;

    // Send pre-built command bytes (already includes header)
    virtual void SendRawCommand(const uint8_t *data, size_t length) = 0;

    // Send a request and wait for response
    virtual std::optional<Response::Response> SendRequest(Request::Request &request, int timeoutMs = 10000) = 0;

    // Send a file
    virtual void SendFile(Files::FileType type, const uint8_t *data, uint32_t length, const char *path = nullptr) = 0;
  };
}