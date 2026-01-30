/**
 * @file modules_typed.c
 * @brief Typed Module Helpers Example - C
 *
 * Demonstrates using module callbacks for sensor data.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#define sleep_ms(ms) Sleep(ms)
#else
#include <unistd.h>
#define sleep_ms(ms) usleep((ms) * 1000)
#endif

static void digital_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  if (len >= 1)
  {
    printf("DIO state: %s\n", data[0] ? "HIGH" : "LOW");
  }
}

static void analog_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  if (len >= 2)
  {
    uint16_t raw = (data[1] << 8) | data[0];
    printf("Analog raw=%d scaled=%.2f\n", raw, raw / 1023.0);
  }
}

static void tof_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  if (len >= 3)
  {
    uint8_t valid = data[0];
    uint16_t dist = (data[2] << 8) | data[1];
    if (valid)
    {
      printf("Distance: %d mm\n", dist);
    }
  }
}

int main(int argc, char *argv[])
{
  const char *port = "/dev/ttyUSB0";
  if (argc > 1)
  {
    port = argv[1];
  }

  cx_t cx = {0};
  lumyn_error_t err;

  err = lumyn_CreateConnectorX(&cx);
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

  printf("Connected! Registering modules...\n");

  err = lumyn_RegisterModule(&cx.base, "digital-1", digital_callback, NULL);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to register digital module: %s\n", Lumyn_ErrorString(err));
  }

  err = lumyn_RegisterModule(&cx.base, "analog-1", analog_callback, NULL);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to register analog module: %s\n", Lumyn_ErrorString(err));
  }

  err = lumyn_RegisterModule(&cx.base, "tof-1", tof_callback, NULL);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to register TOF module: %s\n", Lumyn_ErrorString(err));
  }

  err = lumyn_SetModulePollingEnabled(&cx.base, true);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to enable polling: %s\n", Lumyn_ErrorString(err));
  }

  printf("Press Ctrl+C to exit...\n");
  while (1)
  {
    lumyn_PollModules(&cx.base);
    sleep_ms(500);
  }

  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);
  return 0;
}
