#pragma once

#include <lumyn/cpp/export.hpp>
#include <memory>
#include <optional>
#include <string>

// Forward declarations
namespace lumyn::internal
{
  namespace Response
  {
    struct ResponseHandshakeInfo;
  }
  class ISerialIO;
}

namespace lumyn::internal
{
  /**
   * @brief Base interface for all Lumyn devices
   *
   * Provides core device operations: Connect, Disconnect, Restart, and access to base pointer.
   */
  class LUMYN_SDK_CPP_API ILumynDevice
  {
  public:
    virtual ~ILumynDevice() = default;

    /**
     * @brief Connect to the device using the specified serial interface
     * @param serial Pointer to serial I/O interface
     * @return true if connection was successful
     */
    virtual bool Connect(ISerialIO *serial) = 0;

    /**
     * @brief Disconnect from the device
     */
    virtual void Disconnect(void) = 0;

    /**
     * @brief Check if device is currently connected
     * @return true if connected
     */
    virtual bool IsConnected(void) const = 0;

    /**
     * @brief Restart the device
     * @param delay_ms Delay in milliseconds before restart
     */
    virtual void Restart(uint32_t delay_ms = 0) = 0;

    /**
     * @brief Get pointer to the base device structure
     * @return Pointer to base device (implementation specific)
     */
    virtual void *GetBasePtr() = 0;
    virtual const void *GetBasePtr() const = 0;

    /**
     * @brief Get the latest handshake information received from the device
     * @return Pointer to handshake info, or nullptr if none received
     */
    virtual const Response::ResponseHandshakeInfo *GetLatestHandshake(void) const = 0;

  protected:
    /**
     * @brief Initialize the device after connection
     * @return true if initialization was successful
     */
    virtual bool Initialize(void) = 0;

    /**
     * @brief Request full configuration from device
     * @param outConfigJson Output string to store the JSON configuration
     * @param timeoutMs Timeout in milliseconds
     * @return true if configuration was retrieved successfully
     */
    virtual bool RequestConfig(std::string &outConfigJson, int timeoutMs = 5000) = 0;
  };
}
