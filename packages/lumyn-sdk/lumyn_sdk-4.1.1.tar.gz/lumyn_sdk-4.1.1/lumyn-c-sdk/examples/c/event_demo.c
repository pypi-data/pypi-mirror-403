/**
 * @file event_demo.c
 * @brief ConnectorX Event Demo - C Example
 *
 * Connects to a device, prints current status, and polls events.
 *
 * Usage:
 *     ./event_demo_c --port /dev/ttyACM0 --duration 10 --poll-ms 100
 *     ./event_demo_c --list-ports
 */

#include <lumyn/c/lumyn_device.h>
#include <lumyn/c/lumyn_events.h>
#include <lumyn/c/lumyn_sdk.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#define sleep_ms(ms) Sleep(ms)
#else
#include <unistd.h>
#define sleep_ms(ms) usleep((ms) * 1000)
#endif

static void list_ports(void)
{
  printf("Available serial ports:\n");
#ifdef _WIN32
  printf("  COM1\n");
  printf("  COM3\n");
  printf("  COM4\n");
#else
  printf("  /dev/ttyACM0\n");
  printf("  /dev/ttyUSB0\n");
  printf("  /dev/ttyUSB1\n");
#endif
}

static const char *status_to_string(lumyn_status_t status)
{
  switch (status)
  {
  case LUMYN_STATUS_BOOTING:
    return "Booting";
  case LUMYN_STATUS_ACTIVE:
    return "Active";
  case LUMYN_STATUS_ERROR:
    return "Error";
  case LUMYN_STATUS_FATAL:
    return "Fatal";
  case LUMYN_STATUS_UNKNOWN:
  default:
    return "Unknown";
  }
}

static const char *event_type_to_string(lumyn_event_type_t type)
{
  switch (type)
  {
  case LUMYN_EVENT_BEGIN_INITIALIZATION:
    return "BeginInitialization";
  case LUMYN_EVENT_FINISH_INITIALIZATION:
    return "FinishInitialization";
  case LUMYN_EVENT_ENABLED:
    return "Enabled";
  case LUMYN_EVENT_DISABLED:
    return "Disabled";
  case LUMYN_EVENT_CONNECTED:
    return "Connected";
  case LUMYN_EVENT_DISCONNECTED:
    return "Disconnected";
  case LUMYN_EVENT_ERROR:
    return "Error";
  case LUMYN_EVENT_FATAL_ERROR:
    return "FatalError";
  case LUMYN_EVENT_REGISTERED_ENTITY:
    return "RegisteredEntity";
  case LUMYN_EVENT_CUSTOM:
    return "Custom";
  case LUMYN_EVENT_PIN_INTERRUPT:
    return "PinInterrupt";
  case LUMYN_EVENT_HEARTBEAT:
    return "HeartBeat";
  case LUMYN_EVENT_OTA:
    return "OTA";
  case LUMYN_EVENT_MODULE:
    return "Module";
  default:
    return "Unknown";
  }
}

static void print_event(const lumyn_event_t *evt)
{
  if (!evt)
    return;
  printf("Event: %s", event_type_to_string(evt->type));

  switch (evt->type)
  {
  case LUMYN_EVENT_DISABLED:
    printf(" cause=%d", evt->data.disabled.cause);
    break;
  case LUMYN_EVENT_CONNECTED:
    printf(" connType=%d", evt->data.connected.type);
    break;
  case LUMYN_EVENT_DISCONNECTED:
    printf(" connType=%d", evt->data.disconnected.type);
    break;
  case LUMYN_EVENT_ERROR:
    printf(" errorType=%d msg=%s", evt->data.error.type, evt->data.error.message);
    break;
  case LUMYN_EVENT_FATAL_ERROR:
    printf(" fatalType=%d msg=%s", evt->data.fatal_error.type, evt->data.fatal_error.message);
    break;
  case LUMYN_EVENT_HEARTBEAT:
    printf(" status=%d enabled=%d usb=%d can=%d",
           evt->data.heartbeat.status,
           evt->data.heartbeat.enabled,
           evt->data.heartbeat.connected_usb,
           evt->data.heartbeat.can_ok);
    break;
  default:
    break;
  }

  if (evt->extra_message)
  {
    printf(" extra=\"%s\"", evt->extra_message);
  }
  printf("\n");
}

int main(int argc, char *argv[])
{
  const char *port = NULL;
  int list_ports_flag = 0;
  int duration_sec = 10;
  int poll_ms = 100;

  for (int i = 1; i < argc; i++)
  {
    if (strcmp(argv[i], "--port") == 0 && i + 1 < argc)
    {
      port = argv[++i];
    }
    else if (strcmp(argv[i], "--duration") == 0 && i + 1 < argc)
    {
      duration_sec = atoi(argv[++i]);
    }
    else if (strcmp(argv[i], "--poll-ms") == 0 && i + 1 < argc)
    {
      poll_ms = atoi(argv[++i]);
    }
    else if (strcmp(argv[i], "--list-ports") == 0)
    {
      list_ports_flag = 1;
    }
  }

  if (list_ports_flag)
  {
    list_ports();
    return 0;
  }

  if (!port)
  {
    printf("Error: --port is required (use --list-ports to see available ports)\n");
    return 1;
  }

  cx_t cx = {0};
  lumyn_error_t err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to create instance: %s\n", Lumyn_ErrorString(err));
    return 1;
  }

  printf("Connecting to %s...\n", port);
  err = lumyn_Connect(&cx.base, port);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to connect: %s\n", Lumyn_ErrorString(err));
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }
  printf("Connected to ConnectorX!\n");

  lumyn_connection_status_t status = lumyn_GetCurrentStatus(&cx.base);
  lumyn_status_t health = lumyn_GetDeviceHealth(&cx.base);
  printf("Current status: connected=%d enabled=%d health=%s\n",
         status.connected ? 1 : 0, status.enabled ? 1 : 0, status_to_string(health));

#define MAX_EVENTS 16
  lumyn_event_t events[MAX_EVENTS];
  int out_count = 0;

  time_t start = time(NULL);
  while ((int)(time(NULL) - start) < duration_sec)
  {
    out_count = 0;
    if (lumyn_GetEvents(&cx.base, events, MAX_EVENTS, &out_count) == LUMYN_OK)
    {
      for (int i = 0; i < out_count; ++i)
      {
        print_event(&events[i]);
      }
    }
    sleep_ms(poll_ms);
  }

  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);
  printf("Done!\n");
  return 0;
}
