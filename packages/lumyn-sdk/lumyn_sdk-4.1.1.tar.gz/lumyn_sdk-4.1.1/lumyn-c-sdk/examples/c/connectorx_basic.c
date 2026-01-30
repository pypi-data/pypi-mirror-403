/**
 * @file connectorx_basic.c
 * @brief ConnectorX Basic Usage - C Example
 *
 * Comprehensive 1-channel examples: colors, animations, sequences.
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

#define ZONE_MAIN "main"

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

static void example_basic_colors(cx_base_t *cx)
{
  printf("\n=== Example 1: Basic Colors ===\n");

  lumyn_color_t red = {255, 0, 0};
  lumyn_color_t green = {0, 255, 0};
  lumyn_color_t blue = {0, 0, 255};
  lumyn_color_t orange = {255, 165, 0};

  printf("Setting '%s' to RED...\n", ZONE_MAIN);
  lumyn_SetColor(cx, ZONE_MAIN, red);
  sleep_ms(1000);

  printf("Setting '%s' to GREEN...\n", ZONE_MAIN);
  lumyn_SetColor(cx, ZONE_MAIN, green);
  sleep_ms(1000);

  printf("Setting '%s' to BLUE...\n", ZONE_MAIN);
  lumyn_SetColor(cx, ZONE_MAIN, blue);
  sleep_ms(1000);

  printf("Setting '%s' to ORANGE...\n", ZONE_MAIN);
  lumyn_SetColor(cx, ZONE_MAIN, orange);
  sleep_ms(1000);
}

static void example_animations(cx_base_t *cx)
{
  printf("\n=== Example 2: Built-in Animations ===\n");

  lumyn_color_t black = {0, 0, 0};
  lumyn_color_t blue = {0, 0, 255};
  lumyn_color_t red = {255, 0, 0};
  lumyn_color_t green = {0, 255, 0};
  lumyn_color_t orange = {255, 100, 0};

  printf("Running RAINBOW ROLL animation...\n");
  lumyn_SetAnimation(cx, ZONE_MAIN, LUMYN_ANIMATION_RAINBOW_ROLL, black, 50, false, false);
  sleep_ms(3000);

  printf("Running BREATHE animation (blue)...\n");
  lumyn_SetAnimation(cx, ZONE_MAIN, LUMYN_ANIMATION_BREATHE, blue, 30, false, false);
  sleep_ms(3000);

  printf("Running BLINK animation (red)...\n");
  lumyn_SetAnimation(cx, ZONE_MAIN, LUMYN_ANIMATION_BLINK, red, 500, false, false);
  sleep_ms(3000);

  printf("Running CHASE animation (green)...\n");
  lumyn_SetAnimation(cx, ZONE_MAIN, LUMYN_ANIMATION_CHASE, green, 50, false, false);
  sleep_ms(3000);

  printf("Running FIRE animation...\n");
  lumyn_SetAnimation(cx, ZONE_MAIN, LUMYN_ANIMATION_FIRE, orange, 30, false, false);
  sleep_ms(3000);
}

static void example_sequences(cx_base_t *cx)
{
  printf("\n=== Example 3: Animation Sequences ===\n");

  printf("Running 'startup' sequence...\n");
  lumyn_SetAnimationSequence(cx, ZONE_MAIN, "startup");
  sleep_ms(4000);

  printf("Running 'alliance_red' sequence...\n");
  lumyn_SetAnimationSequence(cx, ZONE_MAIN, "alliance_red");
  sleep_ms(2000);

  printf("Running 'alliance_blue' sequence...\n");
  lumyn_SetAnimationSequence(cx, ZONE_MAIN, "alliance_blue");
  sleep_ms(2000);
}

int main(int argc, char *argv[])
{
  const char *port = NULL;
  const char *example = "all";
  int list_ports_flag = 0;

  for (int i = 1; i < argc; i++)
  {
    if (strcmp(argv[i], "--port") == 0 && i + 1 < argc)
    {
      port = argv[++i];
    }
    else if (strcmp(argv[i], "--example") == 0 && i + 1 < argc)
    {
      example = argv[++i];
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

  printf("Connected successfully!\n");

  if (strcmp(example, "colors") == 0 || strcmp(example, "all") == 0)
  {
    example_basic_colors(&cx.base);
  }

  if (strcmp(example, "animations") == 0 || strcmp(example, "all") == 0)
  {
    example_animations(&cx.base);
  }

  if (strcmp(example, "sequences") == 0 || strcmp(example, "all") == 0)
  {
    example_sequences(&cx.base);
  }

  printf("\nExamples complete!\n");

  lumyn_Disconnect(&cx.base);
  lumyn_DestroyConnectorX(&cx);

  return 0;
}
