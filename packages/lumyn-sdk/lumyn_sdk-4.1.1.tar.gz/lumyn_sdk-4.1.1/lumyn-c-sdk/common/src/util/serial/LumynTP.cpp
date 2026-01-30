#include "lumyn/Constants.h"
#include "lumyn/util/serial/LumynTP.h"

#include <algorithm>
#include <cstring>
#include <type_traits>

#include "lumyn/util/logging/ConsoleLogger.h"
#include "lumyn/util/serial/RLECompressor.h"
#include "lumyn/util/serial/TransmissionPool.h"
#include "lumyn/version.h"

namespace lumyn::internal
{

  using namespace Transmission;

  // Type alias to avoid ambiguity with namespace name on MSVC
  using TransmissionClass = ::lumyn::internal::Transmission::Transmission;

  // ------------------------------------------------------
  // Destructor
  // ------------------------------------------------------
  template <typename PacketT>
  LumynTP<PacketT>::~LumynTP()
  {
    // If we were in the middle of assembling a transmission, release the slot.
    if (_currentSlot)
    {
      TransmissionPool::instance().release(_currentSlot);
      _currentSlot = nullptr;
      _rxBytesFilled = 0;
      _lastPacketId = -1;
    }
  }

  // ------------------------------------------------------
  // start()
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::start()
  {
    auto &logger = ConsoleLogger::getInstance();
    logger.logInfo("LumynTP", "Starting protocol handler");
    _packetSerial.startReading();
  }

  // ------------------------------------------------------
  // TX: sendTransmission(Transmission*)
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::sendTransmission(
      TransmissionClass *transmission)
  {
    auto &logger = ConsoleLogger::getInstance();

    if (!transmission)
    {
      logger.logError("LumynTP", "Null transmission pointer");
      return;
    }

    const auto *header = transmission->getHeader();
    const uint8_t *base = transmission->getBuffer();
    if (!header || !base)
    {
      logger.logError("LumynTP", "Invalid transmission header/buffer");
      return;
    }

    const uint8_t *data = base + sizeof(TransmissionHeader);
    const size_t transmissionSize = transmission->getTotalSize();

    const uint16_t packetCount =
        (transmissionSize + _packetSerial.maxPacketBodySize() - 1) /
        _packetSerial.maxPacketBodySize();
    transmission->setPacketCount(packetCount);

    logger.logInfo("LumynTP",
                   "Sending transmission: type=%d, dataLength=%u, totalSize=%zu, "
                   "packetCount=%u",
                   static_cast<int>(header->type), header->dataLength,
                   transmissionSize, packetCount);

    PacketT packet{};
    uint32_t offset = 0;

    for (uint16_t i = 0; i < packetCount; ++i)
    {
      // Packet ID type-specific
      uint16_t packetId = i;
      if constexpr (std::is_same<typename PacketT::HeaderType,
                                 lumyn::internal::PacketHeader>::value)
      {
        packet.header.packetId = packetId;
        packet.header.crc = 0;
      }
      else
      {
        // e.g. CAN header uses uint8_t ID
        packet.header.packetId = static_cast<uint8_t>(packetId);
      }

      uint16_t bodyLen = 0;
      constexpr size_t maxPacketBufSize = PacketT::Traits::MAX_PACKET_BODY_SIZE;

      if (i == 0)
      {
        // First packet: [TransmissionHeader][payload...]
        constexpr uint16_t headerSize = sizeof(TransmissionHeader);

        // Only copy header if packet buffer is large enough
        if constexpr (maxPacketBufSize >= headerSize)
        {
          std::memcpy(packet.buf, header, headerSize);

          const uint16_t maxBody =
              static_cast<uint16_t>(_packetSerial.maxPacketBodySize() - headerSize);
          const uint16_t remaining =
              static_cast<uint16_t>(header->dataLength - offset);

          bodyLen = std::min<uint16_t>(maxBody, remaining);

          if (bodyLen > 0 && data)
          {
            std::memcpy(packet.buf + headerSize, data, bodyLen);
          }

          packet.header.length = headerSize + bodyLen;
          offset += bodyLen;

          logger.logVerbose(
              "LumynTP",
              "Packet %u (first): headerSize=%u, bodyLength=%u, totalLength=%u", i,
              headerSize, bodyLen, packet.header.length);
        }
        else
        {
          logger.logError("LumynTP", "Packet buffer too small for transmission header");
          return;
        }
      }
      else
      {
        // Subsequent packets: [payload...]
        const uint16_t remaining =
            static_cast<uint16_t>(header->dataLength - offset);
        bodyLen = std::min<uint16_t>(
            static_cast<uint16_t>(_packetSerial.maxPacketBodySize()), remaining);

        if (bodyLen > 0 && data)
        {
          std::memcpy(packet.buf, data + offset, bodyLen);
        }

        packet.header.length = bodyLen;
        offset += bodyLen;

        logger.logVerbose("LumynTP",
                          "Packet %u: offset=%u, length=%u, remaining=%u", i,
                          offset - bodyLen, bodyLen, header->dataLength - offset);
      }

      _packetSerial.send(packet);
    }

    logger.logInfo("LumynTP", "Transmission sent: %u packets, %u bytes total",
                   packetCount, offset);
  }

  // ------------------------------------------------------
  // TX: sendTransmission (legacy)
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::sendTransmission(const uint8_t *data, size_t dataLength,
                                          TransmissionType type)
  {
    auto &logger = ConsoleLogger::getInstance();
    logger.logVerbose("LumynTP",
                      "sendTransmission (legacy): type=%d, dataLength=%zu",
                      static_cast<int>(type), dataLength);

    TransmissionClass *tx = TransmissionClass::build(type, data, dataLength);
    if (!tx)
    {
      logger.logError("LumynTP", "Failed to build transmission");
      return;
    }

    tx = RLECompressor::compress(tx);

    const auto *header = tx->getHeader();
    const uint8_t *base = tx->getBuffer();
    if (!header || !base)
    {
      logger.logError("LumynTP", "Invalid transmission header/buffer");
      tx->unref();
      return;
    }

    const uint8_t *payload = base + sizeof(TransmissionHeader);
    const size_t transmissionSize = tx->getTotalSize();

    const uint16_t packetCount =
        (transmissionSize + _packetSerial.maxPacketBodySize() - 1) /
        _packetSerial.maxPacketBodySize();
    tx->setPacketCount(packetCount);

    logger.logInfo("LumynTP",
                   "Sending transmission: type=%d, dataLength=%u, totalSize=%zu, "
                   "packetCount=%u",
                   static_cast<int>(header->type), header->dataLength,
                   transmissionSize, packetCount);

    logger.logVerbose("LumynTP",
                      "Transmission buffer (%zu bytes): ", transmissionSize);
    std::string bufferStr;
    for (size_t i = 0; i < transmissionSize; ++i)
    {
      bufferStr += std::to_string(static_cast<unsigned>(base[i]));
      if (i < transmissionSize - 1)
      {
        bufferStr += " ";
      }
    }
    logger.logVerbose("LumynTP", "%s", bufferStr.c_str());

    PacketT packet{};
    uint32_t offset = 0;

    for (uint16_t i = 0; i < packetCount; ++i)
    {
      // Packet ID type-specific
      uint16_t packetId = i;
      if constexpr (std::is_same<typename PacketT::HeaderType,
                                 lumyn::internal::PacketHeader>::value)
      {
        packet.header.packetId = packetId;
        packet.header.crc = 0;
      }
      else
      {
        // e.g. CAN header uses uint8_t ID
        packet.header.packetId = static_cast<uint8_t>(packetId);
      }

      uint16_t bodyLen = 0;
      constexpr size_t maxPacketBufSize = PacketT::Traits::MAX_PACKET_BODY_SIZE;

      if (i == 0)
      {
        // First packet: [TransmissionHeader][payload...]
        constexpr uint16_t headerSize = sizeof(TransmissionHeader);

        // Only copy header if packet buffer is large enough
        if constexpr (maxPacketBufSize >= headerSize)
        {
          std::memcpy(packet.buf, header, headerSize);

          const uint16_t maxBody =
              static_cast<uint16_t>(_packetSerial.maxPacketBodySize() - headerSize);
          const uint16_t remaining =
              static_cast<uint16_t>(header->dataLength - offset);

          bodyLen = std::min<uint16_t>(maxBody, remaining);

          if (bodyLen > 0 && payload)
          {
            std::memcpy(packet.buf + headerSize, payload, bodyLen);
          }

          packet.header.length = headerSize + bodyLen;
          offset += bodyLen;

          logger.logVerbose(
              "LumynTP",
              "Packet %u (first): headerSize=%u, bodyLength=%u, totalLength=%u", i,
              headerSize, bodyLen, packet.header.length);
        }
        else
        {
          logger.logError("LumynTP", "Packet buffer too small for transmission header");
          return;
        }
      }
      else
      {
        // Subsequent packets: [payload...]
        const uint16_t remaining =
            static_cast<uint16_t>(header->dataLength - offset);
        bodyLen = std::min<uint16_t>(
            static_cast<uint16_t>(_packetSerial.maxPacketBodySize()), remaining);

        if (bodyLen > 0 && payload)
        {
          std::memcpy(packet.buf, payload + offset, bodyLen);
        }

        packet.header.length = bodyLen;
        offset += bodyLen;

        logger.logVerbose("LumynTP",
                          "Packet %u: offset=%u, length=%u, remaining=%u", i,
                          offset - bodyLen, bodyLen, header->dataLength - offset);
      }

      _packetSerial.send(packet);
    }

    logger.logInfo("LumynTP", "Transmission sent: %u packets, %u bytes total",
                   packetCount, offset);
    tx->unref();
    logger.logVerbose("LumynTP", "Transmission sent and cleaned up");
  }

  // ------------------------------------------------------
  // RX: handlePacket()
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::handlePacket(PacketT &packet)
  {
    auto &logger = ConsoleLogger::getInstance();

    uint16_t packetId;
    if constexpr (std::is_same<typename PacketT::HeaderType,
                               lumyn::internal::PacketHeader>::value)
    {
      packetId = packet.header.packetId;
    }
    else
    {
      packetId = static_cast<uint16_t>(packet.header.packetId);
    }

    logger.logVerbose("LumynTP",
                      "Handling packet: id=%u, length=%u, lastPacketId=%d",
                      packetId, packet.header.length, _lastPacketId);

    if (packetId == 0)
    {
      handleFirstPacket(packet);
    }
    else
    {
      handleSubsequentPacket(packet);
    }

    // finalize based on packetId and header.packetCount
    if (_currentSlot)
    {
      auto *hdr = reinterpret_cast<TransmissionHeader *>(_currentSlot->buffer);
      if (hdr && packetId == (hdr->packetCount - 1))
      {
        logger.logVerbose("LumynTP",
                          "Received final packet %u, finalizing transmission",
                          packetId);
        finalizeTransmission();
      }
    }
  }

  // ------------------------------------------------------
  // RX: first packet [header + first body chunk]
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::handleFirstPacket(PacketT &packet)
  {
    auto &logger = ConsoleLogger::getInstance();

    // Drop any in-progress RX
    if (_currentSlot)
    {
      logger.logWarning("LumynTP",
                        "Discarding incomplete transmission, new first packet");
      TransmissionPool::instance().release(_currentSlot);
      _currentSlot = nullptr;
      _rxBytesFilled = 0;
      _lastPacketId = -1;
    }

    if (packet.header.length < sizeof(TransmissionHeader))
    {
      logger.logError("LumynTP", "First packet too small (%u) for header",
                      packet.header.length);
      return;
    }

    TransmissionHeader header{};
    std::memcpy(&header, packet.buf, sizeof(header));

    const size_t totalSize = sizeof(TransmissionHeader) + header.dataLength;

    if (totalSize > kMaxTransmissionSize)
    {
      logger.logError("LumynTP", "Transmission too large (%u), dropping",
                      static_cast<unsigned>(totalSize));
      return;
    }

    auto &pool = TransmissionPool::instance();
    TransmissionSlot *slot = pool.acquire(totalSize);
    if (!slot)
    {
      logger.logError("LumynTP", "No transmission slots available");
      return;
    }

    slot->isRxScratch = true;

    // Copy header
    std::memcpy(slot->buffer, &header, sizeof(header));

    const size_t headerSize = sizeof(TransmissionHeader);

    size_t firstChunkSize = 0;
    if (packet.header.length > headerSize)
    {
      firstChunkSize = packet.header.length - headerSize;

      if (firstChunkSize > header.dataLength)
      {
        logger.logError("LumynTP",
                        "First packet payload %u > declared dataLength %u",
                        static_cast<unsigned>(firstChunkSize), header.dataLength);
        firstChunkSize = header.dataLength;
      }

      std::memcpy(slot->buffer + headerSize, packet.buf + headerSize,
                  firstChunkSize);

      logger.logVerbose("LumynTP",
                        "Copied %zu bytes of payload from first packet",
                        firstChunkSize);
    }

    _currentSlot = slot;
    _rxBytesFilled = static_cast<uint32_t>(firstChunkSize);
    _lastPacketId = header.packetCount - 1;

    // We record the full desired size; will be exposed when finalized.
    slot->length = totalSize;

    logger.logVerbose("LumynTP",
                      "Created RX buffer: totalSize=%zu, firstChunk=%zu",
                      totalSize, firstChunkSize);
  }

  // ------------------------------------------------------
  // RX: subsequent packets [body only]
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::handleSubsequentPacket(PacketT &packet)
  {
    auto &logger = ConsoleLogger::getInstance();

    if (!_currentSlot)
    {
      uint16_t packetId;
      if constexpr (std::is_same<typename PacketT::HeaderType,
                                 lumyn::internal::PacketHeader>::value)
      {
        packetId = packet.header.packetId;
      }
      else
      {
        packetId = static_cast<uint16_t>(packet.header.packetId);
      }

      logger.logError("LumynTP",
                      "Received packet %u before first packet, dropping",
                      packetId);
      return;
    }

    auto *hdr = reinterpret_cast<TransmissionHeader *>(_currentSlot->buffer);
    if (!hdr)
    {
      logger.logError("LumynTP", "Current RX slot has invalid header, dropping");
      TransmissionPool::instance().release(_currentSlot);
      _currentSlot = nullptr;
      _rxBytesFilled = 0;
      _lastPacketId = -1;
      return;
    }

    const uint32_t remaining = hdr->dataLength - _rxBytesFilled;

    uint16_t copyLen = packet.header.length;
    if (copyLen > remaining)
    {
      logger.logWarning("LumynTP", "Packet body %u > remaining %u, clamping",
                        copyLen, remaining);
      copyLen = static_cast<uint16_t>(remaining);
    }

    const size_t maxCapacity =
        _currentSlot->capacity - sizeof(TransmissionHeader);
    if (_rxBytesFilled + copyLen > maxCapacity)
    {
      logger.logError("LumynTP", "RX overflow: %u + %u > capacity %u, aborting",
                      _rxBytesFilled, copyLen,
                      static_cast<unsigned>(maxCapacity));
      TransmissionPool::instance().release(_currentSlot);
      _currentSlot = nullptr;
      _rxBytesFilled = 0;
      _lastPacketId = -1;
      return;
    }

    uint8_t *dest =
        _currentSlot->buffer + sizeof(TransmissionHeader) + _rxBytesFilled;
    std::memcpy(dest, packet.buf, copyLen);

    _rxBytesFilled += copyLen;

    logger.logVerbose("LumynTP",
                      "Subsequent packet: wrote %u bytes, rxBytesFilled=%u/%u",
                      copyLen, _rxBytesFilled, hdr->dataLength);
  }

  // ------------------------------------------------------
  // RX: finalizeTransmission()
  // ------------------------------------------------------
  template <typename PacketT>
  void LumynTP<PacketT>::finalizeTransmission()
  {
    auto &logger = ConsoleLogger::getInstance();

    if (!_currentSlot)
    {
      logger.logError("LumynTP", "Cannot finalize: no current slot");
      return;
    }

    auto *hdr = reinterpret_cast<TransmissionHeader *>(_currentSlot->buffer);
    if (!hdr)
    {
      logger.logError("LumynTP", "Finalize: header missing");
      TransmissionPool::instance().release(_currentSlot);
      _currentSlot = nullptr;
      _rxBytesFilled = 0;
      _lastPacketId = -1;
      return;
    }

    if (_rxBytesFilled < hdr->dataLength)
    {
      logger.logWarning("LumynTP",
                        "Finalize with incomplete payload: %u/%u bytes",
                        _rxBytesFilled, hdr->dataLength);
      // You can choose to drop instead; for now we still deliver.
    }

    // Ensure length matches declared total size
    _currentSlot->length = sizeof(TransmissionHeader) + hdr->dataLength;

    TransmissionClass *tx = TransmissionClass::adoptSlot(_currentSlot);

    _currentSlot = nullptr;
    _rxBytesFilled = 0;
    _lastPacketId = -1;

    logger.logInfo("LumynTP", "Transmission complete: type=%d, dataLength=%u",
                   static_cast<int>(hdr->type), hdr->dataLength);

    if (onNewTransmission)
    {
      onNewTransmission(tx); // receiver owns ref
    }
    else
    {
      logger.logWarning("LumynTP", "No onNewTransmission callback, dropping");
      tx->unref();
    }
  }

  // ------------------------------------------------------
  // Explicit instantiations
  // ------------------------------------------------------
  template class LumynTP<lumyn::internal::Packet>;
  template class LumynTP<CANPacket>;

} // namespace lumyn::internal
