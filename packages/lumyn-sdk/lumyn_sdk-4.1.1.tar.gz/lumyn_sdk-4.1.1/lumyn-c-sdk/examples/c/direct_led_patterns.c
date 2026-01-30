/**
 * @file direct_led_patterns.c
 * @brief DirectLED Pattern Animations - C Example
 *
 * Demonstrates DirectLED API with various pattern animations.
 * No external dependencies - just pattern generation.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/c/lumyn_config.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
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
  printf("  COM3\n");
#else
  printf("  /dev/ttyACM0\n");
  printf("  /dev/ttyUSB0\n");
#endif
}

static int get_zone_led_count(const char *config_json, const char *zone_id)
{
  if (!config_json || !zone_id || strlen(config_json) == 0)
  {
    return 0;
  }

  lumyn_config_t *cfg = NULL;
  lumyn_error_t err = lumyn_ParseConfig(config_json, strlen(config_json), &cfg);
  if (err != LUMYN_OK || !cfg)
  {
    fprintf(stderr, "Failed to parse device config JSON: %s\n", Lumyn_ErrorString(err));
    return 0;
  }

  int led_count = 0;
  const int channel_count = lumyn_ConfigGetChannelCount(cfg);
  for (int c = 0; c < channel_count && led_count == 0; ++c)
  {
    const lumyn_channel_t *ch = lumyn_ConfigGetChannel(cfg, c);
    const int zone_count = lumyn_ChannelGetZoneCount(ch);
    for (int z = 0; z < zone_count; ++z)
    {
      const lumyn_zone_t *zone = lumyn_ChannelGetZone(ch, z);
      if (zone && strcmp(lumyn_ZoneGetId(zone), zone_id) == 0)
      {
        led_count = lumyn_ZoneGetLedCount(zone);
        break;
      }
    }
  }

  lumyn_FreeConfig(cfg);
  return led_count;
}

static void rainbow_pattern(uint8_t *buffer, int num_leds, int offset)
{
  for (int i = 0; i < num_leds; i++)
  {
    int hue = ((i + offset) * 360 / num_leds) % 360;
    float h = hue / 60.0f;
    int c = 255;
    float x = c * (1 - fabsf(fmodf(h, 2) - 1));

    if (h < 1)
    {
      buffer[i * 3 + 0] = c;
      buffer[i * 3 + 1] = (int)(x);
      buffer[i * 3 + 2] = 0;
    }
    else if (h < 2)
    {
      buffer[i * 3 + 0] = (int)(x);
      buffer[i * 3 + 1] = c;
      buffer[i * 3 + 2] = 0;
    }
    else if (h < 3)
    {
      buffer[i * 3 + 0] = 0;
      buffer[i * 3 + 1] = c;
      buffer[i * 3 + 2] = (int)(x);
    }
    else if (h < 4)
    {
      buffer[i * 3 + 0] = 0;
      buffer[i * 3 + 1] = (int)(x);
      buffer[i * 3 + 2] = c;
    }
    else if (h < 5)
    {
      buffer[i * 3 + 0] = (int)(x);
      buffer[i * 3 + 1] = 0;
      buffer[i * 3 + 2] = c;
    }
    else
    {
      buffer[i * 3 + 0] = c;
      buffer[i * 3 + 1] = 0;
      buffer[i * 3 + 2] = (int)(x);
    }
  }
}

static void wave_pattern(uint8_t *buffer, int num_leds, int frame)
{
  for (int i = 0; i < num_leds; i++)
  {
    float wave = sinf((i + frame) * 0.2f) * 0.5f + 0.5f;
    buffer[i * 3 + 0] = (int)(wave * 255);
    buffer[i * 3 + 1] = (int)(wave * 100);
    buffer[i * 3 + 2] = (int)(wave * 50);
  }
}

static void moving_pixel(uint8_t *buffer, int num_leds, int pos)
{
  memset(buffer, 0, num_leds * 3);
  if (pos >= 0 && pos < num_leds)
  {
    buffer[pos * 3 + 0] = 255;
    buffer[pos * 3 + 1] = 255;
    buffer[pos * 3 + 2] = 255;
  }
}

int main(int argc, char *argv[])
{
  const char *port = NULL;
  const char *zone = "main";
  int num_leds = 0;
  int list_ports_flag = 0;

  for (int i = 1; i < argc; i++)
  {
    if (strcmp(argv[i], "--port") == 0 && i + 1 < argc)
    {
      port = argv[++i];
    }
    else if (strcmp(argv[i], "--zone") == 0 && i + 1 < argc)
    {
      zone = argv[++i];
    }
    else if (strcmp(argv[i], "--num-leds") == 0 && i + 1 < argc)
    {
      num_leds = atoi(argv[++i]);
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
    fprintf(stderr, "Error: --port is required (use --list-ports to see available ports)\n");
    return 1;
  }

  cx_t cx = {0};
  lumyn_error_t err;

  err = lumyn_CreateConnectorX(&cx);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed: %s\n", Lumyn_ErrorString(err));
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

  if (num_leds <= 0)
  {
    char *config_json = NULL;
    err = lumyn_RequestConfigAlloc(&cx.base, &config_json, 5000);
    if (err == LUMYN_OK && config_json)
    {
      num_leds = get_zone_led_count(config_json, zone);
      lumyn_FreeString(config_json);
    }
  }

  if (num_leds <= 0)
  {
    fprintf(stderr, "Unable to determine LED count for zone '%s'. Use --num-leds.\n", zone);
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }

  printf("Connected! Creating DirectLED for %d LEDs...\n", num_leds);

  lumyn_direct_led_t *direct_led = NULL;
  err = lumyn_DirectLEDCreate(&cx.base, zone, num_leds, 30, &direct_led);
  if (err != LUMYN_OK)
  {
    fprintf(stderr, "Failed to create DirectLED: %s\n", Lumyn_ErrorString(err));
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }

  uint8_t *buffer = (uint8_t *)malloc(num_leds * 3);
  if (!buffer)
  {
    fprintf(stderr, "Failed to allocate buffer\n");
    lumyn_DirectLEDDestroy(direct_led);
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }

  printf("\nPattern 1: Rainbow wave (10 seconds)\n");
  for (int frame = 0; frame < 100; frame++)
  {
    rainbow_pattern(buffer, num_leds, frame * 2);
    lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
    sleep_ms(100);
  }

  printf("Pattern 2: Color wave (5 seconds)\n");
  for (int frame = 0; frame < 50; frame++)
  {
    wave_pattern(buffer, num_leds, frame);
    lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
    sleep_ms(100);
  }

  printf("Pattern 3: Moving pixel (5 seconds)\n");
  for (int frame = 0; frame < num_leds * 2; frame++)
  {
    moving_pixel(buffer, num_leds, frame % num_leds);
    lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
    sleep_ms(50);
  }

  printf("Clearing...\n");
  memset(buffer, 0, num_leds * 3);
  lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);

  free(buffer);
  lumyn_DirectLEDDestroy(direct_led);
  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);

  printf("Done!\n");
  return 0;
}
