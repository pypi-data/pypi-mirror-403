#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file handshake_basic.cpp
 * @brief Basic Handshake Example - C++
 *
 * Demonstrates low-level handshake protocol.
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <iostream>
#include <string>

using namespace lumyn::device;

int main(int argc, char* argv[]) {
    std::string port;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--port" && i + 1 < argc) {
            port = argv[++i];
        }
    }

    if (port.empty()) {
        std::cerr << "Usage: " << argv[0] << " --port <port>\n";
        return 1;
    }
    
    try {
        ConnectorX cx;
        
        std::cout << "Connecting to " << port << "...\n";
        auto err = cx.Connect(port);
        if (err != LUMYN_OK) {
            std::cerr << "Failed to connect: " << Lumyn_ErrorString(err) << "\n";
            return 1;
        }
        
        std::cout << "Connected! Handshake completed automatically.\n";
        std::cout << "Device is ready for commands.\n";
        
        cx.Disconnect();
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
