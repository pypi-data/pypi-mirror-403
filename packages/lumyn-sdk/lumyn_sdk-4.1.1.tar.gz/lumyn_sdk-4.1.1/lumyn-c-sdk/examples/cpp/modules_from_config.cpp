#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file modules_from_config.cpp
 * @brief Module discovery + typed helpers example (C++)
 *
 * Reads the device config, discovers modules, registers typed helpers,
 * and prints module data as it arrives.
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/modules/AnalogInputModule.hpp>
#include <lumyn/cpp/modules/DigitalInputModule.hpp>
#include <lumyn/cpp/modules/VL53L1XModule.hpp>
#include <lumyn/c/lumyn_config.h>

#include <chrono>
#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <vector>

static const char *ConnectionTypeToString(lumyn_module_connection_type_t type)
{
  switch (type)
  {
  case LUMYN_MODULE_CONNECTION_I2C:
    return "I2C";
  case LUMYN_MODULE_CONNECTION_SPI:
    return "SPI";
  case LUMYN_MODULE_CONNECTION_UART:
    return "UART";
  case LUMYN_MODULE_CONNECTION_DIO:
    return "DIO";
  case LUMYN_MODULE_CONNECTION_AIO:
    return "AIO";
  default:
    return "Unknown";
  }
}

int main(int argc, char *argv[])
{
  std::cout.setf(std::ios::unitbuf);
  std::string port;
  for (int i = 1; i < argc; ++i)
  {
    if (std::string(argv[i]) == "--port" && i + 1 < argc)
    {
      port = argv[++i];
    }
    else if (std::string(argv[i]) == "--help" || std::string(argv[i]) == "-h")
    {
      std::cout << "Usage: " << argv[0] << " --port <serial port>\n";
      return 0;
    }
  }

  if (port.empty())
  {
    std::cerr << "Error: --port is required\n";
    return 1;
  }

  lumyn::device::ConnectorX cx;
  bool connected = false;
  std::cout << "Connecting to " << port << "...\n";
  auto err = cx.Connect(port);
  if (err != LUMYN_OK)
  {
    std::cerr << "Failed to connect: " << Lumyn_ErrorString(err) << "\n";
    return 1;
  }
  connected = true;

  std::cout << "Connected!\n";

  std::string config_json;
  err = cx.RequestConfig(config_json, 5000);
  if (err != LUMYN_OK || config_json.empty())
  {
    std::cerr << "Failed to read device config: " << Lumyn_ErrorString(err) << "\n";
    if (connected)
      cx.Disconnect();
    return 1;
  }

  lumyn_config_t *config = nullptr;
  err = lumyn_ParseConfig(config_json.data(), config_json.size(), &config);
  if (err != LUMYN_OK || !config)
  {
    std::cerr << "Failed to parse device config: " << Lumyn_ErrorString(err) << "\n";
    if (connected)
      cx.Disconnect();
    return 1;
  }

  const int module_count = lumyn_ConfigGetModuleCount(config);
  if (module_count == 0)
  {
    std::cout << "No modules found in device config.\n";
    lumyn_FreeConfig(config);
    if (connected)
      cx.Disconnect();
    return 0;
  }

  std::cout << "Modules in config: " << module_count << "\n";
  int poll_interval_ms = 10;

  std::vector<std::unique_ptr<lumyn::modules::DigitalInputModule>> digital_modules;
  std::vector<std::unique_ptr<lumyn::modules::AnalogInputModule>> analog_modules;
  std::vector<std::unique_ptr<lumyn::modules::VL53L1XModule>> tof_modules;

  for (int i = 0; i < module_count; ++i)
  {
    const lumyn_module_t *module = lumyn_ConfigGetModule(config, i);
    const char *id = lumyn_ModuleGetId(module);
    const char *type = lumyn_ModuleGetType(module);
    const uint16_t poll_ms = lumyn_ModuleGetPollingRateMs(module);
    const auto conn = lumyn_ModuleGetConnectionType(module);

    std::cout << "  - id=" << (id ? id : "(null)")
              << " type=" << (type ? type : "(null)")
              << " pollingRateMs=" << poll_ms
              << " connection=" << ConnectionTypeToString(conn) << "\n";

    (void)poll_ms;

    if (!id || !type)
      continue;

    if (std::string(type) == "DigitalInput")
    {
      auto mod = std::make_unique<lumyn::modules::DigitalInputModule>(cx, id);
      std::string id_copy = id;
      mod->OnUpdate([id_copy](const lumyn::modules::DigitalInputPayload &payload)
                    { std::cout << "[" << id_copy << "] DIO state: " << (payload.state ? "HIGH" : "LOW") << "\n"; });
      mod->Start();
      digital_modules.push_back(std::move(mod));
    }
    else if (std::string(type) == "AnalogInput")
    {
      auto mod = std::make_unique<lumyn::modules::AnalogInputModule>(cx, id);
      std::string id_copy = id;
      mod->OnUpdate([id_copy](const lumyn::modules::AnalogInputPayload &payload)
                    { std::cout << "[" << id_copy << "] Analog raw=" << payload.raw_value << " scaled=" << payload.scaled_value << "\n"; });
      mod->Start();
      analog_modules.push_back(std::move(mod));
    }
    else if (std::string(type) == "VL53L1X")
    {
      auto mod = std::make_unique<lumyn::modules::VL53L1XModule>(cx, id);
      std::string id_copy = id;
      mod->OnUpdate([id_copy](const lumyn::modules::VL53L1XPayload &payload)
                    {
                      if (payload.valid)
                      {
                        std::cout << "[" << id_copy << "] Distance: " << payload.dist_mm << " mm\n";
                      }
                    });
      mod->Start();
      tof_modules.push_back(std::move(mod));
    }
    else
    {
      std::cout << "  (skipping unsupported module type)\n";
    }
  }

  lumyn_FreeConfig(config);

  cx.GetModuleDispatcher().SetPollIntervalMs(poll_interval_ms);
  std::cout << "Polling every " << poll_interval_ms << " ms. Press Ctrl+C to exit...\n";
  while (true)
  {
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
  }

  return 0;
}
