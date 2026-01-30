/**
 * @file quickstart.c
 * @brief ConnectorX Quick Start - C Example
 *
 * The simplest example to get started with ConnectorX LEDs.
 *
 * Usage:
 *     ./quickstart_c --port /dev/ttyACM0
 *     ./quickstart_c --port COM3 --zone zone_0
 *     ./quickstart_c --list-ports
 */

#include <lumyn/c/lumyn_config.h>
#include <lumyn/c/lumyn_sdk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#define sleep_ms(ms) Sleep(ms)
#else
#include <unistd.h>
#include <time.h>
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

static const char *skip_ws(const char *s)
{
  while (s && *s && (*s == ' ' || *s == '\n' || *s == '\r' || *s == '\t'))
  {
    s++;
  }
  return s;
}

static int extract_string_value(const char *obj, const char *key, char *out, size_t out_size)
{
  char needle[64];
  snprintf(needle, sizeof(needle), "\"%s\"", key);
  const char *p = strstr(obj, needle);
  if (!p)
    return 0;
  p = strchr(p + strlen(needle), ':');
  if (!p)
    return 0;
  p = skip_ws(p + 1);
  if (*p != '"')
    return 0;
  p++;
  const char *end = strchr(p, '"');
  if (!end)
    return 0;
  size_t len = (size_t)(end - p);
  if (len + 1 > out_size)
    len = out_size - 1;
  memcpy(out, p, len);
  out[len] = '\0';
  return 1;
}

static int extract_int_value(const char *obj, const char *key, int *out)
{
  char needle[64];
  snprintf(needle, sizeof(needle), "\"%s\"", key);
  const char *p = strstr(obj, needle);
  if (!p)
    return 0;
  p = strchr(p + strlen(needle), ':');
  if (!p)
    return 0;
  p = skip_ws(p + 1);
  *out = atoi(p);
  return 1;
}

static int extract_bool_value(const char *obj, const char *key, int *out)
{
  char needle[64];
  snprintf(needle, sizeof(needle), "\"%s\"", key);
  const char *p = strstr(obj, needle);
  if (!p)
    return 0;
  p = strchr(p + strlen(needle), ':');
  if (!p)
    return 0;
  p = skip_ws(p + 1);
  if (strncmp(p, "true", 4) == 0)
  {
    *out = 1;
    return 1;
  }
  if (strncmp(p, "false", 5) == 0)
  {
    *out = 0;
    return 1;
  }
  return 0;
}

static int extract_zone_object(const char *json, const char *zone_id, char *out, size_t out_size)
{
  if (!json || !zone_id || !out || out_size == 0)
    return 0;

  char id_key[128];
  snprintf(id_key, sizeof(id_key), "\"id\"");
  const char *p = json;
  while ((p = strstr(p, id_key)) != NULL)
  {
    const char *id_val = strchr(p + strlen(id_key), ':');
    if (!id_val)
      break;
    id_val = skip_ws(id_val + 1);
    if (*id_val != '"')
    {
      p += 4;
      continue;
    }
    id_val++;
    const char *id_end = strchr(id_val, '"');
    if (!id_end)
      break;
    if ((size_t)(id_end - id_val) == strlen(zone_id) &&
        strncmp(id_val, zone_id, id_end - id_val) == 0)
    {
      // find object start
      int depth = 0;
      const char *start = p;
      for (const char *b = p; b >= json; --b)
      {
        if (*b == '}')
          depth++;
        if (*b == '{')
        {
          if (depth == 0)
          {
            start = b;
            break;
          }
          depth--;
        }
        if (b == json)
          break;
      }
      // find object end
      depth = 0;
      const char *end = start;
      for (const char *f = start; *f; ++f)
      {
        if (*f == '{')
          depth++;
        if (*f == '}')
        {
          depth--;
          if (depth == 0)
          {
            end = f;
            break;
          }
        }
      }
      size_t len = (size_t)(end - start + 1);
      if (len >= out_size)
        len = out_size - 1;
      memcpy(out, start, len);
      out[len] = '\0';
      return 1;
    }
    p = id_end + 1;
  }
  return 0;
}

static int format_zone_python_dict(const char *json, const char *zone_id, char *out, size_t out_size)
{
  char obj[2048];
  if (!extract_zone_object(json, zone_id, obj, sizeof(obj)))
    return 0;

  char type[32] = "";
  extract_string_value(obj, "type", type, sizeof(type));
  int brightness = 0;
  int has_brightness = extract_int_value(obj, "brightness", &brightness);

  if (strcmp(type, "matrix") == 0)
  {
    int rows = 0, cols = 0;
    extract_int_value(obj, "rows", &rows);
    extract_int_value(obj, "cols", &cols);
    char corner_tb[32] = "";
    char corner_lr[32] = "";
    char axis_layout[32] = "";
    char seq_layout[32] = "";
    extract_string_value(obj, "cornerTopBottom", corner_tb, sizeof(corner_tb));
    extract_string_value(obj, "cornerLeftRight", corner_lr, sizeof(corner_lr));
    extract_string_value(obj, "axisLayout", axis_layout, sizeof(axis_layout));
    extract_string_value(obj, "sequenceLayout", seq_layout, sizeof(seq_layout));

    if (has_brightness)
    {
      snprintf(out, out_size,
               "{'id': '%s', 'type': 'matrix', 'rows': %d, 'cols': %d, 'brightness': %d, "
               "'orientation': {'cornerTopBottom': '%s', 'cornerLeftRight': '%s', 'axisLayout': '%s', 'sequenceLayout': '%s'}}",
               zone_id, rows, cols, brightness, corner_tb, corner_lr, axis_layout, seq_layout);
    }
    else
    {
      snprintf(out, out_size,
               "{'id': '%s', 'type': 'matrix', 'rows': %d, 'cols': %d, "
               "'orientation': {'cornerTopBottom': '%s', 'cornerLeftRight': '%s', 'axisLayout': '%s', 'sequenceLayout': '%s'}}",
               zone_id, rows, cols, corner_tb, corner_lr, axis_layout, seq_layout);
    }
    return 1;
  }

  int length = 0;
  int reversed = 0;
  extract_int_value(obj, "length", &length);
  extract_bool_value(obj, "reversed", &reversed);
  if (has_brightness)
  {
    snprintf(out, out_size,
             "{'id': '%s', 'type': 'strip', 'length': %d, 'brightness': %d, 'reversed': %s}",
             zone_id, length, brightness, reversed ? "True" : "False");
  }
  else
  {
    snprintf(out, out_size,
             "{'id': '%s', 'type': 'strip', 'length': %d, 'reversed': %s}",
             zone_id, length, reversed ? "True" : "False");
  }
  return 1;
}

static int get_zone_led_count(const char *config_json, const char *zone_id)
{
  if (!config_json || !zone_id || strlen(config_json) == 0)
  {
    return 0;
  }

  lumyn_config_t *cfg = NULL;
  lumyn_error_t err = lumyn_ParseConfig(config_json, strlen(config_json), &cfg);
  if (err != LUMYN_OK)
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
        char zone_buf[1024];
        if (format_zone_python_dict(config_json, zone_id, zone_buf, sizeof(zone_buf)))
        {
          printf("Found zone: %s\n", zone_buf);
        }
        break;
      }
    }
  }

  lumyn_FreeConfig(cfg);
  return led_count;
}

int main(int argc, char *argv[])
{
  const char *port = NULL;
  const char *zone = "zone_0";
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
    printf("Failed to connect!\n");
    printf("Use --list-ports to see available serial ports\n");
    lumyn_DestroyConnectorX(&cx);
    return 1;
  }

  printf("Connected to ConnectorX!\n");

  char *config_json = NULL;
  err = lumyn_RequestConfigAlloc(&cx.base, &config_json, 5000);
  if (err == LUMYN_OK && config_json && strlen(config_json) > 0)
  {
    printf("Config on device: %s\n", config_json);
  }
  else if (err == LUMYN_OK)
  {
    printf("Config on device: None\n");
  }
  else
  {
    printf("Failed to read device config: %s\n", Lumyn_ErrorString(err));
  }

  int num_leds = 0;

  lumyn_color_t red = {255, 0, 0};
  lumyn_color_t green = {0, 150, 0};
  lumyn_color_t blue = {0, 0, 255};
  lumyn_color_t purple = {128, 0, 255};
  lumyn_color_t orange = {255, 128, 0};
  lumyn_color_t black = {0, 0, 0};

  printf("Red breathe animation...\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_BREATHE, red, 10, false, false);
  sleep_ms(6000);

  printf("Green plasma animation...\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_PLASMA, green, 100, false, false);
  sleep_ms(3000);

  printf("Blue chase animation...\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_CHASE, blue, 50, false, false);
  sleep_ms(5000);

  printf("Purple comet animation...\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_COMET, purple, 20, false, false);
  sleep_ms(3000);

  printf("Orange sparkle animation...\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_SPARKLE, orange, 100, false, false);
  sleep_ms(3000);

  printf("Rainbow roll animation...\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_RAINBOW_CYCLE, black, 50, false, false);
  sleep_ms(3000);

  printf("\nDirect LED buffer test with DirectLED...\n");

  num_leds = get_zone_led_count(config_json, zone);

  if (num_leds > 0)
  {
    printf("Zone '%s' has %d LEDs\n", zone, num_leds);
  }
  else
  {
    printf("Could not find zone '%s' in config\n", zone);
  }

  if (num_leds > 0)
  {
    lumyn_direct_led_t *direct_led = NULL;
    err = lumyn_DirectLEDCreate(&cx.base, zone, num_leds, 10, &direct_led);
    if (err != LUMYN_OK)
    {
      fprintf(stderr, "Failed to create DirectLED: %s\n", Lumyn_ErrorString(err));
    }
    else
    {
      uint8_t *buffer = (uint8_t *)malloc(num_leds * 3);
      if (buffer)
      {
        for (int i = 0; i < num_leds; i++)
        {
          buffer[i * 3 + 0] = 255;
          buffer[i * 3 + 1] = 0;
          buffer[i * 3 + 2] = 0;
        }
        printf("Frame 0: Setting all LEDs to RED (auto: full buffer)...\n");
        lumyn_DirectLEDForceFullUpdateRaw(direct_led, buffer, num_leds * 3);
        sleep_ms(1000);

        for (int i = 0; i < num_leds; i++)
        {
          buffer[i * 3 + 0] = 0;
          buffer[i * 3 + 1] = 255;
          buffer[i * 3 + 2] = 0;
        }
        printf("Frame 1: Setting all LEDs to GREEN (auto: delta)...\n");
        lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
        sleep_ms(1000);

        for (int i = 0; i < num_leds; i++)
        {
          if (i % 2 == 0)
          {
            buffer[i * 3 + 0] = 255;
            buffer[i * 3 + 1] = 0;
            buffer[i * 3 + 2] = 0;
          }
          else
          {
            buffer[i * 3 + 0] = 0;
            buffer[i * 3 + 1] = 0;
            buffer[i * 3 + 2] = 255;
          }
        }
        printf("Frame 2: Setting alternating RED/BLUE (auto: delta)...\n");
        lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
        sleep_ms(1000);

        printf("Frames 3-12: Moving white pixel (auto: delta for frames 3-9, full at frame 10)...\n");
        for (int frame = 3; frame < 13; frame++)
        {
          for (int i = 0; i < num_leds; i++)
          {
            if (i == (frame - 3) % num_leds)
            {
              buffer[i * 3 + 0] = 255;
              buffer[i * 3 + 1] = 255;
              buffer[i * 3 + 2] = 255;
            }
            else
            {
              buffer[i * 3 + 0] = 0;
              buffer[i * 3 + 1] = 0;
              buffer[i * 3 + 2] = 0;
            }
          }
          lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
          sleep_ms(100);
        }

        printf("Filling with black\n");
        memset(buffer, 0, num_leds * 3);
        lumyn_DirectLEDUpdateRaw(direct_led, buffer, num_leds * 3);
        sleep_ms(1000);

        free(buffer);
      }

      lumyn_DirectLEDDestroy(direct_led);
    }
  }

  printf("\nOff\n");
  lumyn_SetAnimation(&cx.base, zone, LUMYN_ANIMATION_FILL, black, 0, false, true);
  sleep_ms(1000);

  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);

  if (config_json)
  {
    lumyn_FreeString(config_json);
  }

  printf("Done!\n");
  return 0;
}
