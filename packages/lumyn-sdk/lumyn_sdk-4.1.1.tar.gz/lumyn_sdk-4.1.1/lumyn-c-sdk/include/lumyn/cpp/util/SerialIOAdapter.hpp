#pragma once

#include "lumyn/c/serial_io.h"
// ISerialIO.h is a pure abstract interface (no implementation details) that is
// safe to expose publicly. It's located in util/serial/ for organizational
// purposes but contains no protocol or transmission stack details.
// See allowed_common_headers.txt for justification.
#include <lumyn/util/serial/ISerialIO.h>
#include <functional>
#include <mutex>

namespace lumyn::internal {

/**
 * @brief Adapter that wraps lumyn_serial_io_t (C API) to implement ISerialIO (C++ interface)
 * 
 * This adapter allows the C++ device implementations to use the C serial I/O API
 * through the ISerialIO interface. It handles thread-safe callback management
 * and supports both write_bytes and legacy write methods.
 * 
 * @note This is an internal utility class. While it's in the public headers,
 *       it includes internal dependencies and is primarily for SDK implementation use.
 */
class SerialIOAdapter : public ISerialIO {
public:
  explicit SerialIOAdapter(const lumyn_serial_io_t& io);
  ~SerialIOAdapter() override;

  void writeBytes(const uint8_t* data, size_t length) override;
  void setReadCallback(std::function<void(const uint8_t*, size_t)> callback) override;

private:
  lumyn_serial_io_t io_;
  std::mutex cb_mutex_;
  std::function<void(const uint8_t*, size_t)> cb_;
};

} // namespace lumyn::internal
