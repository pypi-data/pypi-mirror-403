/**
 * @file handshake_basic.c
 * @brief Basic Handshake Example - C
 *
 * Demonstrates low-level handshake protocol.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/c/serial_io.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char* argv[]) {
    const char* port = NULL;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            port = argv[++i];
        }
    }

    if (!port) {
        printf("Usage: %s --port <port>\n", argv[0]);
        return 1;
    }
    
    cx_t cx = {0};
    lumyn_error_t err;
    
    err = lumyn_CreateConnectorX(&cx);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to create instance: %s\n", Lumyn_ErrorString(err));
        return 1;
    }
    
    printf("Connecting to %s...\n", port);
    err = lumyn_Connect(&cx.base, port);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to connect: %s\n", Lumyn_ErrorString(err));
        lumyn_DestroyConnectorX(&cx);
        return 1;
    }
    
    printf("Connected! Handshake completed automatically.\n");
    printf("Device is ready for commands.\n");
    
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);
    
    return 0;
}
