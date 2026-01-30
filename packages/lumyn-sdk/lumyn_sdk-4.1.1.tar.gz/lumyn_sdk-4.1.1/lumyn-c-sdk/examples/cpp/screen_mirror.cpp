#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file screen_mirror.cpp
 * @brief Screen Mirror to LED Matrix - C++ Example
 *
 * NOTE: Full screen capture requires platform-specific libraries.
 * This is a simplified version demonstrating the DirectLED API usage pattern.
 * For full functionality, integrate with screen capture libraries (e.g., X11 on Linux).
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>

#include <lumyn/c/lumyn_config.h>

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

static const char* skip_ws(const char* s) {
    while (s && *s && (*s == ' ' || *s == '\n' || *s == '\r' || *s == '\t')) {
        s++;
    }
    return s;
}

static bool extract_string_value(const char* obj, const char* key, std::string& out) {
    char needle[64];
    std::snprintf(needle, sizeof(needle), "\"%s\"", key);
    const char* p = std::strstr(obj, needle);
    if (!p) return false;
    p = std::strchr(p + std::strlen(needle), ':');
    if (!p) return false;
    p = skip_ws(p + 1);
    if (*p != '"') return false;
    p++;
    const char* end = std::strchr(p, '"');
    if (!end) return false;
    out.assign(p, end - p);
    return true;
}

static bool extract_int_value(const char* obj, const char* key, int& out) {
    char needle[64];
    std::snprintf(needle, sizeof(needle), "\"%s\"", key);
    const char* p = std::strstr(obj, needle);
    if (!p) return false;
    p = std::strchr(p + std::strlen(needle), ':');
    if (!p) return false;
    p = skip_ws(p + 1);
    out = std::atoi(p);
    return true;
}

static bool extract_zone_object(const char* json, const char* zone_id, std::string& out) {
    if (!json || !zone_id) return false;
    const char* id_key = "\"id\"";
    const char* p = json;
    while ((p = std::strstr(p, id_key)) != nullptr) {
        const char* id_val = std::strchr(p + std::strlen(id_key), ':');
        if (!id_val) break;
        id_val = skip_ws(id_val + 1);
        if (*id_val != '"') { p += 4; continue; }
        id_val++;
        const char* id_end = std::strchr(id_val, '"');
        if (!id_end) break;
        if ((size_t)(id_end - id_val) == std::strlen(zone_id) &&
            std::strncmp(id_val, zone_id, id_end - id_val) == 0) {
            int depth = 0;
            const char* start = p;
            for (const char* b = p; b >= json; --b) {
                if (*b == '}') depth++;
                if (*b == '{') {
                    if (depth == 0) { start = b; break; }
                    depth--;
                }
                if (b == json) break;
            }
            depth = 0;
            const char* end = start;
            for (const char* f = start; *f; ++f) {
                if (*f == '{') depth++;
                if (*f == '}') {
                    depth--;
                    if (depth == 0) { end = f; break; }
                }
            }
            out.assign(start, end - start + 1);
            return true;
        }
        p = id_end + 1;
    }
    return false;
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

// Simplified pattern generator instead of actual screen capture
static void generate_pattern(std::vector<uint8_t>& buffer, int width, int height, int frame) {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = (y * width + x) * 3;
            // Generate a moving pattern
            float fx = (x + frame * 0.1f) * 0.2f;
            float fy = (y + frame * 0.1f) * 0.2f;
            buffer[idx + 0] = (uint8_t)(127 + 127 * std::sin(fx));
            buffer[idx + 1] = (uint8_t)(127 + 127 * std::sin(fy));
            buffer[idx + 2] = (uint8_t)(127 + 127 * std::sin(fx + fy));
        }
    }
}

int main(int argc, char* argv[]) {
    std::string port;
    std::string zone = "matrix_display";
    int width = 0, height = 0;
    int fps = 30;
    int duration = 20;
    bool list_ports_flag = false;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = argv[++i];
        } else if (arg == "--zone" && i + 1 < argc) {
            zone = argv[++i];
        } else if (arg == "--width" && i + 1 < argc) {
            width = std::atoi(argv[++i]);
        } else if (arg == "--height" && i + 1 < argc) {
            height = std::atoi(argv[++i]);
        } else if (arg == "--fps" && i + 1 < argc) {
            fps = std::atoi(argv[++i]);
        } else if (arg == "--duration" && i + 1 < argc) {
            duration = std::atoi(argv[++i]);
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
        
        std::string config_json;
        auto cfg_err = cx.RequestConfig(config_json, 5000);
        if (cfg_err == LUMYN_OK && !config_json.empty() && (width == 0 || height == 0)) {
            std::string zone_obj;
            if (extract_zone_object(config_json.c_str(), zone.c_str(), zone_obj)) {
                std::string type;
                extract_string_value(zone_obj.c_str(), "type", type);
                if (type == "matrix") {
                    int rows = 0;
                    int cols = 0;
                    extract_int_value(zone_obj.c_str(), "rows", rows);
                    extract_int_value(zone_obj.c_str(), "cols", cols);
                    if (rows > 0 && cols > 0) {
                        width = (width > 0) ? width : cols;
                        height = (height > 0) ? height : rows;
                    }
                } else if (type == "strip") {
                    int length = 0;
                    extract_int_value(zone_obj.c_str(), "length", length);
                    if (length > 0) {
                        width = (width > 0) ? width : length;
                        height = (height > 0) ? height : 1;
                    }
                }
            }
        }

        if (width == 0 || height == 0) {
            int led_count = 0;
            if (!config_json.empty()) {
                led_count = get_zone_led_count(config_json, zone);
            }
            if (led_count > 0) {
                width = (width > 0) ? width : led_count;
                height = (height > 0) ? height : 1;
            } else {
                width = (width > 0) ? width : 8;
                height = (height > 0) ? height : 8;
            }
        }

        int num_leds = width * height;

        std::cout << "Connected! Creating DirectLED for " << num_leds << " LEDs (" 
                  << width << "x" << height << ")\n";
        
        auto direct_led = cx.CreateDirectLED(zone, num_leds, 30);
        
        std::vector<uint8_t> buffer(num_leds * 3);
        
        auto frame_time = std::chrono::milliseconds(1000 / fps);
        auto start_time = std::chrono::steady_clock::now();
        int frame_count = 0;
        
        std::cout << "Starting pattern animation at " << fps << " FPS for " << duration << " seconds...\n";
        
        while (true) {
            auto elapsed = std::chrono::steady_clock::now() - start_time;
            if (std::chrono::duration_cast<std::chrono::seconds>(elapsed).count() >= duration) {
                break;
            }
            
            auto frame_start = std::chrono::steady_clock::now();
            
            generate_pattern(buffer, width, height, frame_count);
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            
            frame_count++;
            
            if (frame_count % fps == 0) {
                auto actual_elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(elapsed);
                double actual_fps = frame_count * 1000.0 / actual_elapsed.count();
                std::cout << "Frame " << frame_count << ": " << actual_fps << " FPS\n";
            }
            
            auto elapsed_frame = std::chrono::steady_clock::now() - frame_start;
            if (elapsed_frame < frame_time) {
                std::this_thread::sleep_for(frame_time - elapsed_frame);
            }
        }
        
        std::cout << "\nClearing matrix...\n";
        std::fill(buffer.begin(), buffer.end(), 0);
        direct_led.ForceFullUpdateRaw(buffer.data(), buffer.size());
        
        cx.Disconnect();
        
        std::cout << "Done!\n";
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
}
