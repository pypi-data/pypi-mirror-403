#include <lumyn/Constants.h>  // Required for BuiltInAnimations.h (included via SDK headers)
/**
 * @file event_demo.cpp
 * @brief ConnectorX Event Demo - C++ Example
 *
 * Connects to a device, prints current status, and polls events.
 *
 * Usage:
 *     ./event_demo_cpp --port /dev/ttyACM0 --duration 10 --poll-ms 100
 *     ./event_demo_cpp --list-ports
 */

#include <lumyn/c/lumyn_device.h>
#include <lumyn/c/lumyn_events.h>
#include <lumyn/c/lumyn_sdk.h>

#include <chrono>
#include <cstring>
#include <iostream>
#include <thread>

static void list_ports() {
  std::cout << "Available serial ports:\n";
#ifdef _WIN32
  std::cout << "  COM1\n";
  std::cout << "  COM3\n";
  std::cout << "  COM4\n";
#else
  std::cout << "  /dev/ttyACM0\n";
  std::cout << "  /dev/ttyUSB0\n";
  std::cout << "  /dev/ttyUSB1\n";
#endif
}

static const char* status_to_string(lumyn_status_t status) {
  switch (status) {
    case LUMYN_STATUS_BOOTING: return "Booting";
    case LUMYN_STATUS_ACTIVE: return "Active";
    case LUMYN_STATUS_ERROR: return "Error";
    case LUMYN_STATUS_FATAL: return "Fatal";
    case LUMYN_STATUS_UNKNOWN:
    default: return "Unknown";
  }
}

static const char* event_type_to_string(lumyn_event_type_t type) {
  switch (type) {
    case LUMYN_EVENT_BEGIN_INITIALIZATION: return "BeginInitialization";
    case LUMYN_EVENT_FINISH_INITIALIZATION: return "FinishInitialization";
    case LUMYN_EVENT_ENABLED: return "Enabled";
    case LUMYN_EVENT_DISABLED: return "Disabled";
    case LUMYN_EVENT_CONNECTED: return "Connected";
    case LUMYN_EVENT_DISCONNECTED: return "Disconnected";
    case LUMYN_EVENT_ERROR: return "Error";
    case LUMYN_EVENT_FATAL_ERROR: return "FatalError";
    case LUMYN_EVENT_REGISTERED_ENTITY: return "RegisteredEntity";
    case LUMYN_EVENT_CUSTOM: return "Custom";
    case LUMYN_EVENT_PIN_INTERRUPT: return "PinInterrupt";
    case LUMYN_EVENT_HEARTBEAT: return "HeartBeat";
    case LUMYN_EVENT_OTA: return "OTA";
    case LUMYN_EVENT_MODULE: return "Module";
    default: return "Unknown";
  }
}

static void print_event(const lumyn_event_t& evt) {
  std::cout << "Event: " << event_type_to_string(evt.type);

  switch (evt.type) {
    case LUMYN_EVENT_DISABLED:
      std::cout << " cause=" << static_cast<int>(evt.data.disabled.cause);
      break;
    case LUMYN_EVENT_CONNECTED:
      std::cout << " connType=" << static_cast<int>(evt.data.connected.type);
      break;
    case LUMYN_EVENT_DISCONNECTED:
      std::cout << " connType=" << static_cast<int>(evt.data.disconnected.type);
      break;
    case LUMYN_EVENT_ERROR:
      std::cout << " errorType=" << static_cast<int>(evt.data.error.type)
                << " msg=" << evt.data.error.message;
      break;
    case LUMYN_EVENT_FATAL_ERROR:
      std::cout << " fatalType=" << static_cast<int>(evt.data.fatal_error.type)
                << " msg=" << evt.data.fatal_error.message;
      break;
    case LUMYN_EVENT_HEARTBEAT:
      std::cout << " status=" << static_cast<int>(evt.data.heartbeat.status)
                << " enabled=" << static_cast<int>(evt.data.heartbeat.enabled)
                << " usb=" << static_cast<int>(evt.data.heartbeat.connected_usb)
                << " can=" << static_cast<int>(evt.data.heartbeat.can_ok);
      break;
    default:
      break;
  }

  if (evt.extra_message) {
    std::cout << " extra=\"" << evt.extra_message << "\"";
  }
  std::cout << "\n";
}

int main(int argc, char* argv[]) {
  std::string port;
  bool list_ports_flag = false;
  int duration_sec = 10;
  int poll_ms = 100;

  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
      port = argv[++i];
    } else if (std::strcmp(argv[i], "--duration") == 0 && i + 1 < argc) {
      duration_sec = std::atoi(argv[++i]);
    } else if (std::strcmp(argv[i], "--poll-ms") == 0 && i + 1 < argc) {
      poll_ms = std::atoi(argv[++i]);
    } else if (std::strcmp(argv[i], "--list-ports") == 0) {
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

  cx_t cx{};
  if (lumyn_CreateConnectorX(&cx) != LUMYN_OK) {
    std::cerr << "Failed to create instance\n";
    return 1;
  }
  std::cout << "Connecting to " << port << "...\n";
  auto err = lumyn_Connect(&cx.base, port.c_str());
  if (err != LUMYN_OK) {
    std::cerr << "Failed to connect: " << Lumyn_ErrorString(err) << "\n";
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }
  std::cout << "Connected to ConnectorX!\n";

  lumyn_connection_status_t status = lumyn_GetCurrentStatus(&cx.base);
  lumyn_status_t health = lumyn_GetDeviceHealth(&cx.base);
  std::cout << "Current status: connected=" << (status.connected ? 1 : 0)
            << " enabled=" << (status.enabled ? 1 : 0)
            << " health=" << status_to_string(health) << "\n";

  auto start = std::chrono::steady_clock::now();
  while (std::chrono::duration_cast<std::chrono::seconds>(
             std::chrono::steady_clock::now() - start)
             .count() < duration_sec) {
    const int kMaxEvents = 16;
    lumyn_event_t events[kMaxEvents];
    int out_count = 0;
    if (lumyn_GetEvents(&cx.base, events, kMaxEvents, &out_count) == LUMYN_OK) {
      for (int i = 0; i < out_count; ++i) {
        print_event(events[i]);
      }
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(poll_ms));
  }

  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);
  std::cout << "Done!\n";
  return 0;
}
