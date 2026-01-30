#pragma once

#include <cstdint>
#include <functional>

#include "PacketSerial.h"
#include "lumyn/domain/transmission/Packet.h"
#include "lumyn/domain/transmission/Transmission.h"

namespace lumyn::internal {

// Forward declare to avoid ambiguity on MSVC
using TransmissionClass = ::lumyn::internal::Transmission::Transmission;

template <typename PacketT>
class LumynTP {
 public:
  using PacketType = PacketT;
  using PacketSerialType = PacketSerial<PacketT>;

  explicit LumynTP(PacketSerialType& packetSerial)
      : _packetSerial(packetSerial),
        _lastPacketId(-1),
        _currentSlot(nullptr),
        _rxBytesFilled(0) {
    _packetSerial.setOnNewPacket(
        [this](PacketT& packet) { this->handlePacket(packet); });
  }

  ~LumynTP();

  void start();

  void sendTransmission(Transmission::Transmission* transmission);
  void sendTransmission(const uint8_t* data, size_t dataLength,
                        Transmission::TransmissionType type);

  void setOnNewTransmission(std::function<void(TransmissionClass*)> cb) {
    onNewTransmission = std::move(cb);
  }

 private:
  void handlePacket(PacketT& packet);
  void handleFirstPacket(PacketT& packet);
  void handleSubsequentPacket(PacketT& packet);
  void finalizeTransmission();

 private:
  PacketSerialType& _packetSerial;

  std::function<void(TransmissionClass*)> onNewTransmission;

  int32_t _lastPacketId;

  // RX assembly state
  Transmission::TransmissionSlot* _currentSlot;
  uint32_t _rxBytesFilled;
};

// Type aliases
using StandardLumynTP = LumynTP<lumyn::internal::Packet>;
using CANLumynTP = LumynTP<CANPacket>;

}  // namespace lumyn::internal
