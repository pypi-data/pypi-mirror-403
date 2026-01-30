/**
 * @file connectorx_animate.c
 * @brief ConnectorX Animate - Advanced Multi-Channel Control - C Example
 *
 * Demonstrates 4-channel control, groups, sequences.
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

#define GROUP_ALL "all_leds"
#define GROUP_FRONT "front_leds"
#define GROUP_REAR "rear_leds"

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

static void demo_zone_control(cx_base_t *cx)
{
  printf("\n=== Multi-Channel Zone Control ===\n");

  lumyn_color_t red = {255, 0, 0};
  lumyn_color_t blue = {0, 0, 255};
  lumyn_color_t green = {0, 255, 0};
  lumyn_color_t purple = {128, 0, 255};

  printf("Pattern 1: Left (red) vs Right (blue)...\n");
  lumyn_SetGroupColor(cx, "left_side", red);
  lumyn_SetGroupColor(cx, "right_side", blue);
  sleep_ms(2000);

  printf("Pattern 2: Front (green) vs Rear (purple)...\n");
  lumyn_SetGroupColor(cx, GROUP_FRONT, green);
  lumyn_SetGroupColor(cx, GROUP_REAR, purple);
  sleep_ms(2000);

  printf("Pattern 3: All zones synchronized rainbow...\n");
  lumyn_color_t black = {0, 0, 0};
  lumyn_SetGroupAnimation(cx, GROUP_ALL, LUMYN_ANIMATION_RAINBOW_CYCLE, black, 40, false, false);
  sleep_ms(4000);
}

static void demo_sequences(cx_base_t *cx)
{
  printf("\n=== Animation Sequences ===\n");

  printf("Running 'startup' sequence...\n");
  lumyn_SetGroupAnimationSequence(cx, GROUP_ALL, "startup");
  sleep_ms(4000);

  printf("Running 'alliance_red' sequence...\n");
  lumyn_SetGroupAnimationSequence(cx, GROUP_ALL, "alliance_red");
  sleep_ms(2000);

  printf("Running 'alliance_blue' sequence...\n");
  lumyn_SetGroupAnimationSequence(cx, GROUP_ALL, "alliance_blue");
  sleep_ms(2000);
}

int main(int argc, char *argv[])
{
  const char *port = NULL;
  int list_ports_flag = 0;

  for (int i = 1; i < argc; i++)
  {
    if (strcmp(argv[i], "--port") == 0 && i + 1 < argc)
    {
      port = argv[++i];
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

  cx_animate_t cx = {0};
  lumyn_error_t err;

  err = lumyn_CreateConnectorXAnimate(&cx);
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
    lumyn_DestroyConnectorXAnimate(&cx);
    return 1;
  }

  printf("Connected!\n");

  demo_zone_control(&cx.base);
  demo_sequences(&cx.base);

  printf("\n=== All demos complete! ===\n");

  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorXAnimate(&cx);

  return 0;
}
