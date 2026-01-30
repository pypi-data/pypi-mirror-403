/**
 * @file builder_example.cpp
 * @brief C++ example demonstrating animation builder usage
 * 
 * This example shows:
 * - Creating a ConnectorXAnimate instance
 * - Connecting to a device
 * - Using the animation builder pattern
 * - Executing animations with fluent API
 */

#include "lumyn/cpp/connectorXVariant/ConnectorXAnimate.hpp"
#include <iostream>
#include <chrono>

int main() {
    std::cout << "Lumyn Animation Builder Example\n";
    std::cout << "===============================\n";

    try {
        // Create ConnectorXAnimate instance
        lumyn::device::ConnectorXAnimate cx;
        std::cout << "✓ Created ConnectorXAnimate instance\n";

        // Connect to device (will fail without device, but demonstrates API)
        std::cout << "Attempting to connect to /dev/ttyACM0...\n";
        auto err = cx.Connect("/dev/ttyACM0");
        if (err != LUMYN_OK) {
            std::cout << "Connect failed (expected without device): " 
                      << Lumyn_ErrorString(err) << "\n";
            std::cout << "Demonstrating builder API without device...\n\n";
        } else {
            std::cout << "✓ Connected successfully\n";
        }

        // Demonstrate animation builder usage
        std::cout << "Setting up chase animation with builder pattern:\n";
        
    // Create a chase animation on the front zone
    lumyn_color_t blue{0, 100, 255};
        cx.SetAnimation(LUMYN_ANIMATION_CHASE)
          .ForZone("front")
          .WithColor(blue)
          .WithDelay(std::chrono::milliseconds(50))
          .Reverse(false)
          .RunOnce(false);
        
        std::cout << "✓ Chase animation configured for front zone\n";

    // Create a sparkle animation on the back zone
    lumyn_color_t orange{255, 165, 0};
        cx.SetAnimation(LUMYN_ANIMATION_SPARKLE)
          .ForZone("back")
          .WithColor(orange)
          .WithDelay(100)  // Using milliseconds as uint32_t
          .Reverse(false)
          .RunOnce(true);  // Run once and stop
        
        std::cout << "✓ Sparkle animation configured for back zone\n";

    // Create a breathe animation for a group
    lumyn_color_t purple{128, 0, 128};
        cx.SetAnimation(LUMYN_ANIMATION_BREATHE)
          .ForGroup("all_zones")
          .WithColor(purple)
          .WithDelay(std::chrono::milliseconds(10))
          .Reverse(false)
          .RunOnce(false);
        
        std::cout << "✓ Breathe animation configured for all_zones group\n";

        if (err == LUMYN_OK) {
            std::cout << "\nAnimations are now running on the device!\n";
            std::cout << "Press Ctrl+C to stop.\n";
        } else {
            std::cout << "\nBuilder pattern demonstrated successfully.\n";
            std::cout << "Connect a device to see animations in action.\n";
        }

        // Disconnect and cleanup (automatic in destructor)
        std::cout << "\nCleaning up...\n";
        cx.Disconnect();
        std::cout << "✓ Cleanup complete\n";

    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }

    return 0;
}