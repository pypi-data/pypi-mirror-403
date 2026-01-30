#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file connectorx_animate.cpp
 * @brief ConnectorX Animate - Advanced Multi-Channel Control - C++ Example
 */

#include <lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <iostream>
#include <thread>
#include <chrono>
#include <string>

using namespace lumyn::device;

static void demo_zone_control(ConnectorXAnimate& cx) {
    std::cout << "\n=== Multi-Channel Zone Control ===\n";
    
    lumyn_color_t red{255, 0, 0};
    lumyn_color_t blue{0, 0, 255};
    lumyn_color_t green{0, 255, 0};
    lumyn_color_t purple{128, 0, 255};
    
    std::cout << "Pattern 1: Left (red) vs Right (blue)...\n";
    cx.SetGroupColor("left_side", red);
    cx.SetGroupColor("right_side", blue);
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    
    std::cout << "Pattern 2: Front (green) vs Rear (purple)...\n";
    cx.SetGroupColor("front_leds", green);
    cx.SetGroupColor("rear_leds", purple);
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    
    std::cout << "Pattern 3: All zones synchronized rainbow...\n";
    lumyn_color_t black{0, 0, 0};
    cx.SetAnimation(lumyn::led::AnimationType::RainbowCycle).ForGroup("all_leds").WithColor(black).WithDelay(40).execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(4000));
}

static void demo_sequences(ConnectorXAnimate& cx) {
    std::cout << "\n=== Animation Sequences ===\n";
    
    std::cout << "Running 'startup' sequence...\n";
    cx.SetImageSequence("startup").ForGroup("all_leds").execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(4000));
    
    std::cout << "Running 'alliance_red' sequence...\n";
    cx.SetImageSequence("alliance_red").ForGroup("all_leds").execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    
    std::cout << "Running 'alliance_blue' sequence...\n";
    cx.SetImageSequence("alliance_blue").ForGroup("all_leds").execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
}

int main(int argc, char* argv[]) {
    std::string port;
    
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " --port <port>\n";
        return 1;
    }
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = argv[++i];
        }
    }
    
    if (port.empty()) {
        std::cerr << "Error: --port is required\n";
        return 1;
    }
    
    try {
        ConnectorXAnimate cx;
        
        std::cout << "Connecting to " << port << "...\n";
        auto err = cx.Connect(port);
        if (err != LUMYN_OK) {
            std::cerr << "Failed to connect: " << Lumyn_ErrorString(err) << "\n";
            return 1;
        }
        
        std::cout << "Connected!\n";
        
        demo_zone_control(cx);
        demo_sequences(cx);
        
        std::cout << "\n=== All demos complete! ===\n";
        
        cx.Disconnect();
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
