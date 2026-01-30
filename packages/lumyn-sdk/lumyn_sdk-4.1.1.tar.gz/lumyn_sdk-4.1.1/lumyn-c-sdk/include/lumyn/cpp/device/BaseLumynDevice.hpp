#pragma once

#include <lumyn/cpp/export.hpp>
#include <lumyn/cpp/device/ILumynDevice.hpp>
#include <optional>
#include <string>
#include <memory>
#include <vector>
#include <utility>

// Forward declarations
namespace lumyn::internal
{
  namespace Transmission
  {
    class Transmission;
  }
  namespace Eventing
  {
    struct Event;
    enum class Status : int8_t;
    struct HeartBeatInfo;
  }
  namespace Response
  {
    struct ResponseHandshakeInfo;
    struct Response;
  }
  namespace Request
  {
    struct Request;
  }
  namespace Command
  {
    struct CommandHeader;
  }
  class ISerialIO;
}

namespace lumyn::managers
{
  class ConfigManager;
  class EventManager;
}

namespace lumyn::internal
{
  class ILumynTransmissionHandler;

  /**
   * @brief Base implementation of ILumynDevice that owns configuration and event managers
   *
   * This is the main base class for all Lumyn devices.
   * Provides connection management, event handling, transmission handling,
   * and access to ConfigManager and EventManager instances.
   *
   * Per notes.txt: BaseLumynDevice : ILumynDevice
   * - connect, disconnect, restart, configmanager(self.basePtr), eventmanager(self.basePtr)
   */
  class LUMYN_SDK_CPP_API BaseLumynDevice : public ILumynDevice
  {
  public:
    BaseLumynDevice();
    virtual ~BaseLumynDevice();

    // ILumynDevice implementation
    bool Connect(ISerialIO *serial) override;
    void Disconnect(void) override;
    bool IsConnected(void) const override;
    void Restart(uint32_t delay_ms = 0) override;
    void *GetBasePtr() override = 0;
    const void *GetBasePtr() const override = 0;

    // Additional methods (not in ILumynDevice but used by subclasses)
    Eventing::Status GetCurrentStatus(void);
    const Eventing::Event *GetLatestEvent(void) const;

    /**
     * @brief Request full configuration from device
     * @param outConfigJson Output string to store the JSON configuration
     * @param timeoutMs Timeout in milliseconds
     * @return true if configuration was retrieved successfully
     */
    bool RequestConfig(std::string &outConfigJson, int timeoutMs = 5000) override;

    // Transmission/Event handling (Internal)
    void HandleEvent(const Eventing::Event &);

    // Drain buffered events collected from the transport
    std::vector<internal::Eventing::Event> DrainEvents();

  protected:
    bool Initialize(void) override;

    lumyn::managers::ConfigManager &GetConfigManager();
    lumyn::managers::EventManager &GetEventManager();

    void SendConfiguration(const uint8_t *data, uint32_t length);

    const Response::ResponseHandshakeInfo *GetLatestHandshake(void) const override;

    // Protected wrappers for internal members to avoid exposing types in header
    std::optional<internal::Response::Response> SendRequestInternal(internal::Request::Request &request, int timeoutMs);
    void SendCommandInternal(const internal::Command::CommandHeader &header, const void *data, size_t length);
    bool TryPopModuleDataRawInternal(uint16_t moduleId, std::vector<std::vector<uint8_t>> &out);

  public:
    // Public wrappers for module data access (moved from BaseConnectorXVariant)
    /**
     * @brief Get latest data from a module by module ID hash
     * @param moduleId The module ID hash (uint16_t)
     * @param out Vector to store the module data payloads
     * @return true if data was retrieved successfully
     */
    bool GetModuleDataByHash(uint16_t moduleId, std::vector<std::vector<uint8_t>> &out);

    /**
     * @brief Get latest data from a module by module ID string
     * @param moduleId The module ID string (e.g., "sensor1")
     * @param out Vector to store the module data payloads
     * @return true if data was retrieved successfully
     * @note This method internally converts the module ID string to a hash
     */
    bool GetModuleDataByName(std::string_view moduleId, std::vector<std::vector<uint8_t>> &out);

  protected:
    /**
     * @brief Send a request and wait for a response
     * @param request The request to send
     * @param timeoutMs Timeout in milliseconds
     * @return Optional response (empty if timeout or error)
     */
    std::optional<Response::Response> SendRequest(Request::Request &request, int timeoutMs = 10000);

    /**
     * @brief Send a command
     * @param header The command header
     * @param payload Optional payload
     * @param payloadLen Length of the payload
     */
    void SendCommand(const Command::CommandHeader &header, const void *payload, size_t payloadLen);

    /**
     * @brief Send raw pre-built command bytes directly
     * @param data Pointer to the raw command bytes (header + payload already combined)
     * @param length Length of the data
     * @note Use this when you have pre-built command bytes (e.g., from DirectBufferManager)
     */
    void SendRawCommand(const uint8_t *data, size_t length);

  private:
    struct Impl;
    std::unique_ptr<Impl> _impl;

    bool Handshake();

    // Virtual hook for derived classes
    virtual void OnEvent(const Eventing::Event &) = 0;

    // Manager instances
    std::unique_ptr<lumyn::managers::ConfigManager> config_manager_;
    std::unique_ptr<lumyn::managers::EventManager> event_manager_;
  };
}
