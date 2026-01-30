#include "lumyn/Constants.h"
#include "lumyn/util/serial/PacketSerial.h"

#include "lumyn/util/logging/ConsoleLogger.h"

namespace lumyn::internal
{

  // =======================================================
  // Constructor / Destructor
  // =======================================================

  template <typename PacketT>
  PacketSerial<PacketT>::PacketSerial(IEncoder *encoder, size_t maxPacketSize)
      : _encoder(encoder), _maxPacketSize(maxPacketSize)
  {
    ConsoleLogger::getInstance().logVerbose(
        "PacketSerial", "Initialized: maxPacketSize=%zu, ringSize=%zu",
        maxPacketSize, _rxRing.available());
  }

  template <typename PacketT>
  PacketSerial<PacketT>::~PacketSerial()
  {
    ConsoleLogger::getInstance().logVerbose("PacketSerial", "Destroyed");
  }

  // =======================================================
  // Reading Control
  // =======================================================

  template <typename PacketT>
  void PacketSerial<PacketT>::startReading()
  {
    _reading = true;
    ConsoleLogger::getInstance().logVerbose("PacketSerial", "Start reading");
  }

  template <typename PacketT>
  void PacketSerial<PacketT>::stopReading()
  {
    _reading = false;
    ConsoleLogger::getInstance().logVerbose("PacketSerial", "Stop reading");
  }

  // =======================================================
  // Packet Send (COBS Encode)
  // =======================================================

  template <typename PacketT>
  void PacketSerial<PacketT>::send(PacketT &packet)
  {
    auto &logger = ConsoleLogger::getInstance();

    if (packet.header.length > maxPacketBodySize())
    {
      logger.logError("PacketSerial", "Packet body too large: %u > %zu",
                      packet.header.length, maxPacketBodySize());
      return;
    }

    // Serialize packet to raw buffer
    uint8_t rawBuffer[PacketT::maxPacketSize()];
    size_t packetSize = 0;
    PacketT::toBuffer(packet, rawBuffer, packetSize);

    size_t encodedSize = _encoder->getEncodedBufferSize(packetSize);

    uint8_t encodedBuffer[PacketT::maxPacketSize() + COBS_OVERHEAD];
    _encoder->encode(rawBuffer, packetSize, encodedBuffer);

    // COBS packet terminator
    encodedBuffer[encodedSize] = PACKET_MARKER;

    if (writeBytes)
      writeBytes(encodedBuffer, encodedSize + 1);
    else
      logger.logError("PacketSerial", "Write callback not set");
  }

  // =======================================================
  // PROCESS INCOMING BYTES (RING-DRIVEN PARSER)
  // =======================================================

  template <typename PacketT>
  void PacketSerial<PacketT>::processReadData(const uint8_t *data, size_t len)
  {
    if (!_reading || len == 0)
      return;

    auto &logger = ConsoleLogger::getInstance();
    logger.logVerbose("PacketSerial", "RX %zu bytes (ringAvail=%zu)", len,
                      _rxRing.available());

    // Push into ring
    for (size_t i = 0; i < len; ++i)
    {
      if (!_rxRing.push(data[i]))
      {
        if (onOverflow)
          onOverflow();
        logger.logWarning("PacketSerial",
                          "Ring overflow, byte dropped at idx=%zu", i);
      }
    }

    // Process ring → decode → packet extract
    uint8_t b = 0;
    while (_rxRing.pop(b))
    {
      if (b == PACKET_MARKER)
      {
        // End of packet marker
        if (_tmpPacketIndex == 0)
        {
          // ignore empty packet
          continue;
        }

        uint8_t decodeBuf[PacketT::maxPacketSize()];
        size_t decodedSize =
            _encoder->decode(_tmpPacketBuffer, _tmpPacketIndex, decodeBuf);

        logger.logVerbose("PacketSerial",
                          "Decoded %zu bytes from %zu encoded bytes", decodedSize,
                          _tmpPacketIndex);

        // Reset accumulator
        _tmpPacketIndex = 0;

        PacketT pkt = PacketT::fromBuffer(decodeBuf, decodedSize);

        logger.logVerbose("PacketSerial", "Packet received: bodyLen=%u",
                          pkt.header.length);

        if (onNewPacket)
          onNewPacket(pkt);
      }
      else
      {
        // Append to COBS scratch buffer
        if (_tmpPacketIndex < sizeof(_tmpPacketBuffer))
        {
          _tmpPacketBuffer[_tmpPacketIndex++] = b;
        }
        else
        {
          logger.logError("PacketSerial", "tmpPacketBuffer overflow: idx=%zu",
                          _tmpPacketIndex);
          if (onPacketOverflow)
            onPacketOverflow();
          _tmpPacketIndex = 0;
        }
      }
    }
  }

  // -------------------------------------------------------
  // Explicit template instantiation
  // -------------------------------------------------------
  template class PacketSerial<Packet>;
  template class PacketSerial<CANPacket>;

} // namespace lumyn::internal
