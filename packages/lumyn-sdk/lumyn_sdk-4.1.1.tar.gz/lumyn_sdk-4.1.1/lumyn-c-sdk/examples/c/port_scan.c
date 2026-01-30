/**
 * @file port_scan.c
 * @brief Port Scanning Utility - C Example
 *
 * Scans common serial ports and attempts handshake.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <glob.h>
#endif

static int try_handshake(const char* port) {
    cx_t cx = {0};
    lumyn_error_t err;
    
    err = lumyn_CreateConnectorX(&cx);
    if (err != LUMYN_OK) return 0;
    
    err = lumyn_Connect(&cx.base, port);
    if (err == LUMYN_OK) {
        lumyn_Disconnect(&cx.base);
        lumyn_DestroyConnectorX(&cx);
        return 1;
    }
    
    lumyn_DestroyConnectorX(&cx);
    return 0;
}

int main(void) {
    printf("Scanning for ConnectorX on common ports...\n");
    
#ifdef _WIN32
    const char* ports[] = {"COM1", "COM3", "COM4", "COM5", NULL};
    for (int i = 0; ports[i]; i++) {
        printf("Trying %s ... ", ports[i]);
        int ok = try_handshake(ports[i]);
        printf("%s\n", ok ? "ok" : "no");
    }
#else
    glob_t glob_result;
    glob("/dev/ttyACM*", GLOB_NOSORT, NULL, &glob_result);
    glob("/dev/ttyUSB*", GLOB_NOSORT | GLOB_APPEND, NULL, &glob_result);
    
    int any_success = 0;
    for (size_t i = 0; i < glob_result.gl_pathc; i++) {
        printf("Trying %s ... ", glob_result.gl_pathv[i]);
        int ok = try_handshake(glob_result.gl_pathv[i]);
        printf("%s\n", ok ? "ok" : "no");
        any_success |= ok;
    }
    globfree(&glob_result);
    
    if (!any_success) {
        printf("No device responded on common ports.\n");
        return 1;
    }
#endif
    
    return 0;
}
