#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file port_scan.cpp
 * @brief Port Scanning Utility - C++ Example
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <iostream>
#include <vector>
#include <string>
#ifdef _WIN32
#include <windows.h>
#else
#include <glob.h>
#endif

using namespace lumyn::device;

static bool try_handshake(const std::string& port) {
    try {
        ConnectorX cx;
        auto err = cx.Connect(port);
        if (err == LUMYN_OK) {
            cx.Disconnect();
            return true;
        }
    } catch (...) {
    }
    return false;
}

int main() {
    std::cout << "Scanning for ConnectorX on common ports...\n";
    
#ifdef _WIN32
    std::vector<std::string> ports = {"COM1", "COM3", "COM4", "COM5"};
    for (const auto& port : ports) {
        std::cout << "Trying " << port << " ... ";
        bool ok = try_handshake(port);
        std::cout << (ok ? "ok" : "no") << "\n";
    }
#else
    glob_t glob_result;
    glob("/dev/ttyACM*", GLOB_NOSORT, nullptr, &glob_result);
    glob("/dev/ttyUSB*", GLOB_NOSORT | GLOB_APPEND, nullptr, &glob_result);
    
    bool any_success = false;
    for (size_t i = 0; i < glob_result.gl_pathc; i++) {
        std::string port = glob_result.gl_pathv[i];
        std::cout << "Trying " << port << " ... ";
        bool ok = try_handshake(port);
        std::cout << (ok ? "ok" : "no") << "\n";
        any_success |= ok;
    }
    globfree(&glob_result);
    
    if (!any_success) {
        std::cout << "No device responded on common ports.\n";
        return 1;
    }
#endif
    
    return 0;
}
