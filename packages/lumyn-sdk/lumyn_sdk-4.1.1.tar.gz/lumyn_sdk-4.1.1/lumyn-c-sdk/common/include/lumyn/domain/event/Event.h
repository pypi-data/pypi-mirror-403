#pragma once

#include <cstring>
#include <cstdlib>

#include "lumyn/domain/event/EventType.h"
#include "lumyn/packed.h"
#include "lumyn/util/RefCounted.h"
#include "lumyn/types/events.h"

namespace lumyn::internal::Eventing {

PACK(struct BeginInitInfo{});
PACK(struct FinishInitInfo{});
PACK(struct EnabledInfo{});

// DisabledCause is now defined in lumyn/types/events.h as lumyn_disabled_cause_t
enum class DisabledCause : uint8_t {
  NoHeartbeat = LUMYN_DISABLED_NO_HEARTBEAT,
  Manual = LUMYN_DISABLED_MANUAL,
  EStop = LUMYN_DISABLED_ESTOP,
  Restart = LUMYN_DISABLED_RESTART,
};

PACK(struct DisabledInfo { DisabledCause cause; });

// ConnectionType is now defined in lumyn/types/events.h as lumyn_connection_type_t
enum class ConnectionType : uint8_t {
  USB = LUMYN_CONNECTION_USB,
  WebUSB = LUMYN_CONNECTION_WEBUSB,
  I2C = LUMYN_CONNECTION_I2C,
  CAN = LUMYN_CONNECTION_CAN,
  UART = LUMYN_CONNECTION_UART,
};

PACK(struct ConnectedInfo { ConnectionType type; });
PACK(struct DisconnectedInfo { ConnectionType type; });

// ErrorType is now defined in lumyn/types/events.h as lumyn_error_type_t
enum class ErrorType : uint8_t {
  FileNotFound = LUMYN_ERROR_FILE_NOT_FOUND,
  InvalidFile = LUMYN_ERROR_INVALID_FILE,
  EntityNotFound = LUMYN_ERROR_ENTITY_NOT_FOUND,
  DeviceMalfunction = LUMYN_ERROR_DEVICE_MALFUNCTION,
  QueueFull = LUMYN_ERROR_QUEUE_FULL,
  LedStrip = LUMYN_ERROR_LED_STRIP,
  LedMatrix = LUMYN_ERROR_LED_MATRIX,
  InvalidAnimationSequence = LUMYN_ERROR_INVALID_ANIMATION_SEQUENCE,
  InvalidChannel = LUMYN_ERROR_INVALID_CHANNEL,
  DuplicateID = LUMYN_ERROR_DUPLICATE_ID,
  InvalidConfigUpload = LUMYN_ERROR_INVALID_CONFIG_UPLOAD,
  ModuleError = LUMYN_ERROR_MODULE,
};

PACK(struct ErrorInfo {
  ErrorType type;
  char message[16];
});

// FatalErrorType is now defined in lumyn/types/events.h as lumyn_fatal_error_type_t
enum class FatalErrorType : uint8_t {
  InitError = LUMYN_FATAL_INIT_ERROR,
  BadConfig = LUMYN_FATAL_BAD_CONFIG,
  StartTask = LUMYN_FATAL_START_TASK,
  CreateQueue = LUMYN_FATAL_CREATE_QUEUE,
};

PACK(struct FatalErrorInfo {
  FatalErrorType type;
  char message[16];
});

PACK(struct ErrorFlags {
  union {
    struct {
  uint16_t nonFatalErrors;
  uint16_t fatalErrors;
    };
    uint32_t errors;
  };

  void raiseError(ErrorType error) {
    nonFatalErrors |= (1 << static_cast<uint32_t>(error));
  }
  void raiseError(FatalErrorType error) {
    fatalErrors |= (1 << static_cast<uint32_t>(error));
  }
  void clearError(ErrorType error) {
    nonFatalErrors &= ~(1 << static_cast<uint16_t>(error));
  }
  void clearError(FatalErrorType error) {
    fatalErrors &= ~(1 << static_cast<uint16_t>(error));
  }
  void clearError(uint32_t bitmask) { errors &= ~bitmask; }
  bool isErrorSet(ErrorType error) const {
    return nonFatalErrors & (1 << static_cast<uint16_t>(error));
  }
  bool isErrorSet(FatalErrorType error) const {
    return fatalErrors & (1 << static_cast<uint16_t>(error));
  }
});

PACK(struct RegisteredEntityInfo { uint16_t id; });

PACK(struct CustomInfo {
  uint8_t type;
  uint8_t data[16];
  uint8_t length;
});

PACK(struct PinInterruptInfo {
  uint8_t pin;
  void* param;
});

PACK(struct HeartBeatInfo {
  Status status;
  uint8_t enabled;
  uint8_t connectedUSB;
  uint8_t canOK;
});

class ExtraMessagePayload : public RefCounted {
 public:
  uint16_t length;
  uint8_t data[];  // Flexible array member

  static ExtraMessagePayload* create(const uint8_t* msgData,
                                     uint16_t msgLength) {
    if (!msgData || msgLength == 0) return nullptr;

    // Allocate payload + data in one block
    void* mem = malloc(sizeof(ExtraMessagePayload) + msgLength);
    if (!mem) return nullptr;

    auto* payload = new (mem) ExtraMessagePayload();
    payload->length = msgLength;
    memcpy(payload->data, msgData, msgLength);

    return payload;
  }

  static ExtraMessagePayload* create(const char* str) {
    if (!str) return nullptr;
    size_t len = strlen(str) + 1;  // +1 for null terminator
    return create(reinterpret_cast<const uint8_t*>(str),
                  static_cast<uint16_t>(len));
  }

  /**
   * @brief Override unref to properly deallocate malloc'd memory.
   * 
   * Since this class is allocated with malloc() + placement new instead of operator new,
   * we must manually call the destructor and then use free() instead of delete.
   */
  void unref() const override
  {
    if (decrementRefCount())
    {
      // Explicitly call destructor for any cleanup
      const_cast<ExtraMessagePayload*>(this)->~ExtraMessagePayload();
      // Free using malloc's counterpart instead of delete
      free(const_cast<ExtraMessagePayload*>(this));
    }
  }

 protected:
  ExtraMessagePayload() : RefCounted(), length(0) {}
  ~ExtraMessagePayload() override = default;
};

PACK(union EventData {
  BeginInitInfo beginInit;
  FinishInitInfo finishInit;
  EnabledInfo enabled;
  DisabledInfo disabled;
  ConnectedInfo connected;
  DisconnectedInfo disconnected;
  ErrorInfo error;
  FatalErrorInfo fatalError;
  RegisteredEntityInfo registeredEntity;
  CustomInfo custom;
  PinInterruptInfo pinInterrupt;
  HeartBeatInfo heartBeat;
});

PACK(struct EventHeader {
  EventType type;
  EventData data;
});

struct Event {
  EventHeader header;
  ExtraMessagePayload* extraMsg;

  Event()
      : header({.type = EventType::BeginInitialization}), extraMsg(nullptr) {
    memset(&header.data.beginInit, 0, sizeof(EventData));
  }

  Event(EventHeader hdr) : header(hdr), extraMsg(nullptr) {}

  Event(EventHeader hdr, const char* msg) : header(hdr), extraMsg(nullptr) {
    setExtraMessage(msg);
  }

  Event(const Event& other) : header(other.header), extraMsg(other.extraMsg) {
    if (extraMsg) {
      extraMsg->ref();
    }
  }

  Event(Event&& other) noexcept
      : header(other.header), extraMsg(other.extraMsg) {
    other.extraMsg = nullptr;
  }

  Event& operator=(const Event& other) {
    if (this != &other) {
      if (extraMsg) extraMsg->unref();

      header = other.header;
      extraMsg = other.extraMsg;

      if (extraMsg) extraMsg->ref();
    }
    return *this;
  }

  Event& operator=(Event&& other) noexcept {
    if (this != &other) {
      if (extraMsg) extraMsg->unref();

      header = std::move(other.header);
      extraMsg = other.extraMsg;

      other.extraMsg = nullptr;
    }
    return *this;
  }

  ~Event() {
    if (extraMsg) {
      extraMsg->unref();
    }
  }

  void setExtraMessage(const uint8_t* data, uint16_t length) {
    if (extraMsg) {
      extraMsg->unref();
      extraMsg = nullptr;
    }

    if (data && length > 0) {
      extraMsg = ExtraMessagePayload::create(data, length);
    }
  }

  void setExtraMessage(const char* str) {
    if (extraMsg) {
      extraMsg->unref();
      extraMsg = nullptr;
    }

    if (str) {
      extraMsg = ExtraMessagePayload::create(str);
    }
  }

  const uint8_t* getExtraMessage() const {
    return extraMsg ? extraMsg->data : nullptr;
  }

  uint16_t getExtraMessageLength() const {
    return extraMsg ? extraMsg->length : 0;
  }

  const char* getExtraMessageStr() const {
    return extraMsg ? reinterpret_cast<const char*>(extraMsg->data) : nullptr;
  }

  bool hasExtraMessage() const { return extraMsg != nullptr; }
};

static_assert(sizeof(Event) <= 32, "Event should be compact (~24-28 bytes)");

}  // namespace lumyn::internal::Eventing
