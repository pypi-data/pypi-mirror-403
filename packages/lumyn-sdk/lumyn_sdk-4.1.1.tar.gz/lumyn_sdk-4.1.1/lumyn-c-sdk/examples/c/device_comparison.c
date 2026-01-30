/**
 * @file device_comparison.c
 * @brief Device Type Comparison - C Example
 *
 * Demonstrates differences between ConnectorX and ConnectorXAnimate.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    int list_ports_flag = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            port = argv[++i];
        } else if (strcmp(argv[i], "--list-ports") == 0) {
            list_ports_flag = 1;
        }
    }

    if (list_ports_flag) {
        list_ports();
        return 0;
    }

    if (!port) {
        printf("Usage: %s --port <port>\n", argv[0]);
        printf("\nFeature Comparison:\n");
        printf("  ConnectorX: USB + UART, LEDs + Modules\n");
        printf("  ConnectorXAnimate: USB only, LEDs only\n");
        return 1;
    }
    
    printf("\n=== ConnectorX ===\n");
    cx_t cx = {0};
    lumyn_error_t err = lumyn_CreateConnectorX(&cx);
    if (err == LUMYN_OK) {
        printf("Created ConnectorX instance\n");
        err = lumyn_Connect(&cx.base, port);
        if (err == LUMYN_OK) {
            printf("Connected successfully\n");
            printf("Features: USB + UART, LEDs + Modules\n");
            lumyn_Disconnect(&cx.base);
        }
        lumyn_DestroyConnectorX(&cx);
    }
    
    printf("\n=== ConnectorXAnimate ===\n");
    cx_animate_t cx_animate = {0};
    err = lumyn_CreateConnectorXAnimate(&cx_animate);
    if (err == LUMYN_OK) {
        printf("Created ConnectorXAnimate instance\n");
        err = lumyn_Connect(&cx_animate.base, port);
        if (err == LUMYN_OK) {
            printf("Connected successfully\n");
            printf("Features: USB only, LEDs only\n");
            lumyn_Disconnect(&cx_animate.base);
        }
        lumyn_DestroyConnectorXAnimate(&cx_animate);
    }
    
    return 0;
}
