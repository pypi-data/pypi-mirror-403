#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file config_apply_json.cpp
 * @brief Load JSON configuration from disk and push it to the device using the C++ API.
 *
 * Mirrors the workflow in the Python and WPILib vendordeps: load or build a JSON payload,
 * then call `ConnectorX::ApplyConfigurationJson` to send it across the existing C ABI.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <thread>
#include <vector>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#else
#include <glob.h>
#include <unistd.h>
#endif

using lumyn::device::ConnectorX;

static void print_usage(const char *prog)
{
    std::cout << "Usage: " << prog << " --config <file> [--apply <port>] [--save <file>]\n";
    std::cout << "  --config <file>  Path to JSON configuration (required)\n";
    std::cout << "  --apply <port>   Serial port to send the config to (e.g., COM3, /dev/ttyACM0)\n";
    std::cout << "  --save <file>    Copy the JSON payload to disk before applying\n";
}

static bool read_file(const std::string &path, std::string &out)
{
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }
    out.assign(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
    return true;
}

static void sleep_seconds(unsigned seconds)
{
#ifdef _WIN32
    Sleep(seconds * 1000);
#else
    sleep(seconds);
#endif
}

static bool try_connect(ConnectorX &cx, const std::string &port, lumyn_error_t &out_err)
{
    out_err = cx.Connect(port);
    return out_err == LUMYN_OK;
}

#ifndef _WIN32
static std::vector<std::string> enumerate_ports()
{
    std::vector<std::string> ports;
    glob_t glob_result;
    memset(&glob_result, 0, sizeof(glob_result));
    glob("/dev/ttyACM*", GLOB_NOSORT, NULL, &glob_result);
    glob("/dev/ttyUSB*", GLOB_NOSORT | GLOB_APPEND, NULL, &glob_result);

    for (size_t i = 0; i < glob_result.gl_pathc; ++i) {
        if (glob_result.gl_pathv[i]) {
            ports.emplace_back(glob_result.gl_pathv[i]);
        }
    }

    globfree(&glob_result);
    return ports;
}
#endif

static bool try_connect_after_reboot(ConnectorX &cx,
                                     const std::string &preferred_port,
                                     std::string &out_port)
{
    const int max_attempts = 20;
    lumyn_error_t err = LUMYN_ERR_IO;
    for (int attempt = 1; attempt <= max_attempts; ++attempt) {
        if (!preferred_port.empty() && try_connect(cx, preferred_port, err)) {
            out_port = preferred_port;
            return true;
        }

#ifdef _WIN32
        for (int i = 1; i <= 20; ++i) {
            std::string candidate = "COM" + std::to_string(i);
            if (!preferred_port.empty() && candidate == preferred_port) {
                continue;
            }
            if (try_connect(cx, candidate, err)) {
                out_port = candidate;
                return true;
            }
        }
#else
        std::vector<std::string> ports = enumerate_ports();
        for (const auto &candidate : ports) {
            if (!preferred_port.empty() && candidate == preferred_port) {
                continue;
            }
            if (try_connect(cx, candidate, err)) {
                out_port = candidate;
                return true;
            }
        }
#endif

        std::cerr << "Reconnect attempt " << attempt << "/" << max_attempts
                  << " failed: " << Lumyn_ErrorString(err) << "\n";
        sleep_seconds(2);
    }

    return false;
}

int main(int argc, char *argv[])
{
    std::string port;
    std::string config_path;
    std::string save_path;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--config" && i + 1 < argc) {
            config_path = argv[++i];
        } else if (arg == "--apply" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--save" && i + 1 < argc) {
            save_path = argv[++i];
        } else if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
    }

    if (config_path.empty()) {
        std::cerr << "Please specify --config <file> containing the JSON payload.\n";
        print_usage(argv[0]);
        return 1;
    }

    std::string config_json;
    if (!read_file(config_path, config_json) || config_json.empty()) {
        std::cerr << "Failed to load JSON configuration from " << config_path << "\n";
        return 1;
    }

    if (!save_path.empty()) {
        std::ofstream save(save_path, std::ios::binary);
        if (!save) {
            std::cerr << "Unable to write JSON to " << save_path << "\n";
        } else {
            save << config_json;
            std::cout << "Configuration copied to " << save_path << "\n";
        }
    }

    if (port.empty()) {
        std::cout << "Configuration payload (" << config_json.size() << " bytes):\n";
        std::cout << config_json << "\n";
        std::cout << "\nUse --apply <port> to send this payload to a Lumyn device.\n";
        return 0;
    }

    ConnectorX cx;
    lumyn_error_t err = LUMYN_ERR_IO;
    if (!try_connect(cx, port, err)) {
        std::cerr << "Failed to connect to " << port << ": " << Lumyn_ErrorString(err) << "\n";
        return 1;
    }

    std::cout << "Applying configuration to " << port << "...\n";
    if (!cx.ApplyConfigurationJson(config_json)) {
        std::cerr << "Failed to apply configuration via ConnectorX::ApplyConfigurationJson\n";
        cx.Disconnect();
        return 1;
    }

    std::cout << "Waiting for device to finish writing config (~15s)...\n";
    sleep_seconds(15);

    std::string verify_config;
    lumyn_error_t verify_err = cx.RequestConfig(verify_config, 20000);
    if (verify_err == LUMYN_OK && !verify_config.empty()) {
        if (verify_config == config_json) {
            std::cout << "On-wire verification: device echoed the applied config before reboot.\n";
        } else {
            std::cout << "Warning: device responded with a different config before reboot (length "
                      << verify_config.size() << " vs " << config_json.size() << ").\n";
        }
    } else {
        std::cerr << "Pre-restart config read failed: " << Lumyn_ErrorString(verify_err)
                  << " (aborting restart)\n";
        cx.Disconnect();
        return 1;
    }

    std::cout << "Requesting device restart to persist changes...\n";
    cx.RestartDevice(1000);
    cx.Disconnect();

    std::cout << "Waiting for device to reboot (~20s)...\n";
    sleep_seconds(20);

    std::cout << "Reconnecting to read back the stored configuration...\n";
    ConnectorX cx_after;
    std::string connected_port;
    if (!try_connect_after_reboot(cx_after, port, connected_port)) {
        std::cerr << "Reconnection failed after restart.\n";
        return 1;
    }
    if (!connected_port.empty() && connected_port != port) {
        std::cout << "Reconnected on " << connected_port << " after reboot (was " << port << ").\n";
    }

    std::string device_config;
    lumyn_error_t read_err = cx_after.RequestConfig(device_config, 15000);
    if (read_err == LUMYN_OK && !device_config.empty()) {
        std::cout << "Device reports configuration:\n" << device_config << "\n";
    } else {
        std::cerr << "Failed to request stored config: " << Lumyn_ErrorString(read_err) << "\n";
    }

    cx_after.Disconnect();
    cx.Disconnect();
    return 0;
}
