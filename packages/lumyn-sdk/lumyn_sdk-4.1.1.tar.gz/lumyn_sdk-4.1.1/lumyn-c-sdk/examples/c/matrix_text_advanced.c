/**
 * @file matrix_text_advanced.c
 * @brief Matrix Text (Advanced) - C Example
 *
 * Demonstrates advanced matrix text features: fonts, alignment, smooth scrolling,
 * ping-pong, background color, and vertical offset.
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

static void list_ports(void) {
    printf("Available serial ports:\n");
#ifdef _WIN32
    printf("  COM3\n");
#else
    printf("  /dev/ttyACM0\n");
    printf("  /dev/ttyUSB0\n");
#endif
}

int main(int argc, char* argv[]) {
    const char* port = NULL;
    const char* zone = "matrix_display";
    int list_ports_flag = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            port = argv[++i];
        } else if (strcmp(argv[i], "--zone") == 0 && i + 1 < argc) {
            zone = argv[++i];
        } else if (strcmp(argv[i], "--list-ports") == 0) {
            list_ports_flag = 1;
        }
    }

    if (list_ports_flag) {
        list_ports();
        return 0;
    }

    if (!port) {
        fprintf(stderr, "Error: --port is required (use --list-ports to see available ports)\n");
        return 1;
    }

    cx_t cx = {0};
    lumyn_error_t err = lumyn_CreateConnectorX(&cx);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to create ConnectorX: %s\n", Lumyn_ErrorString(err));
        return 1;
    }

    printf("Connecting to %s...\n", port);
    err = lumyn_Connect(&cx.base, port);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to connect: %s\n", Lumyn_ErrorString(err));
        lumyn_DestroyConnectorX(&cx);
        return 1;
    }

    printf("Connected.\n");
    printf("Using matrix zone: %s\n", zone);

    // Example 1: Smooth scrolling with background, font, and ping-pong
    printf("Example 1: smooth scrolling, ping-pong, background\n");
    lumyn_matrix_text_flags_t flags1 = {0};
    flags1.smoothScroll = 1;
    flags1.pingPong = 1;
    lumyn_SetTextAdvanced(
        &cx.base, zone, "HELLO LUMYN", (lumyn_color_t){255, 200, 0},
        LUMYN_MATRIX_TEXT_SCROLL_LEFT, 30, false,
        (lumyn_color_t){10, 10, 40},
        LUMYN_MATRIX_TEXT_FONT_FREE_SANS_BOLD_12,
        LUMYN_MATRIX_TEXT_ALIGN_LEFT,
        flags1, 0);

    sleep_ms(6000);

    // Example 2: Static centered text with alignment + y offset
    printf("Example 2: static centered text with offset\n");
    lumyn_matrix_text_flags_t flags2 = {0};
    flags2.noScroll = 1;
    lumyn_SetTextAdvanced(
        &cx.base, zone, "STATIC", (lumyn_color_t){0, 255, 120},
        LUMYN_MATRIX_TEXT_SCROLL_LEFT, 50, false,
        (lumyn_color_t){0, 0, 0},
        LUMYN_MATRIX_TEXT_FONT_TOM_THUMB,
        LUMYN_MATRIX_TEXT_ALIGN_CENTER,
        flags2, (int8_t)-2);

    sleep_ms(4000);

    // Example 3: Classic scrolling without background
    printf("Example 3: classic scrolling\n");
    lumyn_matrix_text_flags_t flags3 = {0};
    lumyn_SetTextAdvanced(
        &cx.base, zone, "GOOD LUCK!", (lumyn_color_t){255, 0, 0},
        LUMYN_MATRIX_TEXT_SCROLL_RIGHT, 60, false,
        (lumyn_color_t){0, 0, 0},
        LUMYN_MATRIX_TEXT_FONT_BUILTIN,
        LUMYN_MATRIX_TEXT_ALIGN_LEFT,
        flags3, 0);

    sleep_ms(6000);

    printf("Done.\n");

    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    return 0;
}
