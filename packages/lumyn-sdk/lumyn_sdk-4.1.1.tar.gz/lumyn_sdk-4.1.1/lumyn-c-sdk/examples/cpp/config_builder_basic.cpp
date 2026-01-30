#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file config_builder_basic.cpp
 * @brief Configuration Builder - Basic Example - C++
 *
 * Demonstrates creating device configuration programmatically.
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <iostream>
#include <string>
#include <fstream>
#include <thread>
#include <vector>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#else
#include <glob.h>
#include <unistd.h>
#endif

using namespace lumyn::device;

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
    std::memset(&glob_result, 0, sizeof(glob_result));
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

static std::string create_basic_config_json() {
    return R"({
        "team": "9999",
        "network": {"mode": "USB"},
        "channels": {
            "1": {
                "id": "1",
                "length": 144,
                "brightness": 255,
                "zones": [{
                    "id": "main",
                    "type": "strip",
                    "length": 144,
                    "brightness": 100
                }]
            }
        },
        "groups": [{
            "id": "all_leds",
            "zoneIds": ["main"]
        }],
        "sequences": [{
            "id": "startup",
            "steps": [{
                "animationId": "FadeIn",
                "color": {"r": 0, "g": 255, "b": 0},
                "delay": 30,
                "reversed": false,
                "repeat": 1
            }, {
                "animationId": "Fill",
                "color": {"r": 0, "g": 255, "b": 0},
                "delay": -1,
                "reversed": false,
                "repeat": 0
            }]
        }]
    })";
}

int main(int argc, char* argv[]) {
    std::string port;
    std::string save_file;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--apply" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--save" && i + 1 < argc) {
            save_file = argv[++i];
        }
    }
    
    std::string config_json = create_basic_config_json();
    
    if (!save_file.empty()) {
        std::ofstream f(save_file);
        if (f) {
            f << config_json << "\n";
            std::cout << "Configuration saved to " << save_file << "\n";
        }
    }
    
    if (!port.empty()) {
        try {
            ConnectorX cx;
            lumyn_error_t err = LUMYN_ERR_IO;
            if (!try_connect(cx, port, err)) {
                std::cerr << "Failed to connect: " << Lumyn_ErrorString(err) << "\n";
                return 1;
            }
            
            std::cout << "Applying configuration to " << port << "...\n";
            if (!cx.ApplyConfigurationJson(config_json)) {
                std::cerr << "Failed to apply configuration\n";
                cx.Disconnect();
                return 1;
            }

            std::cout << "Waiting for device to finish writing config (~8s)...\n";
            sleep_seconds(8);

            std::string verify_config;
            auto verify_err = cx.RequestConfig(verify_config, 15000);
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
            auto read_err = cx_after.RequestConfig(device_config, 15000);
            if (read_err == LUMYN_OK && !device_config.empty()) {
                std::cout << "Device reports configuration:\n" << device_config << "\n";
            } else {
                std::cerr << "Failed to request stored config: " << Lumyn_ErrorString(read_err) << "\n";
            }

            cx_after.Disconnect();
        } catch (const std::exception& e) {
            std::cerr << "Exception: " << e.what() << "\n";
            return 1;
        }
    } else {
        std::cout << "Configuration JSON:\n";
        std::cout << config_json << "\n";
        std::cout << "\nUse --apply <port> to send to device or --save <file> to save JSON\n";
    }
    
    return 0;
}
