#include <lumyn/Constants.h> // Required for ILogger.h and Network.h (included via various headers)

#include "lumyn/c/lumyn_sdk.h"
#include "lumyn/c/serial_io.h"
#include "internal/ConnectorXInternal.hpp"
#include "internal/ConnectorXAnimateInternal.hpp"
#include "internal/DeviceInternalBase.hpp"

#include <lumyn/util/serial/ISerialIO.h>
#include <lumyn/cpp/device/BaseLumynDevice.hpp>
#include <lumyn/domain/command/led/LEDCommand.h>
#include <lumyn/util/hashing/IDCreator.h>
#include <lumyn/configuration/LumynConfigurationParser.h>
#include <lumyn/domain/command/Command.h>
#include <lumyn/configuration/Configuration.h>
#include <lumyn/cpp/ConfigManager.h>
#include <lumyn/led/DirectBufferManager.h>

#include <algorithm>
#include <chrono>
#include <cstring>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <vector>
#include <climits>

using namespace lumyn_c_sdk::internal;

struct lumyn_device_vtable
{
  lumyn_error_t (*register_module)(cx_base_t *inst, const char *module_id, lumyn_module_data_callback_t cb, void *user);
  lumyn_error_t (*unregister_module)(cx_base_t *inst, const char *module_id);
  lumyn_error_t (*get_latest_data)(cx_base_t *inst, const char *module_id, void *out, size_t size);
  lumyn_error_t (*set_module_polling_enabled)(cx_base_t *inst, bool enabled);
  lumyn_error_t (*poll_modules)(cx_base_t *inst);
};

namespace
{

  class VTableSerialIO final : public lumyn::internal::ISerialIO
  {
  public:
    explicit VTableSerialIO(lumyn_serial_io_t transport) : transport_(transport) {}
    ~VTableSerialIO() override
    {
      if (transport_.close)
        transport_.close(transport_.user);
    }

    void writeBytes(const uint8_t *data, size_t length) override
    {
      if (transport_.write_bytes)
        transport_.write_bytes(transport_.user, data, length);
      else if (transport_.write)
        transport_.write(transport_.user, data, length);
    }

    void setReadCallback(std::function<void(const uint8_t *, size_t)> callback) override
    {
      std::lock_guard<std::mutex> lock(cb_mutex_);
      cb_ = std::move(callback);
      if (!transport_.set_read_callback)
        return;
      transport_.set_read_callback(transport_.user, [](const uint8_t *data, size_t len, void *user)
                                   {
        auto* self = static_cast<VTableSerialIO*>(user);
        std::function<void(const uint8_t*, size_t)> cb_copy;
        { std::lock_guard<std::mutex> lock(self->cb_mutex_); cb_copy = self->cb_; }
        if (cb_copy) cb_copy(data, len); }, this);
    }

  private:
    lumyn_serial_io_t transport_{};
    std::mutex cb_mutex_;
    std::function<void(const uint8_t *, size_t)> cb_;
  };

  void fill_event_alloc(const lumyn::internal::Eventing::Event &in, lumyn_event_t *out)
  {
    std::memset(out, 0, sizeof(*out));
    out->type = static_cast<lumyn_event_type_t>(in.header.type);
    std::memcpy(&out->data, &in.header.data, sizeof(in.header.data));

    if (in.extraMsg && in.extraMsg->length > 0)
    {
      out->extra_message = static_cast<char *>(LUMYN_SDK_MALLOC(in.extraMsg->length + 1));
      std::memcpy(out->extra_message, in.extraMsg->data, in.extraMsg->length);
      out->extra_message[in.extraMsg->length] = '\0';
    }
  }

  void fill_event_view(const lumyn::internal::Eventing::Event &in, lumyn_event_t *out, std::string *storage)
  {
    std::memset(out, 0, sizeof(*out));
    out->type = static_cast<lumyn_event_type_t>(in.header.type);
    std::memcpy(&out->data, &in.header.data, sizeof(in.header.data));
    if (in.extraMsg && in.extraMsg->length > 0 && storage)
    {
      storage->assign(reinterpret_cast<const char *>(in.extraMsg->data), in.extraMsg->length);
      out->extra_message = storage->empty() ? nullptr : storage->data();
    }
  }

  void fill_event_from_cpp(const lumyn::Event &in, lumyn_event_t *out, std::string *storage)
  {
    std::memset(out, 0, sizeof(*out));
    out->type = in.getType();
    std::memcpy(&out->data, &in.getData(), sizeof(in.getData()));
    if (in.getExtraMessage() && storage)
    {
      storage->assign(in.getExtraMessage());
      out->extra_message = storage->empty() ? nullptr : storage->data();
    }
  }

  void dispatch_event(const lumyn::internal::Eventing::Event &evt, const std::vector<std::pair<lumyn_event_callback_t, void *>> &handlers)
  {
    if (handlers.empty())
      return;
    for (const auto &h : handlers)
    {
      if (!h.first)
        continue;
      lumyn_event_t c_evt;
      fill_event_alloc(evt, &c_evt);
      h.first(&c_evt, h.second);
      if (c_evt.extra_message)
      {
        lumyn_FreeString(c_evt.extra_message);
      }
    }
  }

  struct lumyn_zone_impl
  {
    std::string id;
    int led_count;
  };

  struct lumyn_channel_impl
  {
    std::string id;
    std::vector<lumyn_zone_impl> zones;
  };

  struct lumyn_module_impl
  {
    std::string id;
    std::string type;
    uint16_t polling_rate_ms;
    lumyn::internal::ModuleInfo::ModuleConnectionType connection_type;
  };

  struct lumyn_config_impl
  {
    std::vector<lumyn_channel_impl> channels;
    std::vector<lumyn_module_impl> modules;
  };

  // Forward declaration - defined later in file
  bool is_connected(cx_base_t *inst);

  /**
   * DirectLED implementation structure.
   * Wraps DirectBufferManager and maintains reference to the device instance.
   */
  struct lumyn_direct_led_impl
  {
    cx_base_t *instance;
    std::string zone_id;
    size_t num_leds;
    std::unique_ptr<lumyn::internal::DirectBufferManager> buffer_manager;
    std::vector<uint8_t> rgb_buffer; // Working buffer for color conversion
    bool initialized;

    static constexpr size_t kBytesPerLed = lumyn::internal::Constants::LED::kBytesPerLed;

    lumyn_direct_led_impl(cx_base_t *inst, const char *zid, size_t leds, int refresh_interval)
        : instance(inst), zone_id(zid), num_leds(leds), rgb_buffer(leds * kBytesPerLed, 0), initialized(false)
    {
      if (inst && inst->_internal && zid && leds > 0)
      {
        buffer_manager = std::make_unique<lumyn::internal::DirectBufferManager>(
            std::string_view(zone_id), leds * kBytesPerLed, refresh_interval);
        initialized = true;
      }
    }

    // Convert lumyn_color_t array to RGB bytes
    void ColorsToRGB(const lumyn_color_t *colors, size_t count)
    {
      size_t leds_to_convert = std::min(num_leds, count);
      for (size_t i = 0; i < leds_to_convert; ++i)
      {
        size_t offset = i * kBytesPerLed;
        rgb_buffer[offset] = colors[i].r;
        rgb_buffer[offset + 1] = colors[i].g;
        rgb_buffer[offset + 2] = colors[i].b;
      }
      // Zero out any remaining LEDs if input is shorter
      for (size_t i = leds_to_convert * kBytesPerLed; i < rgb_buffer.size(); ++i)
      {
        rgb_buffer[i] = 0;
      }
    }

    // Copy raw RGB data to internal buffer
    void CopyRGB(const uint8_t *data, size_t length)
    {
      size_t bytes_to_copy = std::min(length, rgb_buffer.size());
      std::copy_n(data, bytes_to_copy, rgb_buffer.begin());
      std::fill(rgb_buffer.begin() + bytes_to_copy, rgb_buffer.end(), 0);
    }

    // Send buffer update through the manager (handles delta compression)
    lumyn_error_t SendUpdate(bool force_full)
    {
      if (!initialized || !instance || !instance->_internal)
      {
        return LUMYN_ERR_INVALID_ARGUMENT;
      }
      if (!is_connected(instance))
      {
        return LUMYN_ERR_NOT_CONNECTED;
      }

      // Use DirectBufferManager to get command bytes (handles delta compression)
      std::vector<uint8_t> cmd_bytes;
      if (force_full)
      {
        cmd_bytes = buffer_manager->forceFullUpdate(rgb_buffer.data(), rgb_buffer.size());
      }
      else
      {
        cmd_bytes = buffer_manager->update(rgb_buffer.data(), rgb_buffer.size());
      }

      if (cmd_bytes.empty())
      {
        return LUMYN_ERR_INTERNAL;
      }

      // Send the pre-built command bytes directly to preserve delta compression.
      if (cmd_bytes.size() < sizeof(lumyn::internal::Command::CommandHeader) +
                                 sizeof(lumyn::internal::Command::LED::SetDirectBufferData))
      {
        return LUMYN_ERR_INTERNAL;
      }

      lumyn::internal::Command::CommandHeader header{};
      std::memcpy(&header, cmd_bytes.data(), sizeof(header));
      lumyn::internal::Command::LED::SetDirectBufferData meta{};
      std::memcpy(&meta,
                  cmd_bytes.data() + sizeof(header),
                  sizeof(meta));
      const uint8_t *data = cmd_bytes.data() + sizeof(header) + sizeof(meta);
      const size_t data_len = cmd_bytes.size() - sizeof(header) - sizeof(meta);

      auto *base_internal = static_cast<DeviceInternalBase *>(instance->_internal);
      if (auto *internal = dynamic_cast<ConnectorXInternal *>(base_internal))
      {
        return internal->device()->SendDirectBuffer(meta.zoneId, data, data_len, meta.flags.delta != 0);
      }
      if (auto *internal = dynamic_cast<ConnectorXAnimateInternal *>(base_internal))
      {
        return internal->device()->SendDirectBuffer(meta.zoneId, data, data_len, meta.flags.delta != 0);
      }

      return LUMYN_ERR_NOT_SUPPORTED;
    }
  };

  thread_local std::string tls_event_message;
  thread_local std::vector<std::string> tls_event_messages;

  bool is_connected(cx_base_t *inst)
  {
    if (!inst || !inst->_internal)
      return false;
    return static_cast<DeviceInternalBase *>(inst->_internal)->IsConnected();
  }

  /**
   * Helper to dispatch LED/device commands to ConnectorX or ConnectorXAnimate.
   * Both types inherit from the same base classes, so they have identical interfaces.
   * This eliminates code duplication by working through a common device accessor.
   */
  template <typename Func>
  lumyn_error_t dispatch_device_command(cx_base_t *inst, Func &&fn)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;

    if (auto *internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal)))
    {
      return fn(internal->device());
    }
    if (auto *internal = dynamic_cast<ConnectorXAnimateInternal *>(static_cast<DeviceInternalBase *>(inst->_internal)))
    {
      return fn(internal->device());
    }
    return LUMYN_ERR_NOT_SUPPORTED;
  }

  /**
   * Helper to convert C color struct to C++ animation color.
   */
  inline lumyn::internal::Command::LED::AnimationColor to_anim_color(lumyn_color_t c)
  {
    return {c.r, c.g, c.b};
  }

  /**
   * Helper to convert C matrix text flags struct to C++ flags.
   */
  inline lumyn::internal::Command::LED::MatrixTextFlags to_matrix_flags(lumyn_matrix_text_flags_t flags)
  {
    lumyn::internal::Command::LED::MatrixTextFlags result{};
    result.smoothScroll = flags.smoothScroll ? 1 : 0;
    result.showBackground = flags.showBackground ? 1 : 0;
    result.pingPong = flags.pingPong ? 1 : 0;
    result.noScroll = flags.noScroll ? 1 : 0;
    return result;
  }

  lumyn_error_t register_module_impl(cx_base_t *inst, const char *module_id, lumyn_module_data_callback_t cb, void *user)
  {
    if (!inst || !inst->_internal || !module_id || !cb)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // _internal is DeviceInternalBase*, use dynamic_cast to recover ConnectorXInternal*
    auto *internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (!internal)
      return LUMYN_ERR_NOT_SUPPORTED;
    if (!internal->RegisterModuleCallback(module_id, cb, user))
    {
      return LUMYN_ERR_INTERNAL;
    }
    return LUMYN_OK;
  }

  lumyn_error_t unregister_module_impl(cx_base_t *inst, const char *module_id)
  {
    if (!inst || !inst->_internal || !module_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // _internal is DeviceInternalBase*, use dynamic_cast to recover ConnectorXInternal*
    auto *internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (!internal)
      return LUMYN_ERR_NOT_SUPPORTED;
    bool removed = internal->UnregisterModuleCallback(module_id);
    return removed ? LUMYN_OK : LUMYN_ERR_INVALID_ARGUMENT;
  }

  lumyn_error_t get_latest_data_impl(cx_base_t *inst, const char *module_id, void *out, size_t size)
  {
    if (!inst || !inst->_internal || !module_id || !out || size == 0)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // _internal is DeviceInternalBase*, use dynamic_cast to recover ConnectorXInternal*
    auto *internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (!internal)
      return LUMYN_ERR_NOT_SUPPORTED;
    if (!internal->IsConnected())
      return LUMYN_ERR_NOT_CONNECTED;
    auto *dev = internal->device();
    std::vector<uint8_t> data;
    lumyn_error_t res = dev->GetLatestModuleData(module_id, data);
    if (res != LUMYN_OK)
      return res;
    if (data.empty())
      return LUMYN_ERR_TIMEOUT;

    if (size < data.size())
      return LUMYN_ERR_INVALID_ARGUMENT;
    std::memcpy(out, data.data(), data.size());
    return LUMYN_OK;
  }

  lumyn_error_t set_module_polling_enabled_impl(cx_base_t *inst, bool enabled)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // _internal is DeviceInternalBase*, use dynamic_cast to recover ConnectorXInternal*
    auto *internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (!internal)
      return LUMYN_ERR_NOT_SUPPORTED;
    internal->SetModulePollingEnabled(enabled);
    return LUMYN_OK;
  }

  lumyn_error_t poll_modules_impl(cx_base_t *inst)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // _internal is DeviceInternalBase*, use dynamic_cast to recover ConnectorXInternal*
    auto *internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (!internal)
      return LUMYN_ERR_NOT_SUPPORTED;
    internal->PollModules();
    return LUMYN_OK;
  }

  const lumyn_device_vtable kConnectorXVtable = {
      register_module_impl,
      unregister_module_impl,
      get_latest_data_impl,
      set_module_polling_enabled_impl,
      poll_modules_impl,
  };

  const lumyn_device_vtable kNoModuleVtable = {
      nullptr,
      nullptr,
      nullptr,
      nullptr,
      nullptr,
  };

} // namespace

// Define a stringification helper for protocol version
#define LUMYN_STRINGIFY_(x) #x
#define LUMYN_STRINGIFY(x) LUMYN_STRINGIFY_(x)
#define LUMYN_PROTOCOL_VERSION_STRING  \
  LUMYN_STRINGIFY(LUMYN_VERSION_MAJOR) \
  "." LUMYN_STRINGIFY(LUMYN_VERSION_MINOR) "." LUMYN_STRINGIFY(LUMYN_VERSION_PATCH)

extern "C"
{

  // =============================================================================
  // Version Functions
  // =============================================================================

  const char *lumyn_GetVersion(void)
  {
    return LUMYN_SDK_VERSION;
  }

  int lumyn_GetVersionMajor(void)
  {
    return LUMYN_SDK_VERSION_MAJOR;
  }

  int lumyn_GetVersionMinor(void)
  {
    return LUMYN_SDK_VERSION_MINOR;
  }

  int lumyn_GetVersionPatch(void)
  {
    return LUMYN_SDK_VERSION_PATCH;
  }

  // =============================================================================
  // Error Functions
  // =============================================================================

  const char *Lumyn_ErrorString(lumyn_error_t error)
  {
    switch (error)
    {
    case LUMYN_OK:
      return "OK";
    case LUMYN_ERR_INVALID_ARGUMENT:
      return "Invalid argument";
    case LUMYN_ERR_INVALID_HANDLE:
      return "Invalid handle";
    case LUMYN_ERR_NOT_CONNECTED:
      return "Not connected";
    case LUMYN_ERR_TIMEOUT:
      return "Timeout";
    case LUMYN_ERR_IO:
      return "I/O error";
    case LUMYN_ERR_INTERNAL:
      return "Internal error";
    case LUMYN_ERR_NOT_SUPPORTED:
      return "Not supported";
    case LUMYN_ERR_PARSE:
      return "Parse error";
    default:
      return "Unknown error";
    }
  }

  lumyn_error_t lumyn_CreateConnectorX(cx_t *inst)
  {
    if (!inst)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto *internal = new ConnectorXInternal(&inst->base);
    internal->SetDispatchFunction(dispatch_event);
    // Store as DeviceInternalBase* to handle multiple inheritance pointer adjustment
    inst->base._internal = static_cast<DeviceInternalBase *>(internal);
    inst->base._vtable = &kConnectorXVtable;
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_CreateConnectorXAlloc(cx_t **out_inst)
  {
    if (!out_inst)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto *inst = static_cast<cx_t *>(LUMYN_SDK_MALLOC(sizeof(cx_t)));
    if (!inst)
      return LUMYN_ERR_INTERNAL;
    std::memset(inst, 0, sizeof(*inst));
    const auto err = lumyn_CreateConnectorX(inst);
    if (err != LUMYN_OK)
    {
      LUMYN_SDK_FREE(inst);
      return err;
    }
    *out_inst = inst;
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_CreateConnectorXAnimate(cx_animate_t *inst)
  {
    if (!inst)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto *internal = new ConnectorXAnimateInternal(&inst->base);
    internal->SetDispatchFunction(dispatch_event);
    // Store as DeviceInternalBase* to handle multiple inheritance pointer adjustment
    inst->base._internal = static_cast<DeviceInternalBase *>(internal);
    inst->base._vtable = &kNoModuleVtable;
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_CreateConnectorXAnimateAlloc(cx_animate_t **out_inst)
  {
    if (!out_inst)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto *inst = static_cast<cx_animate_t *>(LUMYN_SDK_MALLOC(sizeof(cx_animate_t)));
    if (!inst)
      return LUMYN_ERR_INTERNAL;
    std::memset(inst, 0, sizeof(*inst));
    const auto err = lumyn_CreateConnectorXAnimate(inst);
    if (err != LUMYN_OK)
    {
      LUMYN_SDK_FREE(inst);
      return err;
    }
    *out_inst = inst;
    return LUMYN_OK;
  }

  void lumyn_DestroyConnectorX(cx_t *inst)
  {
    if (!inst || !inst->base._internal)
      return;
    // _internal stores DeviceInternalBase*, dynamic_cast to get the full object
    auto *base = static_cast<DeviceInternalBase *>(inst->base._internal);
    auto *internal = dynamic_cast<ConnectorXInternal *>(base);
    if (internal)
    {
      internal->Disconnect();
      delete internal;
    }
    else
    {
      // Fallback: just delete as DeviceInternalBase
      delete base;
    }
    inst->base._internal = nullptr;
    inst->base._vtable = nullptr;
  }

  void lumyn_DestroyConnectorXAlloc(cx_t *inst)
  {
    if (!inst)
      return;
    lumyn_DestroyConnectorX(inst);
    LUMYN_SDK_FREE(inst);
  }

  void lumyn_DestroyConnectorXAnimate(cx_animate_t *inst)
  {
    if (!inst || !inst->base._internal)
      return;
    // _internal stores DeviceInternalBase*, dynamic_cast to get the full object
    auto *base = static_cast<DeviceInternalBase *>(inst->base._internal);
    auto *internal = dynamic_cast<ConnectorXAnimateInternal *>(base);
    internal->Disconnect();
    delete internal;
    inst->base._internal = nullptr;
    inst->base._vtable = nullptr;
  }

  void lumyn_DestroyConnectorXAnimateAlloc(cx_animate_t *inst)
  {
    if (!inst)
      return;
    lumyn_DestroyConnectorXAnimate(inst);
    LUMYN_SDK_FREE(inst);
  }

  lumyn_error_t lumyn_ConnectIO_internal(cx_base_t *inst, const lumyn_serial_io_t *io)
  {
    if (!inst || !inst->_internal || !io)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // Try ConnectorXInternal first (has ConnectWithAdapter)
    auto *cx_internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (cx_internal)
    {
      lumyn_serial_io_t io_copy = *io;
      auto serial_adapter = std::make_unique<VTableSerialIO>(io_copy);
      if (!cx_internal->ConnectWithAdapter(std::move(serial_adapter)))
      {
        return LUMYN_ERR_IO;
      }
      return LUMYN_OK;
    }
    // Try ConnectorXAnimateInternal
    auto *anim_internal = dynamic_cast<ConnectorXAnimateInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (anim_internal)
    {
      lumyn_serial_io_t io_copy = *io;
      auto serial_adapter = std::make_unique<VTableSerialIO>(io_copy);
      if (!anim_internal->ConnectWithAdapter(std::move(serial_adapter)))
      {
        return LUMYN_ERR_IO;
      }
      return LUMYN_OK;
    }
    return LUMYN_ERR_INVALID_ARGUMENT;
  }

  lumyn_error_t lumyn_Connect(cx_base_t *inst, const char *port)
  {
    return lumyn_ConnectWithBaud(inst, port, 115200);
  }

  lumyn_error_t lumyn_ConnectWithBaud(cx_base_t *inst, const char *port, int baud_rate)
  {
    if (!inst || !inst->_internal || !port)
      return LUMYN_ERR_INVALID_ARGUMENT;

    lumyn_serial_io_cfg_t cfg = LUMYN_SERIAL_CFG_DEFAULT;
    cfg.path = port;
    cfg.baud = baud_rate;

    lumyn_serial_io_t io = {0};
    auto err = lumyn_serial_open(&cfg, &io);
    if (err != LUMYN_OK)
    {
      std::cerr << "[SDK] Failed to open serial port " << port << ": " << Lumyn_ErrorString(err) << std::endl;
      return err;
    }

    // Try ConnectorXInternal first
    auto *cx_internal = dynamic_cast<ConnectorXInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (cx_internal)
    {
      auto serial_adapter = std::make_unique<VTableSerialIO>(io);
      if (!cx_internal->ConnectWithAdapter(std::move(serial_adapter)))
      {
        std::cerr << "[SDK] Connection failure in ConnectorX logic." << std::endl;
        return LUMYN_ERR_IO;
      }
      return LUMYN_OK;
    }

    // Try ConnectorXAnimateInternal
    auto *anim_internal = dynamic_cast<ConnectorXAnimateInternal *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (anim_internal)
    {
      auto serial_adapter = std::make_unique<VTableSerialIO>(io);
      if (!anim_internal->ConnectWithAdapter(std::move(serial_adapter)))
      {
        std::cerr << "[SDK] Connection failure in ConnectorXAnimate logic." << std::endl;
        return LUMYN_ERR_IO;
      }
      return LUMYN_OK;
    }

    return LUMYN_ERR_INVALID_ARGUMENT;
  }

  lumyn_error_t lumyn_Disconnect(cx_base_t *inst)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_HANDLE;
    auto *internal = static_cast<DeviceInternalBase *>(inst->_internal);
    internal->Disconnect();
    internal->NotifyConnectionState(false);
    return LUMYN_OK;
  }

  bool lumyn_IsConnected(cx_base_t *inst)
  {
    return inst && inst->_internal && static_cast<DeviceInternalBase *>(inst->_internal)->IsConnected();
  }

  lumyn_connection_status_t lumyn_GetCurrentStatus(cx_base_t *inst)
  {
    if (!inst || !inst->_internal)
      return {false, false};

    auto *internal = static_cast<DeviceInternalBase *>(inst->_internal);
    bool connected = false;
    bool enabled = false;

    // Get connection status including the enabled field from the latest heartbeat
    internal->GetConnectionStatus(&connected, &enabled);

    return {connected, enabled};
  }

  lumyn_status_t lumyn_GetDeviceHealth(cx_base_t *inst)
  {
    if (!inst || !inst->_internal)
      return LUMYN_STATUS_UNKNOWN;
    lumyn_status_t health = LUMYN_STATUS_UNKNOWN;
    static_cast<DeviceInternalBase *>(inst->_internal)->GetDeviceHealth(&health);
    return health;
  }

  void lumyn_SetConnectionStateCallback(cx_base_t *inst, void (*cb)(bool, void *), void *user)
  {
    if (!inst || !inst->_internal)
      return;
    static_cast<DeviceInternalBase *>(inst->_internal)->SetConnectionStateCallback(cb, user);
  }

  void lumyn_FreeString(char *str)
  {
    if (str)
      LUMYN_SDK_FREE(str);
  }

  lumyn_error_t lumyn_RequestConfig(cx_base_t *inst, char *out, size_t *size, uint32_t timeout_ms)
  {
    if (!inst || !inst->_internal || !size)
      return LUMYN_ERR_INVALID_ARGUMENT;

    auto *base_dev = dynamic_cast<lumyn::internal::BaseLumynDevice *>(static_cast<lumyn_c_sdk::internal::DeviceInternalBase *>(inst->_internal));
    if (!base_dev)
      return LUMYN_ERR_INVALID_ARGUMENT;

    std::string cfg;
    bool ok = base_dev->RequestConfig(cfg, static_cast<int>(timeout_ms));
    if (!ok)
      return LUMYN_ERR_TIMEOUT;

    if (!out)
    {
      *size = cfg.size() + 1;
      return LUMYN_OK;
    }
    if (*size < cfg.size() + 1)
    {
      *size = cfg.size() + 1;
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    std::memcpy(out, cfg.data(), cfg.size());
    out[cfg.size()] = '\0';
    *size = cfg.size() + 1;
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_RequestConfigAlloc(cx_base_t *inst, char **out, uint32_t timeout_ms)
  {
    if (!inst || !inst->_internal || !out)
      return LUMYN_ERR_INVALID_ARGUMENT;

    auto *base_dev = dynamic_cast<lumyn::internal::BaseLumynDevice *>(static_cast<lumyn_c_sdk::internal::DeviceInternalBase *>(inst->_internal));
    if (!base_dev)
      return LUMYN_ERR_INVALID_ARGUMENT;

    std::string cfg;
    bool ok = base_dev->RequestConfig(cfg, static_cast<int>(timeout_ms));
    if (!ok)
      return LUMYN_ERR_TIMEOUT;

    *out = static_cast<char *>(LUMYN_SDK_MALLOC(cfg.size() + 1));
    if (!*out)
      return LUMYN_ERR_INTERNAL;
    std::memcpy(*out, cfg.data(), cfg.size());
    (*out)[cfg.size()] = '\0';
    return LUMYN_OK;
  }

  void lumyn_RestartDevice(cx_base_t *inst, uint32_t delay_ms)
  {
    if (!inst || !inst->_internal)
      return;
    auto *base_dev = dynamic_cast<lumyn::internal::BaseLumynDevice *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (base_dev)
    {
      base_dev->Restart(delay_ms);
    }
  }

  lumyn_error_t lumyn_AddEventHandler(cx_base_t *inst, lumyn_event_callback_t cb, void *user)
  {
    if (!inst || !inst->_internal || !cb)
      return LUMYN_ERR_INVALID_ARGUMENT;
    static_cast<DeviceInternalBase *>(inst->_internal)->AddEventHandler(cb, user);
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_GetLatestEvent(cx_base_t *inst, lumyn_event_t *evt)
  {
    if (!inst || !inst->_internal || !evt)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto *internal = static_cast<DeviceInternalBase *>(inst->_internal);
    if (!internal->IsConnected())
    {
      return LUMYN_ERR_NOT_CONNECTED;
    }

    // GetLatestEvent() returns optional<Event>, not Event
    auto opt_evt = internal->GetLatestEvent();
    if (!opt_evt)
      return LUMYN_ERR_TIMEOUT;

    fill_event_from_cpp(*opt_evt, evt, &tls_event_message);
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_GetEvents(cx_base_t *inst, lumyn_event_t *arr, int max_count, int *out_count)
  {
    if (!inst || !inst->_internal || !arr || !out_count || max_count <= 0)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto *base_dev = dynamic_cast<lumyn::internal::BaseLumynDevice *>(static_cast<DeviceInternalBase *>(inst->_internal));
    if (!base_dev)
      return LUMYN_ERR_INVALID_ARGUMENT;
    auto events = base_dev->DrainEvents();
    const int copy_count = std::min<int>(max_count, static_cast<int>(events.size()));
    tls_event_messages.clear();
    tls_event_messages.resize(copy_count);
    for (int i = 0; i < copy_count; ++i)
    {
      fill_event_view(events[i], &arr[i], &tls_event_messages[i]);
    }
    *out_count = copy_count;
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_SetColor(cx_base_t *inst, const char *zone_id, lumyn_color_t color)
  {
    if (!inst || !inst->_internal || !zone_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [zone_id, color](auto *device)
                                   {
      device->GetLEDCommander().SetColor(zone_id, to_anim_color(color));
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetGroupColor(cx_base_t *inst, const char *group_id, lumyn_color_t color)
  {
    if (!inst || !inst->_internal || !group_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [group_id, color](auto *device)
                                   {
      device->GetLEDCommander().SetGroupColor(group_id, to_anim_color(color));
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetAnimation(cx_base_t *inst, const char *zone_id, lumyn_animation_t anim, lumyn_color_t color, uint32_t delay, bool reversed, bool one_shot)
  {
    if (!inst || !inst->_internal || !zone_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [zone_id, anim, color, delay, reversed, one_shot](auto *device)
                                   {
      device->GetLEDCommander().SetAnimation(zone_id, static_cast<lumyn::led::Animation>(anim),
                                             to_anim_color(color),
                                             std::chrono::milliseconds(delay),
                                             reversed, one_shot);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetGroupAnimation(cx_base_t *inst, const char *group_id, lumyn_animation_t anim, lumyn_color_t color, uint32_t delay, bool reversed, bool one_shot)
  {
    if (!inst || !inst->_internal || !group_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [group_id, anim, color, delay, reversed, one_shot](auto *device)
                                   {
      device->GetLEDCommander().SetGroupAnimation(group_id, static_cast<lumyn::led::Animation>(anim),
                                                  to_anim_color(color),
                                                  std::chrono::milliseconds(delay),
                                                  reversed, one_shot);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetAnimationSequence(cx_base_t *inst, const char *zone_id, const char *sequence_id)
  {
    if (!inst || !inst->_internal || !zone_id || !sequence_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [zone_id, sequence_id](auto *device)
                                   {
      device->GetLEDCommander().SetAnimationSequence(zone_id, sequence_id);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetGroupAnimationSequence(cx_base_t *inst, const char *group_id, const char *sequence_id)
  {
    if (!inst || !inst->_internal || !group_id || !sequence_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [group_id, sequence_id](auto *device)
                                   {
      device->GetLEDCommander().SetGroupAnimationSequence(group_id, sequence_id);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetImageSequence(cx_base_t *inst, const char *zone_id, const char *sequence_id, lumyn_color_t color, bool set_color, bool one_shot)
  {
    if (!inst || !inst->_internal || !zone_id || !sequence_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [zone_id, sequence_id, color, set_color, one_shot](auto *device)
                                   {
      device->GetMatrixCommander().SetBitmap(zone_id, sequence_id, to_anim_color(color), set_color, one_shot);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetGroupImageSequence(cx_base_t *inst, const char *group_id, const char *sequence_id, lumyn_color_t color, bool set_color, bool one_shot)
  {
    if (!inst || !inst->_internal || !group_id || !sequence_id)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [group_id, sequence_id, color, set_color, one_shot](auto *device)
                                   {
      device->GetMatrixCommander().SetGroupBitmap(group_id, sequence_id, to_anim_color(color), set_color, one_shot);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetText(cx_base_t *inst, const char *zone_id, const char *text, lumyn_color_t color, lumyn_matrix_text_scroll_direction_t direction, uint32_t delay_ms, bool one_shot)
  {
    if (!inst || !inst->_internal || !zone_id || !text)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [zone_id, text, color, direction, delay_ms, one_shot](auto *device)
                                   {
      device->GetMatrixCommander().SetText(zone_id, text, to_anim_color(color),
                                           static_cast<lumyn::internal::Command::LED::MatrixTextScrollDirection>(direction),
                                           std::chrono::milliseconds(delay_ms), one_shot);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetGroupText(cx_base_t *inst, const char *group_id, const char *text, lumyn_color_t color, lumyn_matrix_text_scroll_direction_t direction, uint32_t delay_ms, bool one_shot)
  {
    if (!inst || !inst->_internal || !group_id || !text)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    return dispatch_device_command(inst, [group_id, text, color, direction, delay_ms, one_shot](auto *device)
                                   {
      device->GetMatrixCommander().SetGroupText(group_id, text, to_anim_color(color),
                                                static_cast<lumyn::internal::Command::LED::MatrixTextScrollDirection>(direction),
                                                std::chrono::milliseconds(delay_ms), one_shot);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetTextAdvanced(cx_base_t *inst, const char *zone_id, const char *text,
                                      lumyn_color_t color, lumyn_matrix_text_scroll_direction_t direction,
                                      uint32_t delay_ms, bool one_shot, lumyn_color_t bg_color,
                                      lumyn_matrix_text_font_t font, lumyn_matrix_text_align_t align,
                                      lumyn_matrix_text_flags_t flags, int8_t y_offset)
  {
    if (!inst || !inst->_internal || !zone_id || !text)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    auto cpp_flags = to_matrix_flags(flags);
    auto cpp_dir = static_cast<lumyn::internal::Command::LED::MatrixTextScrollDirection>(direction);
    auto cpp_font = static_cast<lumyn::internal::Command::LED::MatrixTextFont>(font);
    auto cpp_align = static_cast<lumyn::internal::Command::LED::MatrixTextAlign>(align);

    return dispatch_device_command(inst, [zone_id, text, color, bg_color, cpp_dir, cpp_font, cpp_align, cpp_flags, delay_ms, one_shot, y_offset](auto *device)
                                   {
      device->GetMatrixCommander().SetText(
          zone_id, text, to_anim_color(color), cpp_dir, std::chrono::milliseconds(delay_ms), one_shot,
          to_anim_color(bg_color), cpp_font, cpp_align, cpp_flags, y_offset);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_SetGroupTextAdvanced(cx_base_t *inst, const char *group_id, const char *text,
                                           lumyn_color_t color, lumyn_matrix_text_scroll_direction_t direction,
                                           uint32_t delay_ms, bool one_shot, lumyn_color_t bg_color,
                                           lumyn_matrix_text_font_t font, lumyn_matrix_text_align_t align,
                                           lumyn_matrix_text_flags_t flags, int8_t y_offset)
  {
    if (!inst || !inst->_internal || !group_id || !text)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;

    auto cpp_flags = to_matrix_flags(flags);
    auto cpp_dir = static_cast<lumyn::internal::Command::LED::MatrixTextScrollDirection>(direction);
    auto cpp_font = static_cast<lumyn::internal::Command::LED::MatrixTextFont>(font);
    auto cpp_align = static_cast<lumyn::internal::Command::LED::MatrixTextAlign>(align);

    return dispatch_device_command(inst, [group_id, text, color, bg_color, cpp_dir, cpp_font, cpp_align, cpp_flags, delay_ms, one_shot, y_offset](auto *device)
                                   {
      device->GetMatrixCommander().SetGroupText(
          group_id, text, to_anim_color(color), cpp_dir, std::chrono::milliseconds(delay_ms), one_shot,
          to_anim_color(bg_color), cpp_font, cpp_align, cpp_flags, y_offset);
      return LUMYN_OK; });
  }

  lumyn_error_t lumyn_CreateDirectBuffer(cx_base_t *inst, const char *zone_id, size_t buffer_length, int full_refresh_interval_ms)
  {
    if (!inst || !inst->_internal || !zone_id || buffer_length == 0)
      return LUMYN_ERR_INVALID_ARGUMENT;
    // Currently no persistent buffer manager is required; creation just validates arguments.
    (void)full_refresh_interval_ms;
    return LUMYN_OK;
  }

  lumyn_error_t lumyn_UpdateDirectBuffer(cx_base_t *inst, const char *zone_id, const uint8_t *data, size_t length, bool delta)
  {
    if (!inst || !inst->_internal || !zone_id || !data || length == 0 || length > UINT16_MAX)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!is_connected(inst))
      return LUMYN_ERR_NOT_CONNECTED;
    uint16_t zone_hash = lumyn::internal::IDCreator::createId(std::string_view(zone_id));

    return dispatch_device_command(inst, [zone_hash, data, length, delta](auto *device)
                                   { return device->SendDirectBuffer(zone_hash, data, length, delta); });
  }

  // =============================================================================
  // DirectLED API Implementation
  // =============================================================================

  lumyn_error_t lumyn_DirectLEDCreate(
      cx_base_t *inst,
      const char *zone_id,
      size_t num_leds,
      int full_refresh_interval,
      lumyn_direct_led_t **out_handle)
  {
    if (!inst || !inst->_internal || !zone_id || num_leds == 0 || !out_handle)
    {
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    auto *impl = new (std::nothrow) lumyn_direct_led_impl(inst, zone_id, num_leds, full_refresh_interval);
    if (!impl)
    {
      return LUMYN_ERR_INTERNAL;
    }

    if (!impl->initialized)
    {
      delete impl;
      return LUMYN_ERR_INTERNAL;
    }

    *out_handle = reinterpret_cast<lumyn_direct_led_t *>(impl);
    return LUMYN_OK;
  }

  void lumyn_DirectLEDDestroy(lumyn_direct_led_t *handle)
  {
    if (!handle)
      return;
    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    delete impl;
  }

  lumyn_error_t lumyn_DirectLEDUpdate(
      lumyn_direct_led_t *handle,
      const lumyn_color_t *colors,
      size_t count)
  {
    if (!handle || !colors || count == 0)
    {
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    impl->ColorsToRGB(colors, count);
    return impl->SendUpdate(false);
  }

  lumyn_error_t lumyn_DirectLEDUpdateRaw(
      lumyn_direct_led_t *handle,
      const uint8_t *rgb_data,
      size_t length)
  {
    if (!handle || !rgb_data || length == 0)
    {
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    impl->CopyRGB(rgb_data, length);
    return impl->SendUpdate(false);
  }

  lumyn_error_t lumyn_DirectLEDForceFullUpdate(
      lumyn_direct_led_t *handle,
      const lumyn_color_t *colors,
      size_t count)
  {
    if (!handle || !colors || count == 0)
    {
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    impl->ColorsToRGB(colors, count);
    return impl->SendUpdate(true);
  }

  lumyn_error_t lumyn_DirectLEDForceFullUpdateRaw(
      lumyn_direct_led_t *handle,
      const uint8_t *rgb_data,
      size_t length)
  {
    if (!handle || !rgb_data || length == 0)
    {
      return LUMYN_ERR_INVALID_ARGUMENT;
    }

    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    impl->CopyRGB(rgb_data, length);
    return impl->SendUpdate(true);
  }

  void lumyn_DirectLEDReset(lumyn_direct_led_t *handle)
  {
    if (!handle)
      return;
    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    if (impl->buffer_manager)
    {
      impl->buffer_manager->reset();
    }
  }

  void lumyn_DirectLEDSetRefreshInterval(lumyn_direct_led_t *handle, int interval)
  {
    if (!handle)
      return;
    auto *impl = reinterpret_cast<lumyn_direct_led_impl *>(handle);
    if (impl->buffer_manager)
    {
      impl->buffer_manager->setFullRefreshInterval(interval);
    }
  }

  size_t lumyn_DirectLEDGetLength(const lumyn_direct_led_t *handle)
  {
    if (!handle)
      return 0;
    const auto *impl = reinterpret_cast<const lumyn_direct_led_impl *>(handle);
    return impl->num_leds;
  }

  const char *lumyn_DirectLEDGetZoneId(const lumyn_direct_led_t *handle)
  {
    if (!handle)
      return nullptr;
    const auto *impl = reinterpret_cast<const lumyn_direct_led_impl *>(handle);
    return impl->zone_id.c_str();
  }

  bool lumyn_DirectLEDIsInitialized(const lumyn_direct_led_t *handle)
  {
    if (!handle)
      return false;
    const auto *impl = reinterpret_cast<const lumyn_direct_led_impl *>(handle);
    return impl->initialized;
  }

  // =============================================================================
  // Module API Implementation
  // =============================================================================

  lumyn_error_t lumyn_RegisterModule(cx_base_t *inst, const char *module_id, lumyn_module_data_callback_t cb, void *user)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!inst->_vtable || !inst->_vtable->register_module)
      return LUMYN_ERR_NOT_SUPPORTED;
    return inst->_vtable->register_module(inst, module_id, cb, user);
  }

  lumyn_error_t lumyn_UnregisterModule(cx_base_t *inst, const char *module_id)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!inst->_vtable || !inst->_vtable->unregister_module)
      return LUMYN_ERR_NOT_SUPPORTED;
    return inst->_vtable->unregister_module(inst, module_id);
  }

  lumyn_error_t lumyn_GetLatestData(cx_base_t *inst, const char *module_id, void *out, size_t size)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!inst->_vtable || !inst->_vtable->get_latest_data)
      return LUMYN_ERR_NOT_SUPPORTED;
    return inst->_vtable->get_latest_data(inst, module_id, out, size);
  }

  lumyn_error_t lumyn_SetModulePollingEnabled(cx_base_t *inst, bool enabled)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!inst->_vtable || !inst->_vtable->set_module_polling_enabled)
      return LUMYN_ERR_NOT_SUPPORTED;
    return inst->_vtable->set_module_polling_enabled(inst, enabled);
  }

  lumyn_error_t lumyn_PollModules(cx_base_t *inst)
  {
    if (!inst || !inst->_internal)
      return LUMYN_ERR_INVALID_ARGUMENT;
    if (!inst->_vtable || !inst->_vtable->poll_modules)
      return LUMYN_ERR_NOT_SUPPORTED;
    return inst->_vtable->poll_modules(inst);
  }

  lumyn_error_t lumyn_ParseConfig(
      const char *json,
      size_t json_len,
      lumyn_config_t **out_config)
  {
    if (!json || !out_config || json_len == 0)
      return LUMYN_ERR_INVALID_ARGUMENT;
#if LUMYN_HAS_JSON_PARSER
    // Parse JSON string
    std::string json_str(json, json_len);
    auto parsed = lumyn::config::ParseConfig(json_str);
    if (!parsed)
      return LUMYN_ERR_PARSE;

    // Allocate and populate config structure
    auto *config = static_cast<lumyn_config_t *>(LUMYN_SDK_MALLOC(sizeof(lumyn_config_impl)));
    if (!config)
      return LUMYN_ERR_INTERNAL;

    try
    {
      auto *config_impl = new (config) lumyn_config_impl();

      // Extract channels from parsed configuration
      if (parsed->channels)
      {
        for (const auto &ch : *parsed->channels)
        {
          lumyn_channel_impl channel;
          channel.id = ch.id;

          // Extract zones from channel
          for (const auto &z : ch.zones)
          {
            lumyn_zone_impl zone;
            zone.id = z.id;
            // Calculate LED count based on zone type
            if (z.type == lumyn::internal::Configuration::ZoneType::Strip)
            {
              zone.led_count = z.strip.length;
            }
            else
            {
              // Matrix type
              zone.led_count = z.matrix.rows * z.matrix.cols;
            }
            channel.zones.push_back(zone);
          }

          config_impl->channels.push_back(channel);
        }
      }

      if (parsed->sensors)
      {
        for (const auto &mod : *parsed->sensors)
        {
          lumyn_module_impl module;
          module.id = mod.id;
          module.type = mod.type;
          module.polling_rate_ms = mod.pollingRateMs;
          module.connection_type = mod.connectionType;
          config_impl->modules.push_back(std::move(module));
        }
      }

      *out_config = config;
      return LUMYN_OK;
    }
    catch (...)
    {
      LUMYN_SDK_FREE(config);
      return LUMYN_ERR_INTERNAL;
    }
#else
    (void)json;
    (void)json_len;
    (void)out_config;
    return LUMYN_ERR_NOT_SUPPORTED;
#endif
  }

  void lumyn_FreeConfig(lumyn_config_t *config)
  {
    if (!config)
      return;
    auto *config_impl = reinterpret_cast<lumyn_config_impl *>(config);
    config_impl->~lumyn_config_impl();
    LUMYN_SDK_FREE(config);
  }

  int lumyn_ConfigGetChannelCount(const lumyn_config_t *config)
  {
    if (!config)
      return 0;
    const auto *config_impl = reinterpret_cast<const lumyn_config_impl *>(config);
    return static_cast<int>(config_impl->channels.size());
  }

  const lumyn_channel_t *lumyn_ConfigGetChannel(
      const lumyn_config_t *config,
      int index)
  {
    if (!config || index < 0)
      return nullptr;
    const auto *config_impl = reinterpret_cast<const lumyn_config_impl *>(config);
    if (index >= static_cast<int>(config_impl->channels.size()))
      return nullptr;
    return reinterpret_cast<const lumyn_channel_t *>(&config_impl->channels[index]);
  }

  const char *lumyn_ChannelGetId(const lumyn_channel_t *channel)
  {
    if (!channel)
      return nullptr;
    const auto *ch = reinterpret_cast<const lumyn_channel_impl *>(channel);
    return ch->id.c_str();
  }

  int lumyn_ConfigGetModuleCount(const lumyn_config_t *config)
  {
    if (!config)
      return 0;
    const auto *config_impl = reinterpret_cast<const lumyn_config_impl *>(config);
    return static_cast<int>(config_impl->modules.size());
  }

  const lumyn_module_t *lumyn_ConfigGetModule(
      const lumyn_config_t *config,
      int index)
  {
    if (!config || index < 0)
      return nullptr;
    const auto *config_impl = reinterpret_cast<const lumyn_config_impl *>(config);
    if (index >= static_cast<int>(config_impl->modules.size()))
      return nullptr;
    return reinterpret_cast<const lumyn_module_t *>(&config_impl->modules[index]);
  }

  const char *lumyn_ModuleGetId(const lumyn_module_t *module)
  {
    if (!module)
      return nullptr;
    const auto *mod = reinterpret_cast<const lumyn_module_impl *>(module);
    return mod->id.c_str();
  }

  const char *lumyn_ModuleGetType(const lumyn_module_t *module)
  {
    if (!module)
      return nullptr;
    const auto *mod = reinterpret_cast<const lumyn_module_impl *>(module);
    return mod->type.c_str();
  }

  uint16_t lumyn_ModuleGetPollingRateMs(const lumyn_module_t *module)
  {
    if (!module)
      return 0;
    const auto *mod = reinterpret_cast<const lumyn_module_impl *>(module);
    return mod->polling_rate_ms;
  }

  lumyn_module_connection_type_t lumyn_ModuleGetConnectionType(const lumyn_module_t *module)
  {
    if (!module)
      return LUMYN_MODULE_CONNECTION_I2C;
    const auto *mod = reinterpret_cast<const lumyn_module_impl *>(module);
    return mod->connection_type;
  }

  int lumyn_ChannelGetZoneCount(const lumyn_channel_t *channel)
  {
    if (!channel)
      return 0;
    const auto *ch = reinterpret_cast<const lumyn_channel_impl *>(channel);
    return static_cast<int>(ch->zones.size());
  }

  const lumyn_zone_t *lumyn_ChannelGetZone(
      const lumyn_channel_t *channel,
      int index)
  {
    if (!channel || index < 0)
      return nullptr;
    const auto *ch = reinterpret_cast<const lumyn_channel_impl *>(channel);
    if (index >= static_cast<int>(ch->zones.size()))
      return nullptr;
    return reinterpret_cast<const lumyn_zone_t *>(&ch->zones[index]);
  }

  const char *lumyn_ZoneGetId(const lumyn_zone_t *zone)
  {
    if (!zone)
      return nullptr;
    const auto *z = reinterpret_cast<const lumyn_zone_impl *>(zone);
    return z->id.c_str();
  }

  int lumyn_ZoneGetLedCount(const lumyn_zone_t *zone)
  {
    if (!zone)
      return 0;
    const auto *z = reinterpret_cast<const lumyn_zone_impl *>(zone);
    return z->led_count;
  }

  lumyn_error_t lumyn_ApplyConfig(
      cx_base_t *inst,
      const char *json,
      size_t json_len)
  {
    if (!inst || !inst->_internal || !json || json_len == 0)
      return LUMYN_ERR_INVALID_ARGUMENT;

    auto *internal = static_cast<DeviceInternalBase *>(inst->_internal);
    if (!internal->IsConnected())
      return LUMYN_ERR_NOT_CONNECTED;

    // Send configuration to device via internal method
    internal->SendConfigurationInternal(reinterpret_cast<const uint8_t *>(json), static_cast<uint32_t>(json_len));

    return LUMYN_OK;
  }

} // extern "C"
