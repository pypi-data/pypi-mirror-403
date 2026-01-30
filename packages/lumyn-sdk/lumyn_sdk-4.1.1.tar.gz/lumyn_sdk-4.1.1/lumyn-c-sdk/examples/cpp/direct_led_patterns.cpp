#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file direct_led_patterns.cpp
 * @brief DirectLED Pattern Animations - C++ Example
 *
 * Demonstrates DirectLED API with various pattern animations.
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/c/lumyn_config.h>
#include <iostream>
#include <vector>
#include <cmath>
#include <thread>
#include <chrono>
#include <cstring>

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

static int get_zone_led_count(const std::string& config_json, const std::string& zone_id) {
    if (config_json.empty()) {
        return 0;
    }

    lumyn_config_t* cfg = nullptr;
    lumyn_error_t err = lumyn_ParseConfig(config_json.c_str(), config_json.size(), &cfg);
    if (err != LUMYN_OK || !cfg) {
        std::cerr << "Failed to parse device config JSON: " << Lumyn_ErrorString(err) << "\n";
        return 0;
    }

    int led_count = 0;
    const int channel_count = lumyn_ConfigGetChannelCount(cfg);
    for (int c = 0; c < channel_count && led_count == 0; ++c) {
        const lumyn_channel_t* ch = lumyn_ConfigGetChannel(cfg, c);
        const int zone_count = lumyn_ChannelGetZoneCount(ch);
        for (int z = 0; z < zone_count; ++z) {
            const lumyn_zone_t* zone = lumyn_ChannelGetZone(ch, z);
            if (zone && zone_id == lumyn_ZoneGetId(zone)) {
                led_count = lumyn_ZoneGetLedCount(zone);
                break;
            }
        }
    }

    lumyn_FreeConfig(cfg);
    return led_count;
}

static void rainbow_pattern(std::vector<uint8_t>& buffer, int num_leds, int offset) {
    for (int i = 0; i < num_leds; i++) {
        int hue = ((i + offset) * 360 / num_leds) % 360;
        float h = hue / 60.0f;
        int c = 255;
        float x = c * (1 - std::abs(std::fmod(h, 2) - 1));
        
        if (h < 1) {
            buffer[i*3+0] = c; buffer[i*3+1] = (int)(x); buffer[i*3+2] = 0;
        } else if (h < 2) {
            buffer[i*3+0] = (int)(x); buffer[i*3+1] = c; buffer[i*3+2] = 0;
        } else if (h < 3) {
            buffer[i*3+0] = 0; buffer[i*3+1] = c; buffer[i*3+2] = (int)(x);
        } else if (h < 4) {
            buffer[i*3+0] = 0; buffer[i*3+1] = (int)(x); buffer[i*3+2] = c;
        } else if (h < 5) {
            buffer[i*3+0] = (int)(x); buffer[i*3+1] = 0; buffer[i*3+2] = c;
        } else {
            buffer[i*3+0] = c; buffer[i*3+1] = 0; buffer[i*3+2] = (int)(x);
        }
    }
}

static void wave_pattern(std::vector<uint8_t>& buffer, int num_leds, int frame) {
    for (int i = 0; i < num_leds; i++) {
        float wave = std::sin((i + frame) * 0.2f) * 0.5f + 0.5f;
        buffer[i*3+0] = (int)(wave * 255);
        buffer[i*3+1] = (int)(wave * 100);
        buffer[i*3+2] = (int)(wave * 50);
    }
}

static void moving_pixel(std::vector<uint8_t>& buffer, int num_leds, int pos) {
    std::fill(buffer.begin(), buffer.end(), 0);
    if (pos >= 0 && pos < num_leds) {
        buffer[pos*3+0] = 255;
        buffer[pos*3+1] = 255;
        buffer[pos*3+2] = 255;
    }
}

int main(int argc, char* argv[]) {
    std::string port;
    std::string zone = "main";
    int num_leds = 0;
    bool list_ports_flag = false;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--zone" && i + 1 < argc) {
            zone = argv[++i];
        } else if (arg == "--num-leds" && i + 1 < argc) {
            num_leds = std::atoi(argv[++i]);
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
        
        if (num_leds <= 0) {
            std::string config_json;
            auto cfg_err = cx.RequestConfig(config_json, 5000);
            if (cfg_err == LUMYN_OK && !config_json.empty()) {
                num_leds = get_zone_led_count(config_json, zone);
            }
        }

        if (num_leds <= 0) {
            std::cerr << "Unable to determine LED count for zone '" << zone << "'. Use --num-leds.\n";
            cx.Disconnect();
            return 1;
        }

        std::cout << "Connected! Creating DirectLED for " << num_leds << " LEDs...\n";
        
        auto direct_led = cx.CreateDirectLED(zone, num_leds, 30);
        
        std::vector<uint8_t> buffer(num_leds * 3);
        
        std::cout << "\nPattern 1: Rainbow wave (10 seconds)\n";
        for (int frame = 0; frame < 100; frame++) {
            rainbow_pattern(buffer, num_leds, frame * 2);
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        std::cout << "Pattern 2: Color wave (5 seconds)\n";
        for (int frame = 0; frame < 50; frame++) {
            wave_pattern(buffer, num_leds, frame);
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        std::cout << "Pattern 3: Moving pixel (5 seconds)\n";
        for (int frame = 0; frame < num_leds * 2; frame++) {
            moving_pixel(buffer, num_leds, frame % num_leds);
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
        
        std::cout << "Clearing...\n";
        std::fill(buffer.begin(), buffer.end(), 0);
        direct_led.UpdateRaw(buffer.data(), buffer.size());
        
        cx.Disconnect();
        
        std::cout << "Done!\n";
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
}
