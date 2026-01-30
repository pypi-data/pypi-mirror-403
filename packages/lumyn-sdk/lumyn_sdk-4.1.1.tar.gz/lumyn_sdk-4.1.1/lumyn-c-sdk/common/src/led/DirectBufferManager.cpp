#include "lumyn/led/DirectBufferManager.h"

namespace lumyn::internal
{

  DirectBufferManager::DirectBufferManager(std::string_view zoneId, size_t length, int fullRefreshInterval)
      : _buffer(zoneId, length),
        _fullRefreshInterval(fullRefreshInterval),
        _frameCount(0)
  {
  }

  DirectBufferManager::DirectBufferManager(uint16_t zoneId, size_t length, int fullRefreshInterval)
      : _buffer(zoneId, length),
        _fullRefreshInterval(fullRefreshInterval),
        _frameCount(0)
  {
  }

  std::vector<uint8_t> DirectBufferManager::update(const uint8_t *data, size_t length)
  {
    // First frame or periodic full refresh (when interval > 0)
    bool needsFullRefresh = !_buffer.hasPreviousBuffer() ||
                            (_fullRefreshInterval > 0 && _frameCount >= _fullRefreshInterval);

    if (needsFullRefresh)
    {
      _frameCount = 0;
      return _buffer.forceFullUpdate(data, length);
    }

    _frameCount++;
    return _buffer.update(data, length, true);
  }

  std::vector<uint8_t> DirectBufferManager::update(const std::vector<uint8_t> &data)
  {
    return update(data.data(), data.size());
  }

  std::vector<uint8_t> DirectBufferManager::forceFullUpdate(const uint8_t *data, size_t length)
  {
    _frameCount = 0;
    return _buffer.forceFullUpdate(data, length);
  }

  void DirectBufferManager::reset()
  {
    _buffer.reset();
    _frameCount = 0;
  }

} // namespace lumyn::internal
