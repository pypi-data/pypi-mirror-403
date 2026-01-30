#include "lumyn/cpp/device/DirectLED.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

#include "lumyn/led/DirectBufferManager.h"
#include "lumyn/domain/command/Command.h"
#include "lumyn/domain/command/led/LEDCommand.h"

namespace lumyn::device
{

  DirectLED::DirectLED(cx_base_t *instance,
                       std::string_view zone_id,
                       size_t num_leds,
                       int full_refresh_interval)
      : num_leds_(num_leds),
        zone_id_(zone_id)
  {
    lumyn_direct_led_t *handle = nullptr;
    lumyn_error_t err = lumyn_DirectLEDCreate(
        instance,
        std::string(zone_id).c_str(),
        num_leds,
        full_refresh_interval,
        &handle);

    if (err == LUMYN_OK && handle)
    {
      handle_ = handle;
    }
  }

  DirectLED::DirectLED(std::function<lumyn_error_t(uint16_t, const uint8_t*, size_t, bool)> sender,
                       std::string_view zone_id,
                       size_t num_leds,
                       int full_refresh_interval)
      : num_leds_(num_leds),
        zone_id_(zone_id),
        send_direct_(std::move(sender))
  {
    if (send_direct_ && num_leds_ > 0)
    {
      buffer_manager_ = std::make_unique<lumyn::internal::DirectBufferManager>(
          zone_id_, num_leds_ * kBytesPerLed, full_refresh_interval);
      rgb_buffer_.assign(num_leds_ * kBytesPerLed, 0);
    }
  }

  DirectLED::~DirectLED()
  {
    if (handle_)
    {
      lumyn_DirectLEDDestroy(handle_);
      handle_ = nullptr;
    }
  }

  DirectLED::DirectLED(DirectLED &&other) noexcept
      : handle_(other.handle_),
        num_leds_(other.num_leds_)
  {
    other.handle_ = nullptr;
    other.num_leds_ = 0;
  }

  DirectLED &DirectLED::operator=(DirectLED &&other) noexcept
  {
    if (this != &other)
    {
      // Clean up current state
      if (handle_)
      {
        lumyn_DirectLEDDestroy(handle_);
      }

      // Move from other
      handle_ = other.handle_;
      num_leds_ = other.num_leds_;

      // Invalidate other
      other.handle_ = nullptr;
      other.num_leds_ = 0;
    }
    return *this;
  }

  bool DirectLED::Update(const lumyn_color_t *colors, size_t count)
  {
    if (!colors || count == 0)
      return false;
    if (handle_)
      return lumyn_DirectLEDUpdate(handle_, colors, count) == LUMYN_OK;
    if (!buffer_manager_ || rgb_buffer_.empty())
      return false;

    const size_t leds_to_convert = std::min(count, num_leds_);
    for (size_t i = 0; i < leds_to_convert; ++i)
    {
      const size_t offset = i * kBytesPerLed;
      rgb_buffer_[offset] = colors[i].r;
      rgb_buffer_[offset + 1] = colors[i].g;
      rgb_buffer_[offset + 2] = colors[i].b;
    }
    std::fill(rgb_buffer_.begin() + leds_to_convert * kBytesPerLed, rgb_buffer_.end(), 0);
    return UpdateRaw(rgb_buffer_.data(), rgb_buffer_.size());
  }

  bool DirectLED::Update(const std::vector<lumyn_color_t> &colors)
  {
    return Update(colors.data(), colors.size());
  }

  bool DirectLED::UpdateRaw(const uint8_t *rgb_data, size_t length)
  {
    if (!rgb_data || length == 0)
      return false;
    if (handle_)
      return lumyn_DirectLEDUpdateRaw(handle_, rgb_data, length) == LUMYN_OK;
    if (!buffer_manager_ || !send_direct_)
      return false;

    const auto cmd_bytes = buffer_manager_->update(rgb_data, length);
    if (cmd_bytes.size() < sizeof(lumyn::internal::Command::CommandHeader) +
                               sizeof(lumyn::internal::Command::LED::SetDirectBufferData))
      return false;

    lumyn::internal::Command::LED::SetDirectBufferData meta{};
    std::memcpy(&meta,
                cmd_bytes.data() + sizeof(lumyn::internal::Command::CommandHeader),
                sizeof(meta));
    const uint8_t* data = cmd_bytes.data() + sizeof(lumyn::internal::Command::CommandHeader) + sizeof(meta);
    const size_t data_len = cmd_bytes.size() - sizeof(lumyn::internal::Command::CommandHeader) - sizeof(meta);
    return send_direct_(meta.zoneId, data, data_len, meta.flags.delta != 0) == LUMYN_OK;
  }

  bool DirectLED::ForceFullUpdate(const lumyn_color_t *colors, size_t count)
  {
    if (!colors || count == 0)
      return false;
    if (handle_)
      return lumyn_DirectLEDForceFullUpdate(handle_, colors, count) == LUMYN_OK;
    if (!buffer_manager_ || rgb_buffer_.empty())
      return false;

    const size_t leds_to_convert = std::min(count, num_leds_);
    for (size_t i = 0; i < leds_to_convert; ++i)
    {
      const size_t offset = i * kBytesPerLed;
      rgb_buffer_[offset] = colors[i].r;
      rgb_buffer_[offset + 1] = colors[i].g;
      rgb_buffer_[offset + 2] = colors[i].b;
    }
    std::fill(rgb_buffer_.begin() + leds_to_convert * kBytesPerLed, rgb_buffer_.end(), 0);
    return ForceFullUpdateRaw(rgb_buffer_.data(), rgb_buffer_.size());
  }

  bool DirectLED::ForceFullUpdate(const std::vector<lumyn_color_t> &colors)
  {
    return ForceFullUpdate(colors.data(), colors.size());
  }

  bool DirectLED::ForceFullUpdateRaw(const uint8_t *rgb_data, size_t length)
  {
    if (!rgb_data || length == 0)
      return false;
    if (handle_)
      return lumyn_DirectLEDForceFullUpdateRaw(handle_, rgb_data, length) == LUMYN_OK;
    if (!buffer_manager_ || !send_direct_)
      return false;

    const auto cmd_bytes = buffer_manager_->forceFullUpdate(rgb_data, length);
    if (cmd_bytes.size() < sizeof(lumyn::internal::Command::CommandHeader) +
                               sizeof(lumyn::internal::Command::LED::SetDirectBufferData))
      return false;

    lumyn::internal::Command::LED::SetDirectBufferData meta{};
    std::memcpy(&meta,
                cmd_bytes.data() + sizeof(lumyn::internal::Command::CommandHeader),
                sizeof(meta));
    const uint8_t* data = cmd_bytes.data() + sizeof(lumyn::internal::Command::CommandHeader) + sizeof(meta);
    const size_t data_len = cmd_bytes.size() - sizeof(lumyn::internal::Command::CommandHeader) - sizeof(meta);
    return send_direct_(meta.zoneId, data, data_len, meta.flags.delta != 0) == LUMYN_OK;
  }

  void DirectLED::Reset()
  {
    if (handle_)
      lumyn_DirectLEDReset(handle_);
    if (buffer_manager_)
      buffer_manager_->reset();
  }

  void DirectLED::SetFullRefreshInterval(int interval)
  {
    if (handle_)
      lumyn_DirectLEDSetRefreshInterval(handle_, interval);
    if (buffer_manager_)
      buffer_manager_->setFullRefreshInterval(interval);
  }

  size_t DirectLED::GetLength() const
  {
    if (handle_)
      return lumyn_DirectLEDGetLength(handle_);
    return num_leds_;
  }

  size_t DirectLED::GetExpectedBufferLength() const
  {
    return GetLength() * kBytesPerLed;
  }

  bool DirectLED::IsInitialized() const
  {
    if (handle_)
      return lumyn_DirectLEDIsInitialized(handle_);
    return buffer_manager_ != nullptr;
  }

  const char *DirectLED::GetZoneId() const
  {
    if (handle_)
      return lumyn_DirectLEDGetZoneId(handle_);
    return zone_id_.empty() ? nullptr : zone_id_.c_str();
  }

} // namespace lumyn::device
