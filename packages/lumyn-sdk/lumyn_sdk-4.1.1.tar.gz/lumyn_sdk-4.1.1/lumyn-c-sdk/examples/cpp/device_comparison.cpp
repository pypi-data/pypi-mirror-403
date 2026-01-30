#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file device_comparison.cpp
 * @brief Device Type Comparison - C++ Example
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>
#include <iostream>
#include <string>

using namespace lumyn::device;

static void list_ports() {
    std::cout << "Available serial ports:\n";
#ifdef _WIN32
    std::cout << "  COM3\n";
#else
    std::cout << "  /dev/ttyACM0\n";
    std::cout << "  /dev/ttyUSB0\n";
#endif
}

int main(int argc, char* argv[]) {
    std::string port;
    bool list_ports_flag = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--list-ports") {
            list_ports_flag = true;
        }
    }

    if (list_ports_flag) {
        list_ports();
        return 0;
    }

    if (port.empty()) {
        std::cout << "Usage: " << argv[0] << " --port <port>\n";
        std::cout << "\nFeature Comparison:\n";
        std::cout << "  ConnectorX: USB + UART, LEDs + Modules\n";
        std::cout << "  ConnectorXAnimate: USB only, LEDs only\n";
        return 1;
    }
    
    std::cout << "\n=== ConnectorX ===\n";
    try {
        ConnectorX cx;
        std::cout << "Created ConnectorX instance\n";
        auto err = cx.Connect(port);
        if (err == LUMYN_OK) {
            std::cout << "Connected successfully\n";
            std::cout << "Features: USB + UART, LEDs + Modules\n";
            cx.Disconnect();
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }
    
    std::cout << "\n=== ConnectorXAnimate ===\n";
    try {
        ConnectorXAnimate cx_animate;
        std::cout << "Created ConnectorXAnimate instance\n";
        auto err = cx_animate.Connect(port);
        if (err == LUMYN_OK) {
            std::cout << "Connected successfully\n";
            std::cout << "Features: USB only, LEDs only\n";
            cx_animate.Disconnect();
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }
    
    return 0;
}
