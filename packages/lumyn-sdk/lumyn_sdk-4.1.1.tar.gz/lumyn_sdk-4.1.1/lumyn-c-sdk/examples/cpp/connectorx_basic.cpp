#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file connectorx_basic.cpp
 * @brief ConnectorX Basic Usage - C++ Example
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <iostream>
#include <thread>
#include <chrono>
#include <string>

using namespace lumyn::device;

static void example_basic_colors(ConnectorX& cx) {
    std::cout << "\n=== Example 1: Basic Colors ===\n";
    
    lumyn_color_t red{255, 0, 0};
    lumyn_color_t green{0, 255, 0};
    lumyn_color_t blue{0, 0, 255};
    lumyn_color_t orange{255, 165, 0};
    
    std::cout << "Setting 'main' to RED...\n";
    cx.SetColor("main", red);
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    std::cout << "Setting 'main' to GREEN...\n";
    cx.SetColor("main", green);
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    std::cout << "Setting 'main' to BLUE...\n";
    cx.SetColor("main", blue);
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    
    std::cout << "Setting 'main' to ORANGE...\n";
    cx.SetColor("main", orange);
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
}

static void example_animations(ConnectorX& cx) {
    std::cout << "\n=== Example 2: Built-in Animations ===\n";
    
    lumyn_color_t black{0, 0, 0};
    lumyn_color_t blue{0, 0, 255};
    lumyn_color_t red{255, 0, 0};
    lumyn_color_t green{0, 255, 0};
    lumyn_color_t orange{255, 100, 0};
    
    std::cout << "Running RAINBOW ROLL animation...\n";
    cx.SetAnimation(lumyn::led::AnimationType::RainbowRoll).ForZone("main").WithColor(black).WithDelay(50).execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(3000));
    
    std::cout << "Running BREATHE animation (blue)...\n";
    cx.SetAnimation(lumyn::led::AnimationType::Breathe).ForZone("main").WithColor(blue).WithDelay(30).execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(3000));
    
    std::cout << "Running BLINK animation (red)...\n";
    cx.SetAnimation(lumyn::led::AnimationType::Blink).ForZone("main").WithColor(red).WithDelay(500).execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(3000));
    
    std::cout << "Running CHASE animation (green)...\n";
    cx.SetAnimation(lumyn::led::AnimationType::Chase).ForZone("main").WithColor(green).WithDelay(50).execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(3000));
    
    std::cout << "Running FIRE animation...\n";
    cx.SetAnimation(lumyn::led::AnimationType::Fire).ForZone("main").WithColor(orange).WithDelay(30).execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(3000));
}

static void example_sequences(ConnectorX& cx) {
    std::cout << "\n=== Example 3: Animation Sequences ===\n";
    
    std::cout << "Running 'startup' sequence...\n";
    cx.SetImageSequence("startup").ForZone("main").execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(4000));
    
    std::cout << "Running 'alliance_red' sequence...\n";
    cx.SetImageSequence("alliance_red").ForZone("main").execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    
    std::cout << "Running 'alliance_blue' sequence...\n";
    cx.SetImageSequence("alliance_blue").ForZone("main").execute();
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
}

int main(int argc, char* argv[]) {
    std::string port;
    std::string example = "all";
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--example" && i + 1 < argc) {
            example = argv[++i];
        }
    }
    
    if (port.empty()) {
        std::cerr << "Error: --port is required\n";
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
        
        std::cout << "Connected successfully!\n";
        
        if (example == "colors" || example == "all") {
            example_basic_colors(cx);
        }
        
        if (example == "animations" || example == "all") {
            example_animations(cx);
        }
        
        if (example == "sequences" || example == "all") {
            example_sequences(cx);
        }
        
        std::cout << "\nExamples complete!\n";
        
        cx.Disconnect();
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
