#pragma once

#include "lumyn/cpp/export.hpp"
#include "lumyn/cpp/device/BaseLumynDevice.hpp"
#include "lumyn/cpp/device/BaseLEDDevice.hpp"
#include "lumyn/cpp/device/DirectLED.hpp"
#include "lumyn/cpp/device/builder/AnimationBuilder.hpp"
#include "lumyn/cpp/device/builder/ImageSequenceBuilder.hpp"
#include "lumyn/cpp/device/builder/MatrixTextBuilder.hpp"
#include "lumyn/c/lumyn_sdk.h"
#include "lumyn/c/serial_io.h"
#include "lumyn/types/events.h"
#include "lumyn/types/status.h"
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#include <mutex>
#include <thread>
#include <atomic>

namespace lumyn::device
{

  /**
   * @brief Base class for ConnectorX device variants
   *
   * Provides shared implementation for ConnectorX and ConnectorXAnimate.
   * Contains all the common logic for connection, events, configuration, and LED control.
   * Derived classes only need to:
   *   - Implement constructor to call InitializeLEDCommanders
   *   - Override GetBasePtr() to return this
   *   - Override OnEvent() (typically empty)
   *   - Add device-specific functionality (e.g., modules for ConnectorX)
   */
  class LUMYN_SDK_CPP_API BaseConnectorXVariant
      : public internal::BaseLEDDevice,
        public internal::BaseLumynDevice
  {
  public:
    BaseConnectorXVariant();
    ~BaseConnectorXVariant() override;

    BaseConnectorXVariant(const BaseConnectorXVariant &) = delete;
    BaseConnectorXVariant &operator=(const BaseConnectorXVariant &) = delete;
    BaseConnectorXVariant(BaseConnectorXVariant &&) = delete;
    BaseConnectorXVariant &operator=(BaseConnectorXVariant &&) = delete;

    // Connection / status
    ::lumyn_error_t Connect(const ::lumyn_serial_io_t &io);
    ::lumyn_error_t Connect(const std::string &port, std::optional<int> baud = std::nullopt);
    void Disconnect();
    bool IsConnected() const;
    ::lumyn::ConnectionStatus GetCurrentStatus() const;
    ::lumyn::Status GetDeviceHealth() const;

    // Events
    ::lumyn_error_t AddEventHandler(std::function<void(const ::lumyn::Event &)> handler);
    ::lumyn_error_t GetLatestEvent(::lumyn_event_t &out_event);
    std::optional<::lumyn::Event> GetLatestEvent();
    std::vector<::lumyn::Event> GetEvents();
    void SetAutoPollEvents(bool enabled);
    void PollEvents();

    // Configuration
    ::lumyn_error_t RequestConfig(std::string &out_json, uint32_t timeout_ms = 1000);
    bool ApplyConfigurationJson(const std::string &json);
    bool LoadConfigurationFromFile(const std::string &path);

    // LED control
    void SetColor(std::string_view zone_id, ::lumyn_color_t color) const;
    void SetGroupColor(std::string_view group_id, ::lumyn_color_t color) const;
    AnimationBuilder SetAnimation(::lumyn::led::Animation animation);
    ImageSequenceBuilder SetImageSequence(std::string_view sequence_id);
    MatrixTextBuilder SetText(std::string_view text);

    // Animation sequences (pre-defined in config JSON)
    void SetAnimationSequence(std::string_view zone_id, std::string_view sequence_id);
    void SetGroupAnimationSequence(std::string_view group_id, std::string_view sequence_id);

    // Direct LED buffer helpers
    ::lumyn_error_t SendDirectBuffer(std::string_view zone_id, const uint8_t *data, size_t length, bool delta);
    ::lumyn_error_t SendDirectBuffer(uint16_t zone_hash, const uint8_t *data, size_t length, bool delta);
    ::lumyn::device::DirectLED CreateDirectLED(std::string_view zone_id, size_t num_leds, int full_refresh_interval_ms = 100);

    // Send pre-built raw command bytes (e.g., from DirectBufferManager)
    void SendRawCommand(const uint8_t *data, size_t length);

    // BaseLEDDevice override - handles LED command dispatch
    void SendLEDCommand(const void *data, uint32_t length) override;

    // Get cx_base_t* for C API calls (returns nullptr for pure C++ usage)
    cx_base_t *GetCBasePtr() { return c_base_ptr_; }
    const cx_base_t *GetCBasePtr() const { return c_base_ptr_; }

    // Set cx_base_t* (called by C API layer)
    void SetCBasePtr(cx_base_t *base_ptr) { c_base_ptr_ = base_ptr; }
    void SetAlertsEnabled(bool enabled) { alerts_enabled_ = enabled; }

  protected:
    // Start/stop event polling thread (called by Connect/Disconnect)
    void StartEventPolling();
    void StopEventPolling();

    // Hook for derived classes to handle disconnect cleanup (e.g., module polling)
    virtual void OnDisconnect() {}

    cx_base_t *c_base_ptr_{nullptr}; // Pointer to C struct (set by C API layer, nullptr for pure C++ usage)
    bool auto_poll_events_{true};
    std::atomic<bool> poll_events_{false};
    std::thread event_thread_;
    bool alerts_enabled_{true};
  };

} // namespace lumyn::device
