/**
 * @file modules_from_config.c
 * @brief Module discovery + typed helpers example (C)
 *
 * Reads the device config, discovers modules, registers typed parsers,
 * and prints module data as it arrives.
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

static const char *connection_type_to_string(lumyn_module_connection_type_t type)
{
  switch (type)
  {
  case LUMYN_MODULE_CONNECTION_I2C:
    return "I2C";
  case LUMYN_MODULE_CONNECTION_SPI:
    return "SPI";
  case LUMYN_MODULE_CONNECTION_UART:
    return "UART";
  case LUMYN_MODULE_CONNECTION_DIO:
    return "DIO";
  case LUMYN_MODULE_CONNECTION_AIO:
    return "AIO";
  default:
    return "Unknown";
  }
}

static void digital_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  (void)user;
  lumyn_digital_input_payload_t payload;
  if (!lumyn_ParseDigitalInputPayload(data, len, &payload))
    return;
  printf("[%s] DIO state: %s\n", module_id, payload.state ? "HIGH" : "LOW");
}

static void analog_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  (void)user;
  lumyn_analog_input_payload_t payload;
  if (!lumyn_ParseAnalogInputPayload(data, len, &payload))
    return;
  printf("[%s] Analog raw=%u scaled=%u\n", module_id, payload.raw_value, payload.scaled_value);
}

static void tof_callback(const char *module_id, const uint8_t *data, size_t len, void *user)
{
  (void)user;
  lumyn_vl53l1x_payload_t payload;
  if (!lumyn_ParseVL53L1XPayload(data, len, &payload))
    return;
  if (payload.valid)
  {
    printf("[%s] Distance: %u mm\n", module_id, payload.dist_mm);
  }
}

int main(int argc, char *argv[])
{
  const char *port = NULL;

  for (int i = 1; i < argc; ++i)
  {
    if (strcmp(argv[i], "--port") == 0 && i + 1 < argc)
    {
      port = argv[++i];
    }
    else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0)
    {
      printf("Usage: %s --port <serial port>\n", argv[0]);
      return 0;
    }
  }

  if (!port)
  {
    fprintf(stderr, "Error: --port is required\n");
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

  printf("Connected!\n");

  char *config_json = NULL;
  err = lumyn_RequestConfigAlloc(&cx.base, &config_json, 5000);
  if (err != LUMYN_OK || !config_json || config_json[0] == '\0')
  {
    fprintf(stderr, "Failed to read device config: %s\n", Lumyn_ErrorString(err));
    lumyn_FreeString(config_json);
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }

  lumyn_config_t *config = NULL;
  err = lumyn_ParseConfig(config_json, strlen(config_json), &config);
  if (err != LUMYN_OK || !config)
  {
    fprintf(stderr, "Failed to parse device config: %s\n", Lumyn_ErrorString(err));
    lumyn_FreeString(config_json);
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }

  int module_count = lumyn_ConfigGetModuleCount(config);
  if (module_count == 0)
  {
    printf("No modules found in device config.\n");
    lumyn_FreeConfig(config);
    lumyn_FreeString(config_json);
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 0;
  }

  printf("Modules in config: %d\n", module_count);
  int poll_interval_ms = 10;
  for (int i = 0; i < module_count; ++i)
  {
    const lumyn_module_t *module = lumyn_ConfigGetModule(config, i);
    const char *id = lumyn_ModuleGetId(module);
    const char *type = lumyn_ModuleGetType(module);
    uint16_t poll_ms = lumyn_ModuleGetPollingRateMs(module);
    lumyn_module_connection_type_t conn = lumyn_ModuleGetConnectionType(module);

    printf("  - id=%s type=%s pollingRateMs=%u connection=%s\n",
           id ? id : "(null)",
           type ? type : "(null)",
           poll_ms,
           connection_type_to_string(conn));

    (void)poll_ms;

    if (!id || !type)
      continue;

    if (strcmp(type, "DigitalInput") == 0)
    {
      lumyn_RegisterModule(&cx.base, id, digital_callback, NULL);
    }
    else if (strcmp(type, "AnalogInput") == 0)
    {
      lumyn_RegisterModule(&cx.base, id, analog_callback, NULL);
    }
    else if (strcmp(type, "VL53L1X") == 0)
    {
      lumyn_RegisterModule(&cx.base, id, tof_callback, NULL);
    }
    else
    {
      printf("  (skipping unsupported module type)\n");
    }
  }

  lumyn_SetModulePollingEnabled(&cx.base, true);

  printf("Polling every %d ms. Press Ctrl+C to exit...\n", poll_interval_ms);
  while (1)
  {
    lumyn_PollModules(&cx.base);
    sleep_ms(poll_interval_ms);
  }

  lumyn_FreeConfig(config);
  lumyn_FreeString(config_json);
  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);
  return 0;
}
