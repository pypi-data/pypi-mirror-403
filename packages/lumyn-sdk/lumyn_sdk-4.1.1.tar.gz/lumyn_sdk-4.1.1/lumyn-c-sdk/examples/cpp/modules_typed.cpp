#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file modules_typed.cpp
 * @brief Typed Module Helpers Example - C++
 *
 * Demonstrates using module callbacks for sensor data.
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <iostream>
#include <thread>
#include <chrono>
#include <vector>

using namespace lumyn::device;

int main(int argc, char* argv[]) {
    std::string port = "/dev/ttyUSB0";
    if (argc > 1) {
        port = argv[1];
    }
    
    try {
        ConnectorX cx;
        
        std::cout << "Connecting to " << port << "...\n";
        auto err = cx.Connect(port);
        if (err != LUMYN_OK) {
            std::cerr << "Failed to connect: " << Lumyn_ErrorString(err) << "\n";
            return 1;
        }
        
        std::cout << "Connected! Registering modules...\n";
        
        cx.RegisterModule("digital-1", [](const std::vector<uint8_t>& data) {
            if (data.size() >= 1) {
                std::cout << "DIO state: " << (data[0] ? "HIGH" : "LOW") << "\n";
            }
        });
        
        cx.RegisterModule("analog-1", [](const std::vector<uint8_t>& data) {
            if (data.size() >= 2) {
                uint16_t raw = (data[1] << 8) | data[0];
                std::cout << "Analog raw=" << raw << " scaled=" << (raw / 1023.0) << "\n";
            }
        });
        
        cx.RegisterModule("tof-1", [](const std::vector<uint8_t>& data) {
            if (data.size() >= 3) {
                uint8_t valid = data[0];
                uint16_t dist = (data[2] << 8) | data[1];
                if (valid) {
                    std::cout << "Distance: " << dist << " mm\n";
                }
            }
        });
        
        cx.SetModulePollingEnabled(true);
        
        std::cout << "Press Ctrl+C to exit...\n";
        while (true) {
            cx.PollModules();
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
