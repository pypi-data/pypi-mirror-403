#include "lumyn/c/serial_io.h"
#include "lumyn/Constants.h"

#include <atomic>
#include <cstring>
#include <memory>
#include <string>
#include <thread>

#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <termios.h>
#include <unistd.h>
#endif
#endif

namespace lumyn_c_sdk::serial
{

#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL

  typedef void (*lumyn_serial_read_cb)(const uint8_t *data, size_t len, void *user);

// Constants for Windows serial configuration
#if defined(_WIN32)
  // Windows COMMTIMEOUTS: Use minimal blocking timeouts for high throughput.
  // ReadIntervalTimeout = MAXDWORD + ReadTotalTimeoutMultiplier = 0 + ReadTotalTimeoutConstant = 0
  // means return immediately with whatever is available (non-blocking read).
  static constexpr DWORD WIN_READ_INTERVAL_TIMEOUT_MS = MAXDWORD;
  static constexpr DWORD WIN_READ_TOTAL_TIMEOUT_CONSTANT_MS = 0;
  static constexpr DWORD WIN_READ_TOTAL_TIMEOUT_MULTIPLIER = 0;
  static constexpr DWORD WIN_WRITE_TOTAL_TIMEOUT_CONSTANT_MS = 100; // Allow up to 100ms for writes
  static constexpr DWORD WIN_WRITE_TOTAL_TIMEOUT_MULTIPLIER = 0;
  static constexpr DWORD WIN_READ_RETRY_SLEEP_MS = 1; // Reduced from 10ms
  static constexpr DWORD WIN_BYTE_SIZE = 8;
#endif

// Constants for POSIX serial configuration
#if !defined(_WIN32)
  // Poll with a short timeout in the background thread; manual update can pass its own timeout.
  static constexpr int POLL_TIMEOUT_MS = 50;
  static constexpr int POLL_EVENTS = POLLIN;
#endif

#if defined(_WIN32)

  struct WinSerial
  {
    HANDLE handle{INVALID_HANDLE_VALUE};
    std::atomic<bool> running{false};
    std::thread reader;
    std::atomic<lumyn_serial_read_cb> cb{nullptr};
    std::atomic<void *> cb_user{nullptr};
    bool use_threading{true};

    ~WinSerial() { close(); }

    void start_thread()
    {
      if (running.load())
        return;
      running.store(true);
      reader = std::thread([this]()
                           {
      uint8_t buf[512];
      while (running.load()) {
        DWORD read = 0;
        if (ReadFile(handle, buf, sizeof(buf), &read, nullptr) && read > 0) {
          auto cb_local = cb.load();
          if (cb_local) cb_local(buf, static_cast<size_t>(read), cb_user.load());
        } else {
          Sleep(WIN_READ_RETRY_SLEEP_MS);
        }
      } });
    }

    void stop_thread()
    {
      running.store(false);
      if (handle != INVALID_HANDLE_VALUE)
      {
        CancelIoEx(handle, nullptr);
      }
      if (reader.joinable())
        reader.join();
    }

    void close()
    {
      stop_thread();
      if (handle != INVALID_HANDLE_VALUE)
      {
        CloseHandle(handle);
        handle = INVALID_HANDLE_VALUE;
      }
    }

    lumyn_error_t set_threading(bool enable)
    {
      if (enable == use_threading)
        return LUMYN_OK;
      use_threading = enable;
      if (use_threading)
        start_thread();
      else
        stop_thread();
      return LUMYN_OK;
    }

    lumyn_error_t update(int timeout_ms)
    {
      if (use_threading)
        return LUMYN_OK;
      uint8_t buf[512];
      DWORD read = 0;
      if (ReadFile(handle, buf, sizeof(buf), &read, nullptr) && read > 0)
      {
        auto cb_local = cb.load();
        if (cb_local)
          cb_local(buf, static_cast<size_t>(read), cb_user.load());
      }
      else if (timeout_ms > 0)
      {
        Sleep(static_cast<DWORD>(timeout_ms));
      }
      return LUMYN_OK;
    }

    lumyn_error_t update() { return update(0); }
  };

  static void win_write(void *user, const uint8_t *data, size_t len)
  {
    if (!user || (!data && len))
      return;
    auto *port = static_cast<WinSerial *>(user);
    DWORD written = 0;
    WriteFile(port->handle, data, (DWORD)len, &written, nullptr);
    // Note: Removed FlushFileBuffers() - it blocks until all data is physically
    // written which severely impacts throughput on USB CDC serial ports.
    // Windows serial driver handles buffering appropriately without explicit flush.
  }

  static void win_set_read_cb(void *user, lumyn_serial_read_cb cb, void *cb_user)
  {
    if (!user)
      return;
    auto *port = static_cast<WinSerial *>(user);
    port->cb.store(cb);
    port->cb_user.store(cb_user);
  }

  static void win_close(void *user)
  {
    if (user)
      delete static_cast<WinSerial *>(user);
  }

  static lumyn_error_t open_windows(const char *path, int baud, lumyn_serial_io_t *out_io)
  {
    auto *port = new WinSerial();
    port->handle = CreateFileA(path, GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr);
    if (port->handle == INVALID_HANDLE_VALUE)
    {
      delete port;
      return LUMYN_ERR_IO;
    }

    DCB dcb = {sizeof(DCB)};
    if (!GetCommState(port->handle, &dcb))
    {
      port->close();
      delete port;
      return LUMYN_ERR_IO;
    }
    dcb.BaudRate = baud;
    dcb.ByteSize = WIN_BYTE_SIZE;
    dcb.Parity = NOPARITY;
    dcb.StopBits = ONESTOPBIT;
    dcb.fDtrControl = DTR_CONTROL_ENABLE; // Enable DTR for USB CDC devices
    dcb.fRtsControl = RTS_CONTROL_ENABLE; // Enable RTS as well
    if (!SetCommState(port->handle, &dcb))
    {
      port->close();
      delete port;
      return LUMYN_ERR_IO;
    }

    // Also explicitly set DTR signal
    EscapeCommFunction(port->handle, SETDTR);

    COMMTIMEOUTS to = {
        WIN_READ_INTERVAL_TIMEOUT_MS,
        WIN_READ_TOTAL_TIMEOUT_MULTIPLIER,
        WIN_READ_TOTAL_TIMEOUT_CONSTANT_MS,
        WIN_WRITE_TOTAL_TIMEOUT_MULTIPLIER,
        WIN_WRITE_TOTAL_TIMEOUT_CONSTANT_MS,
    };
    SetCommTimeouts(port->handle, &to);

    if (port->use_threading)
      port->start_thread();
    out_io->user = port;
    out_io->write = win_write;
    out_io->write_bytes = win_write;
    out_io->set_read_callback = win_set_read_cb;
    out_io->close = win_close;
    return LUMYN_OK;
  }

#else

  struct PosixSerial
  {
    int fd{-1};
    std::atomic<bool> running{false};
    std::thread reader;
    std::atomic<lumyn_serial_read_cb> cb{nullptr};
    std::atomic<void *> cb_user{nullptr};
    bool use_threading{true};

    ~PosixSerial() { close(); }

    void start_thread()
    {
      if (running.load())
        return;
      running.store(true);
      reader = std::thread([this]()
                           {
      uint8_t buf[512];
      pollfd pfd{ fd, POLL_EVENTS, 0 };
      while (running.load()) {
        if (::poll(&pfd, 1, POLL_TIMEOUT_MS) > 0 && (pfd.revents & POLLIN)) {
          ssize_t n = ::read(fd, buf, sizeof(buf));
          if (n > 0) {
            auto cb_local = cb.load();
            if (cb_local) cb_local(buf, (size_t)n, cb_user.load());
          }
        }
      } });
    }

    void stop_thread()
    {
      running.store(false);
      if (fd >= 0)
      {
        ::close(fd);
        fd = -1;
      }
      if (reader.joinable())
        reader.join();
    }

    void close()
    {
      stop_thread();
    }

    lumyn_error_t set_threading(bool enable)
    {
      if (enable == use_threading)
        return LUMYN_OK;
      use_threading = enable;
      if (use_threading)
        start_thread();
      else
        stop_thread();
      return LUMYN_OK;
    }

    lumyn_error_t update(int timeout_ms)
    {
      if (use_threading || fd < 0)
        return LUMYN_OK;
      pollfd pfd{fd, POLL_EVENTS, 0};
      if (::poll(&pfd, 1, timeout_ms) > 0 && (pfd.revents & POLLIN))
      {
        uint8_t buf[512];
        ssize_t n = ::read(fd, buf, sizeof(buf));
        if (n > 0)
        {
          auto cb_local = cb.load();
          if (cb_local)
            cb_local(buf, (size_t)n, cb_user.load());
        }
      }
      return LUMYN_OK;
    }

    lumyn_error_t update() { return update(0); }
  };

  static void posix_write(void *user, const uint8_t *data, size_t len)
  {
    if (!user || (!data && len))
      return;
    auto *port = static_cast<PosixSerial *>(user);
    size_t off = 0;
    while (off < len)
    {
      ssize_t n = ::write(port->fd, data + off, len - off);
      if (n > 0)
        off += (size_t)n;
      else if (n < 0 && errno == EINTR)
        continue;
      else
        break;
    }
  }

  static void posix_set_read_cb(void *user, lumyn_serial_read_cb cb, void *cb_user)
  {
    if (!user)
      return;
    auto *port = static_cast<PosixSerial *>(user);
    port->cb.store(cb);
    port->cb_user.store(cb_user);
  }

  static void posix_close(void *user)
  {
    if (user)
      delete static_cast<PosixSerial *>(user);
  }

  static bool baud_to_speed(int baud, speed_t *out_speed)
  {
    if (!out_speed)
      return false;
    switch (baud)
    {
    case 9600:
      *out_speed = B9600;
      return true;
    case 19200:
      *out_speed = B19200;
      return true;
    case 38400:
      *out_speed = B38400;
      return true;
    case 57600:
      *out_speed = B57600;
      return true;
    case 115200:
      *out_speed = B115200;
      return true;
#ifdef B230400
    case 230400:
      *out_speed = B230400;
      return true;
#endif
#ifdef B460800
    case 460800:
      *out_speed = B460800;
      return true;
#endif
#ifdef B921600
    case 921600:
      *out_speed = B921600;
      return true;
#endif
    default:
      return false;
    }
  }

  static lumyn_error_t open_posix(const char *path, int baud, lumyn_serial_io_t *out_io)
  {
    auto *port = new PosixSerial();
    // O_RDWR: open for read/write, O_NOCTTY: avoid becoming a controlling terminal,
    // O_NONBLOCK: non-blocking for poll-driven reads.
    port->fd = ::open(path, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (port->fd < 0)
    {
      delete port;
      return LUMYN_ERR_IO;
    }

    termios tio{};
    if (tcgetattr(port->fd, &tio) != 0)
    {
      port->close();
      delete port;
      return LUMYN_ERR_IO;
    }
    cfmakeraw(&tio);
    speed_t speed = 0;
    if (!baud_to_speed(baud, &speed))
    {
      port->close();
      delete port;
      return LUMYN_ERR_NOT_SUPPORTED;
    }
    cfsetispeed(&tio, speed);
    cfsetospeed(&tio, speed);
    if (tcsetattr(port->fd, TCSANOW, &tio) != 0)
    {
      port->close();
      delete port;
      return LUMYN_ERR_IO;
    }

    if (port->use_threading)
      port->start_thread();
    out_io->user = port;
    out_io->write = posix_write;
    out_io->write_bytes = posix_write;
    out_io->set_read_callback = posix_set_read_cb;
    out_io->close = posix_close;
    return LUMYN_OK;
  }

#endif // Windows/Posix

#endif // ENABLE_BUILTIN_SERIAL

} // namespace lumyn_c_sdk::serial

extern "C"
{

  static bool is_builtin_io(const lumyn_serial_io_t *io)
  {
    if (!io || !io->user)
      return false;
#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL
#if defined(_WIN32)
    return io->write == lumyn_c_sdk::serial::win_write &&
           io->set_read_callback == lumyn_c_sdk::serial::win_set_read_cb &&
           io->close == lumyn_c_sdk::serial::win_close;
#else
    return io->write == lumyn_c_sdk::serial::posix_write &&
           io->set_read_callback == lumyn_c_sdk::serial::posix_set_read_cb &&
           io->close == lumyn_c_sdk::serial::posix_close;
#endif
#else
    (void)io;
    return false;
#endif
  }

  LUMYN_SDK_API lumyn_error_t lumyn_serial_open(const lumyn_serial_io_cfg_t *cfg, lumyn_serial_io_t *out_io)
  {
#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL
    if (!cfg || !cfg->path || !out_io)
      return LUMYN_ERR_INVALID_ARGUMENT;

    int baud = cfg->baud > 0 ? cfg->baud : lumyn::internal::Constants::Serial::kDefaultBaudRate;

#if defined(_WIN32)
    return lumyn_c_sdk::serial::open_windows(cfg->path, baud, out_io);
#else
    return lumyn_c_sdk::serial::open_posix(cfg->path, baud, out_io);
#endif
#else
    (void)cfg;
    if (out_io)
      std::memset(out_io, 0, sizeof(*out_io));
    return LUMYN_ERR_NOT_SUPPORTED;
#endif
  }

  LUMYN_SDK_API void lumyn_serial_io_close(lumyn_serial_io_t *io)
  {
    if (io && io->close)
      io->close(io->user);
    if (io)
    {
      io->user = nullptr;
      io->write = nullptr;
      io->write_bytes = nullptr;
      io->set_read_callback = nullptr;
      io->close = nullptr;
    }
  }

#ifdef LUMYN_HAS_THREADS
  LUMYN_SDK_API lumyn_error_t lumyn_serial_set_threaded(lumyn_serial_io_t *io, bool enable)
  {
#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL
    if (!is_builtin_io(io))
      return LUMYN_ERR_INVALID_ARGUMENT;
#if defined(_WIN32)
    return static_cast<lumyn_c_sdk::serial::WinSerial *>(io->user)->set_threading(enable);
#else
    return static_cast<lumyn_c_sdk::serial::PosixSerial *>(io->user)->set_threading(enable);
#endif
#else
    (void)io;
    (void)enable;
    return LUMYN_ERR_NOT_SUPPORTED;
#endif
  }
#endif

  LUMYN_SDK_API lumyn_error_t lumyn_serial_update(lumyn_serial_io_t *io)
  {
#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL
    if (!is_builtin_io(io))
      return LUMYN_ERR_INVALID_ARGUMENT;
#if defined(_WIN32)
    return static_cast<lumyn_c_sdk::serial::WinSerial *>(io->user)->update();
#else
    return static_cast<lumyn_c_sdk::serial::PosixSerial *>(io->user)->update();
#endif
#else
    return LUMYN_ERR_NOT_SUPPORTED;
#endif
  }

  LUMYN_SDK_API lumyn_error_t lumyn_serial_update_timeout(lumyn_serial_io_t *io, int timeout_ms)
  {
#if defined(LUMYN_SDK_ENABLE_BUILTIN_SERIAL) && LUMYN_SDK_ENABLE_BUILTIN_SERIAL
    if (!is_builtin_io(io))
      return LUMYN_ERR_INVALID_ARGUMENT;
    const int clamped = timeout_ms < 0 ? 0 : timeout_ms;
#if defined(_WIN32)
    return static_cast<lumyn_c_sdk::serial::WinSerial *>(io->user)->update(clamped);
#else
    return static_cast<lumyn_c_sdk::serial::PosixSerial *>(io->user)->update(clamped);
#endif
#else
    (void)timeout_ms;
    return LUMYN_ERR_NOT_SUPPORTED;
#endif
  }

} // extern "C"
