#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file quickstart.cpp
 * @brief ConnectorX Quick Start - C++ Example
 *
 * The simplest example to get started with ConnectorX LEDs.
 *
 * Usage:
 *     ./quickstart_cpp --port /dev/ttyACM0
 *     ./quickstart_cpp --port COM3 --zone zone_0
 *     ./quickstart_cpp --list-ports
 */

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/c/lumyn_config.h> // C parser matches Python behavior
#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <cstring>

using namespace lumyn::device;

static const char* skip_ws(const char* s) {
    while (s && *s && (*s == ' ' || *s == '\n' || *s == '\r' || *s == '\t')) {
        s++;
    }
    return s;
}

static bool extract_string_value(const char* obj, const char* key, std::string& out) {
    std::string needle = "\"" + std::string(key) + "\"";
    const char* p = strstr(obj, needle.c_str());
    if (!p) return false;
    p = strchr(p + needle.size(), ':');
    if (!p) return false;
    p = skip_ws(p + 1);
    if (*p != '"') return false;
    p++;
    const char* end = strchr(p, '"');
    if (!end) return false;
    out.assign(p, end - p);
    return true;
}

static bool extract_int_value(const char* obj, const char* key, int& out) {
    std::string needle = "\"" + std::string(key) + "\"";
    const char* p = strstr(obj, needle.c_str());
    if (!p) return false;
    p = strchr(p + needle.size(), ':');
    if (!p) return false;
    p = skip_ws(p + 1);
    out = std::atoi(p);
    return true;
}

static bool extract_bool_value(const char* obj, const char* key, bool& out) {
    std::string needle = "\"" + std::string(key) + "\"";
    const char* p = strstr(obj, needle.c_str());
    if (!p) return false;
    p = strchr(p + needle.size(), ':');
    if (!p) return false;
    p = skip_ws(p + 1);
    if (strncmp(p, "true", 4) == 0) { out = true; return true; }
    if (strncmp(p, "false", 5) == 0) { out = false; return true; }
    return false;
}

static bool extract_zone_object(const char* json, const char* zone_id, std::string& out) {
    const char* p = json;
    while ((p = strstr(p, "\"id\"")) != nullptr) {
        const char* id_val = strchr(p + 4, ':');
        if (!id_val) break;
        id_val = skip_ws(id_val + 1);
        if (*id_val != '"') { p += 4; continue; }
        id_val++;
        const char* id_end = strchr(id_val, '"');
        if (!id_end) break;
        if ((size_t)(id_end - id_val) == strlen(zone_id) &&
            strncmp(id_val, zone_id, id_end - id_val) == 0) {
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

static bool format_zone_python_dict(const std::string& json, const std::string& zone_id, std::string& out) {
    std::string obj;
    if (!extract_zone_object(json.c_str(), zone_id.c_str(), obj)) return false;

    std::string type;
    extract_string_value(obj.c_str(), "type", type);
    int brightness = 0;
    bool has_brightness = extract_int_value(obj.c_str(), "brightness", brightness);

    if (type == "matrix") {
        int rows = 0, cols = 0;
        extract_int_value(obj.c_str(), "rows", rows);
        extract_int_value(obj.c_str(), "cols", cols);
        std::string corner_tb, corner_lr, axis_layout, seq_layout;
        extract_string_value(obj.c_str(), "cornerTopBottom", corner_tb);
        extract_string_value(obj.c_str(), "cornerLeftRight", corner_lr);
        extract_string_value(obj.c_str(), "axisLayout", axis_layout);
        extract_string_value(obj.c_str(), "sequenceLayout", seq_layout);
        if (has_brightness) {
            out = "{'id': '" + zone_id + "', 'type': 'matrix', 'rows': " + std::to_string(rows) +
                  ", 'cols': " + std::to_string(cols) + ", 'brightness': " + std::to_string(brightness) +
                  ", 'orientation': {'cornerTopBottom': '" + corner_tb + "', 'cornerLeftRight': '" + corner_lr +
                  "', 'axisLayout': '" + axis_layout + "', 'sequenceLayout': '" + seq_layout + "'}}";
        } else {
            out = "{'id': '" + zone_id + "', 'type': 'matrix', 'rows': " + std::to_string(rows) +
                  ", 'cols': " + std::to_string(cols) +
                  ", 'orientation': {'cornerTopBottom': '" + corner_tb + "', 'cornerLeftRight': '" + corner_lr +
                  "', 'axisLayout': '" + axis_layout + "', 'sequenceLayout': '" + seq_layout + "'}}";
        }
        return true;
    }

    int length = 0;
    bool reversed = false;
    extract_int_value(obj.c_str(), "length", length);
    extract_bool_value(obj.c_str(), "reversed", reversed);
    if (has_brightness) {
        out = "{'id': '" + zone_id + "', 'type': 'strip', 'length': " + std::to_string(length) +
              ", 'brightness': " + std::to_string(brightness) + ", 'reversed': " + (reversed ? "True" : "False") + "}";
    } else {
        out = "{'id': '" + zone_id + "', 'type': 'strip', 'length': " + std::to_string(length) +
              ", 'reversed': " + (reversed ? "True" : "False") + "}";
    }
    return true;
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
                std::string zone_str;
                if (format_zone_python_dict(config_json, zone_id, zone_str)) {
                    std::cout << "Found zone: " << zone_str << "\n";
                }
                break;
            }
        }
    }

    lumyn_FreeConfig(cfg);
    return led_count;
}

int main(int argc, char* argv[]) {
    std::string port;
    std::string zone = "zone_0";
    bool list_ports_flag = false;
    
    for (int i = 1; i < argc; i++) {
        if (std::strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            port = argv[++i];
        } else if (std::strcmp(argv[i], "--zone") == 0 && i + 1 < argc) {
            zone = argv[++i];
        } else if (std::strcmp(argv[i], "--list-ports") == 0) {
            list_ports_flag = true;
        }
    }
    
    if (port.empty()) {
        std::cout << "Error: --port is required (use --list-ports to see available ports)\n";
        return 1;
    }
    
    try {
        ConnectorX cx;
        
        std::cout << "Connecting to " << port << "...\n";
        auto err = cx.Connect(port);
        if (err != LUMYN_OK) {
            std::cout << "Failed to connect!\n";
            std::cout << "Use --list-ports to see available serial ports\n";
            return 1;
        }
        
        std::cout << "Connected to ConnectorX!\n";
        
        std::string config_json;
        auto cfg_err = cx.RequestConfig(config_json, 5000);
        if (cfg_err == LUMYN_OK && !config_json.empty()) {
            std::cout << "Config on device: " << config_json << "\n";
        } else if (cfg_err == LUMYN_OK) {
            std::cout << "Config on device: None\n";
        } else {
            std::cout << "Failed to read device config: " << Lumyn_ErrorString(cfg_err) << "\n";
        }

        int num_leds = -1;

        lumyn_color_t black{0, 0, 0};
        lumyn_color_t red{255, 0, 0};
        lumyn_color_t green{0, 150, 0};
        lumyn_color_t blue{0, 0, 255};
        lumyn_color_t purple{128, 0, 255};
        lumyn_color_t orange{255, 128, 0};

        std::cout << "Red breathe animation...\n";
        cx.SetAnimation(LUMYN_ANIMATION_BREATHE).ForZone(zone).WithColor(red).WithDelay(10).RunOnce(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(6000));

        std::cout << "Green plasma animation...\n";
        cx.SetAnimation(LUMYN_ANIMATION_PLASMA).ForZone(zone).WithColor(green).WithDelay(100).RunOnce(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(3000));

        std::cout << "Blue chase animation...\n";
        cx.SetAnimation(LUMYN_ANIMATION_CHASE).ForZone(zone).WithColor(blue).WithDelay(50).RunOnce(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(5000));

        std::cout << "Purple comet animation...\n";
        cx.SetAnimation(LUMYN_ANIMATION_COMET).ForZone(zone).WithColor(purple).WithDelay(20).RunOnce(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(3000));

        std::cout << "Orange sparkle animation...\n";
        cx.SetAnimation(LUMYN_ANIMATION_SPARKLE).ForZone(zone).WithColor(orange).WithDelay(100).RunOnce(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(3000));

        std::cout << "Rainbow roll animation...\n";
        cx.SetAnimation(LUMYN_ANIMATION_RAINBOW_CYCLE).ForZone(zone).WithColor(black).WithDelay(50).RunOnce(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(3000));

        std::cout << "\nDirect LED buffer test with DirectLED...\n";

        if (!config_json.empty()) {
            num_leds = get_zone_led_count(config_json, zone);
        }

        if (num_leds > 0) {
            std::cout << "Zone '" << zone << "' has " << num_leds << " LEDs\n";

            auto direct_led = cx.CreateDirectLED(zone, num_leds, 10);

            std::vector<uint8_t> buffer(static_cast<size_t>(num_leds) * 3);

            for (int i = 0; i < num_leds; i++) {
                buffer[i * 3 + 0] = 255;
                buffer[i * 3 + 1] = 0;
                buffer[i * 3 + 2] = 0;
            }
            std::cout << "Frame 0: Setting all LEDs to RED (auto: full buffer)...\n";
            direct_led.ForceFullUpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));

            for (int i = 0; i < num_leds; i++) {
                buffer[i * 3 + 0] = 0;
                buffer[i * 3 + 1] = 255;
                buffer[i * 3 + 2] = 0;
            }
            std::cout << "Frame 1: Setting all LEDs to GREEN (auto: delta)...\n";
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));

            for (int i = 0; i < num_leds; i++) {
                if (i % 2 == 0) {
                    buffer[i * 3 + 0] = 255;
                    buffer[i * 3 + 1] = 0;
                    buffer[i * 3 + 2] = 0;
                } else {
                    buffer[i * 3 + 0] = 0;
                    buffer[i * 3 + 1] = 0;
                    buffer[i * 3 + 2] = 255;
                }
            }
            std::cout << "Frame 2: Setting alternating RED/BLUE (auto: delta)...\n";
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));

            std::cout << "Frames 3-12: Moving white pixel (auto: delta for frames 3-9, full at frame 10)...\n";
            for (int frame = 3; frame < 13; frame++) {
                for (int i = 0; i < num_leds; i++) {
                    if (i == (frame - 3) % num_leds) {
                        buffer[i * 3 + 0] = 255;
                        buffer[i * 3 + 1] = 255;
                        buffer[i * 3 + 2] = 255;
                    } else {
                        buffer[i * 3 + 0] = 0;
                        buffer[i * 3 + 1] = 0;
                        buffer[i * 3 + 2] = 0;
                    }
                }
                direct_led.UpdateRaw(buffer.data(), buffer.size());
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }

            std::cout << "Filling with black\n";
            std::fill(buffer.begin(), buffer.end(), 0);
            direct_led.UpdateRaw(buffer.data(), buffer.size());
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        } else {
            std::cout << "Could not find zone '" << zone << "' in config\n";
        }

        std::cout << "\nOff\n";
        cx.SetAnimation(LUMYN_ANIMATION_FILL).ForZone(zone).WithColor(black).WithDelay(0).RunOnce(true);
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        
        cx.Disconnect();
        
        std::cout << "Done!\n";
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }
}
