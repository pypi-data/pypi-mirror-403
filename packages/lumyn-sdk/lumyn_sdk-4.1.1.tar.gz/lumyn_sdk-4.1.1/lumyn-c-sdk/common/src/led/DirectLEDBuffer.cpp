#include "lumyn/led/DirectLEDBuffer.h"
#include "lumyn/domain/command/CommandBuilder.h"
#include "lumyn/util/hashing/IDCreator.h"
#include "lumyn/util/serial/DeltaCompressor.h"

#include <cstring>

namespace lumyn::internal
{

  DirectLEDBuffer::DirectLEDBuffer(std::string_view zoneId, size_t length)
      : _zoneId(IDCreator::createId(zoneId)),
        _bufferLength(length),
        _paddedLength(calculatePaddedLength(length))
  {
  }

  DirectLEDBuffer::DirectLEDBuffer(uint16_t zoneId, size_t length)
      : _zoneId(zoneId),
        _bufferLength(length),
        _paddedLength(calculatePaddedLength(length))
  {
  }

  size_t DirectLEDBuffer::calculatePaddedLength(size_t length)
  {
    const size_t remainder = length % 4;
    return (remainder == 0) ? length : length + (4 - remainder);
  }

  std::vector<uint8_t> DirectLEDBuffer::update(const uint8_t *data, size_t length, bool useDelta)
  {
    // Validate length matches expected
    if (length != _bufferLength)
    {
      // Length mismatch - return empty to signal error
      // Caller should check for empty result
      return {};
    }

    // Create padded buffer
    std::vector<uint8_t> paddedData(_paddedLength, 0);
    std::memcpy(paddedData.data(), data, length);

    bool isDelta = false;
    std::vector<uint8_t> dataToSend;

    // Attempt delta compression if enabled and we have a previous buffer
    if (useDelta && !_previousBuffer.empty())
    {
      // Encode delta (XOR current against previous)
      DeltaCompressor::encode(paddedData.data(), _previousBuffer.data(),
                              _paddedLength, dataToSend);
      isDelta = true;
    }
    else
    {
      // Send full buffer
      dataToSend = paddedData;
      isDelta = false;
    }

    // Store current buffer for next delta comparison
    _previousBuffer = std::move(paddedData);

    // Build and return command bytes
    return Command::CommandBuilder::buildSetDirectBuffer(
        _zoneId, dataToSend.data(), static_cast<uint16_t>(dataToSend.size()), isDelta);
  }

  std::vector<uint8_t> DirectLEDBuffer::update(const std::vector<uint8_t> &data, bool useDelta)
  {
    return update(data.data(), data.size(), useDelta);
  }

  std::vector<uint8_t> DirectLEDBuffer::forceFullUpdate(const uint8_t *data, size_t length)
  {
    return update(data, length, false);
  }

  void DirectLEDBuffer::reset()
  {
    _previousBuffer.clear();
  }

} // namespace lumyn::internal
