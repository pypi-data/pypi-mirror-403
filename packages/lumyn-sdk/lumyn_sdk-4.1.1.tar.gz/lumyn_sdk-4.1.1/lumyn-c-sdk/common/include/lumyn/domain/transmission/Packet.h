#pragma once

#include <cstdint>
#include <cstring>
#include <iostream>

#include "lumyn/packed.h"
#include "lumyn/util/logging/ConsoleLogger.h"

namespace lumyn::internal {

constexpr uint8_t PACKET_MARKER = 0x00;
constexpr uint8_t COBS_OVERHEAD = 3;

// Standard packet header for serial/stream protocols
PACK(struct PacketHeader {
  uint16_t packetId;
  uint8_t length;
  uint8_t crc;

  static constexpr size_t baseSize() {
    return sizeof(packetId) + sizeof(length) + sizeof(crc);
  }
});

// CAN-specific packet header (fits in CAN extended ID + data)
PACK(struct PacketCANHeader {
  uint8_t packetId;  // 8-bit packet ID (up to 256 packets per transmission)
  uint8_t length;    // Data length in this packet

  static constexpr size_t baseSize() {
    return sizeof(packetId) + sizeof(length);
  }
});

// Packet traits - define packet characteristics for each header type
template <typename HeaderT>
struct PacketTraits;

template <>
struct PacketTraits<PacketHeader> {
  static constexpr size_t PACKET_SIZE = 256;
  static constexpr size_t MAX_PACKET_SIZE = PACKET_SIZE - COBS_OVERHEAD;
  static constexpr size_t MAX_PACKET_BODY_SIZE =
      MAX_PACKET_SIZE - sizeof(PacketHeader);
  using HeaderType = PacketHeader;
};

template <>
struct PacketTraits<PacketCANHeader> {
  static constexpr size_t PACKET_SIZE = 10;
  static constexpr size_t MAX_PACKET_SIZE = PACKET_SIZE - COBS_OVERHEAD;
  // CAN 2.0 max frame size + 2 bytes of ID
  static constexpr size_t MAX_PACKET_BODY_SIZE =
      MAX_PACKET_SIZE - sizeof(PacketCANHeader);
  using HeaderType = PacketCANHeader;
};

// Generic packet structure
template <typename HeaderT>
struct TPacket {
  using Traits = PacketTraits<HeaderT>;
  using HeaderType = typename Traits::HeaderType;

  HeaderType header;
  uint8_t buf[Traits::MAX_PACKET_BODY_SIZE];

  static TPacket fromBuffer(const uint8_t buffer[], size_t bufferSize) {
    if (bufferSize < HeaderType::baseSize()) {
      lumyn::internal::ConsoleLogger::getInstance().logError(
          "Packet", "Buffer is too small to contain packet header");
    }

    TPacket packet;
    size_t offset = 0;

    // Copy header
    memcpy(&packet.header, buffer, sizeof(HeaderType));
    offset += sizeof(HeaderType);

    if (packet.header.length > Traits::MAX_PACKET_BODY_SIZE) {
      lumyn::internal::ConsoleLogger::getInstance().logError(
          "Packet", "Packet body is too large: %u > %zu", packet.header.length,
          Traits::MAX_PACKET_BODY_SIZE);
    }

    if (bufferSize < offset + packet.header.length) {
      lumyn::internal::ConsoleLogger::getInstance().logError(
          "Packet", "Buffer is too small to contain packet body");
    }

    std::memcpy(packet.buf, buffer + offset, packet.header.length);

    return packet;
  }

  static void toBuffer(const TPacket& packet, uint8_t* buffer,
                       size_t& bufferSize) {
    size_t offset = 0;

    // Copy header
    memcpy(buffer, &packet.header, sizeof(HeaderType));
    offset += sizeof(HeaderType);

    // Copy body
    memcpy(buffer + offset, packet.buf, packet.header.length);
    offset += packet.header.length;

    bufferSize = offset;
  }

  static constexpr size_t maxPacketSize() { return Traits::MAX_PACKET_SIZE; }

  static constexpr size_t maxBodySize() { return Traits::MAX_PACKET_BODY_SIZE; }
};

// Type aliases for convenience
using Packet = TPacket<PacketHeader>;
using CANPacket = TPacket<PacketCANHeader>;

}  // namespace lumyn::internal