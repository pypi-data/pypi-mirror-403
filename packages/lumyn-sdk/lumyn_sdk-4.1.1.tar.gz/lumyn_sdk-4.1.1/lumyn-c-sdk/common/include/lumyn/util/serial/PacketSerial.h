#pragma once

#include <atomic>
#include <cstdint>
#include <functional>

#include "lumyn/domain/transmission/Packet.h"
#include "lumyn/util/serial/IEncoder.h"
#include "lumyn/util/serial/RxByteRing.h"

namespace lumyn::internal {

template <typename PacketT>
class PacketSerial {
 public:
  using PacketType = PacketT;
  using HeaderType = typename PacketT::HeaderType;
  using Traits = typename PacketT::Traits;

  PacketSerial(IEncoder* encoder,
               size_t maxPacketSize = PacketT::maxPacketSize());

  ~PacketSerial();

  void startReading();
  void stopReading();

  void send(PacketT& packet);

  inline size_t maxPacketBodySize() const {
    return _maxPacketSize - HeaderType::baseSize();
  }

  // ---- Callbacks ----
  inline void setOnOverflow(std::function<void()> cb) { onOverflow = cb; }

  inline void setOnPacketOverflow(std::function<void()> cb) {
    onPacketOverflow = cb;
  }

  inline void setOnNewPacket(std::function<void(PacketT&)> cb) {
    onNewPacket = cb;
  }

  inline void setWriteCallback(std::function<void(const uint8_t*, size_t)> cb) {
    writeBytes = cb;
  }

  // ---- Input Bytes ----
  void processReadData(const uint8_t* data, size_t length);

 private:
  IEncoder* _encoder;
  size_t _maxPacketSize;

  RxByteRing<4096> _rxRing;

  // COBS decode scratch
  uint8_t _tmpPacketBuffer[PacketT::maxPacketSize() + COBS_OVERHEAD];
  size_t _tmpPacketIndex = 0;

  std::atomic<bool> _reading{false};

  std::function<void()> onOverflow;
  std::function<void()> onPacketOverflow;
  std::function<void(PacketT&)> onNewPacket;
  std::function<void(const uint8_t*, size_t)> writeBytes;
};

// Aliases
using StandardPacketSerial = PacketSerial<lumyn::internal::Packet>;
using CANPacketSerial = PacketSerial<CANPacket>;

}  // namespace lumyn::internal
