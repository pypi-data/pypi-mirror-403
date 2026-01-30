#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file matrix_text_advanced.cpp
 * @brief Matrix Text (Advanced) - C++ Example
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <iostream>
#include <string>
#include <thread>
#include <chrono>

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
    std::string zone = "matrix_display";
    bool list_ports_flag = false;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--zone" && i + 1 < argc) {
            zone = argv[++i];
        } else if (arg == "--list-ports") {
            list_ports_flag = true;
        }
    }

    if (list_ports_flag) {
        list_ports();
        return 0;
    }

    if (port.empty()) {
        std::cerr << "Error: --port is required (use --list-ports to see available ports)\n";
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

        std::cout << "Connected.\n";
        std::cout << "Using matrix zone: " << zone << "\n";

        // Example 1: Smooth scrolling with background, font, and ping-pong
        std::cout << "Example 1: smooth scrolling, ping-pong, background\n";
        cx.SetText("HELLO LUMYN")
            .ForZone(zone)
            .WithColor({255, 200, 0})
            .WithBackgroundColor({10, 10, 40})
            .WithFont(LUMYN_MATRIX_TEXT_FONT_FREE_SANS_BOLD_12)
            .WithDirection(LUMYN_MATRIX_TEXT_SCROLL_LEFT)
            .WithDelay(30)
            .SmoothScroll(true)
            .PingPong(true)
            .RunOnce(false);

        std::this_thread::sleep_for(std::chrono::seconds(6));

        // Example 2: Static centered text with alignment + y offset
        std::cout << "Example 2: static centered text with offset\n";
        cx.SetText("STATIC")
            .ForZone(zone)
            .WithColor({0, 255, 120})
            .WithBackgroundColor({0, 0, 0})
            .WithFont(LUMYN_MATRIX_TEXT_FONT_TOM_THUMB)
            .WithAlign(LUMYN_MATRIX_TEXT_ALIGN_CENTER)
            .NoScroll(true)
            .WithYOffset(-2)
            .RunOnce(false);

        std::this_thread::sleep_for(std::chrono::seconds(4));

        // Example 3: Classic scrolling without background
        std::cout << "Example 3: classic scrolling\n";
        cx.SetText("GOOD LUCK!")
            .ForZone(zone)
            .WithColor({255, 0, 0})
            .WithFont(LUMYN_MATRIX_TEXT_FONT_BUILTIN)
            .WithDirection(LUMYN_MATRIX_TEXT_SCROLL_RIGHT)
            .WithDelay(60)
            .SmoothScroll(false)
            .PingPong(false)
            .RunOnce(false);

        std::this_thread::sleep_for(std::chrono::seconds(6));

        std::cout << "Done.\n";

        cx.Disconnect();
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
