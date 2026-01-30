#include "lumyn/cpp/util/SerialIOAdapter.hpp"
#include <lumyn/util/serial/ISerialIO.h>

namespace lumyn::internal {

SerialIOAdapter::SerialIOAdapter(const lumyn_serial_io_t& io) : io_(io) {}

SerialIOAdapter::~SerialIOAdapter() {
  if (io_.close) io_.close(io_.user);
}

void SerialIOAdapter::writeBytes(const uint8_t* data, size_t length) {
  if (io_.write_bytes) {
    io_.write_bytes(io_.user, data, length);
  } else if (io_.write) {
    io_.write(io_.user, data, length);
  }
}

void SerialIOAdapter::setReadCallback(std::function<void(const uint8_t*, size_t)> callback) {
  std::lock_guard<std::mutex> lock(cb_mutex_);
  cb_ = std::move(callback);
  if (!io_.set_read_callback) return;
  
  io_.set_read_callback(io_.user, [](const uint8_t* data, size_t len, void* user) {
    auto* self = static_cast<SerialIOAdapter*>(user);
    std::function<void(const uint8_t*, size_t)> cb_copy;
    {
      std::lock_guard<std::mutex> lock(self->cb_mutex_);
      cb_copy = self->cb_;
    }
    if (cb_copy) cb_copy(data, len);
  }, this);
}

} // namespace lumyn::internal
