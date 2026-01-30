/**
 * @file config_builder_basic.c
 * @brief Configuration Builder - Basic Example - C
 *
 * Demonstrates creating device configuration programmatically.
 * Since C SDK doesn't have a fluent builder API, we build JSON strings.
 */

#include <lumyn/c/lumyn_sdk.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <glob.h>
#include <unistd.h>
#endif

static void sleep_seconds(unsigned seconds)
{
#ifdef _WIN32
    Sleep(seconds * 1000);
#else
    sleep(seconds);
#endif
}

static bool try_connect(const char *port, cx_t *cx, lumyn_error_t *out_err)
{
    const int max_attempts = 20;
    for (int attempt = 1; attempt <= max_attempts; ++attempt) {
        *out_err = lumyn_Connect(&cx->base, port);
        if (*out_err == LUMYN_OK) {
            return true;
        }
        fprintf(stderr, "Connect attempt %d/%d failed: %s\n", attempt, max_attempts, Lumyn_ErrorString(*out_err));
        sleep_seconds(2);
    }
    return false;
}

static bool try_connect_port(const char *port, cx_t *cx, lumyn_error_t *out_err)
{
    if (!port || !*port) {
        return false;
    }
    *out_err = lumyn_Connect(&cx->base, port);
    return *out_err == LUMYN_OK;
}

#ifndef _WIN32
static int enumerate_ports(char ports[][256], int max_ports)
{
    if (max_ports <= 0) {
        return 0;
    }

    glob_t glob_result;
    memset(&glob_result, 0, sizeof(glob_result));
    glob("/dev/ttyACM*", GLOB_NOSORT, NULL, &glob_result);
    glob("/dev/ttyUSB*", GLOB_NOSORT | GLOB_APPEND, NULL, &glob_result);

    int count = 0;
    for (size_t i = 0; i < glob_result.gl_pathc && count < max_ports; ++i) {
        const char *path = glob_result.gl_pathv[i];
        if (!path) {
            continue;
        }
        strncpy(ports[count], path, sizeof(ports[count]) - 1);
        ports[count][sizeof(ports[count]) - 1] = '\0';
        count++;
    }

    globfree(&glob_result);
    return count;
}
#endif

static bool try_connect_after_reboot(const char *preferred_port,
                                     cx_t *cx,
                                     char *out_port,
                                     size_t out_port_size,
                                     lumyn_error_t *out_err)
{
    const int max_attempts = 20;
    for (int attempt = 1; attempt <= max_attempts; ++attempt) {
        if (preferred_port && try_connect_port(preferred_port, cx, out_err)) {
            snprintf(out_port, out_port_size, "%s", preferred_port);
            return true;
        }

#ifdef _WIN32
        for (int i = 1; i <= 20; ++i) {
            char candidate[16];
            snprintf(candidate, sizeof(candidate), "COM%d", i);
            if (preferred_port && strcmp(candidate, preferred_port) == 0) {
                continue;
            }
            if (try_connect_port(candidate, cx, out_err)) {
                snprintf(out_port, out_port_size, "%s", candidate);
                return true;
            }
        }
#else
        char ports[64][256];
        int port_count = enumerate_ports(ports, 64);
        for (int i = 0; i < port_count; ++i) {
            if (preferred_port && strcmp(ports[i], preferred_port) == 0) {
                continue;
            }
            if (try_connect_port(ports[i], cx, out_err)) {
                snprintf(out_port, out_port_size, "%s", ports[i]);
                return true;
            }
        }
#endif

        fprintf(stderr, "Reconnect attempt %d/%d failed: %s\n",
                attempt, max_attempts, Lumyn_ErrorString(*out_err));
        sleep_seconds(2);
    }

    return false;
}

static const char* create_basic_config_json(void) {
    return "{"
        "\"team\": \"9999\","
        "\"network\": {\"mode\": \"USB\"},"
        "\"channels\": {"
            "\"1\": {"
                "\"id\": \"1\","
                "\"length\": 144,"
                "\"brightness\": 255,"
                "\"zones\": ["
                    "{"
                        "\"id\": \"main\","
                        "\"type\": \"strip\","
                        "\"length\": 144,"
                        "\"brightness\": 100"
                    "}"
                "]"
            "}"
        "},"
        "\"groups\": ["
            "{"
                "\"id\": \"all_leds\","
                "\"zoneIds\": [\"main\"]"
            "}"
        "],"
        "\"sequences\": ["
            "{"
                "\"id\": \"startup\","
                "\"steps\": ["
                    "{"
                        "\"animationId\": \"FadeIn\","
                        "\"color\": {\"r\": 0, \"g\": 255, \"b\": 0},"
                        "\"delay\": 30,"
                        "\"reversed\": false,"
                        "\"repeat\": 1"
                    "},"
                    "{"
                        "\"animationId\": \"Fill\","
                        "\"color\": {\"r\": 0, \"g\": 255, \"b\": 0},"
                        "\"delay\": -1,"
                        "\"reversed\": false,"
                        "\"repeat\": 0"
                    "}"
                "]"
            "}"
        "]"
    "}";
}

int main(int argc, char* argv[]) {
    const char* port = NULL;
    int save_only = 0;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--apply") == 0 && i + 1 < argc) {
            port = argv[++i];
        } else if (strcmp(argv[i], "--save") == 0 && i + 1 < argc) {
            FILE* f = fopen(argv[++i], "w");
            if (f) {
                fprintf(f, "%s\n", create_basic_config_json());
                fclose(f);
                printf("Configuration saved to %s\n", argv[i]);
            }
            save_only = 1;
        }
    }
    
    if (save_only) {
        return 0;
    }
    
    printf("Configuration JSON:\n");
    printf("%s\n", create_basic_config_json());
    
    if (port) {
        printf("\nApplying configuration to device at %s...\n", port);
        
        cx_t cx = {0};
        lumyn_error_t err;
        
        err = lumyn_CreateConnectorX(&cx);
        if (err != LUMYN_OK) {
            fprintf(stderr, "Failed: %s\n", Lumyn_ErrorString(err));
            return 1;
        }
        
        if (!try_connect(port, &cx, &err)) {
            fprintf(stderr, "Failed to connect to %s\n", port);
            lumyn_DestroyConnectorX(&cx);
            return 1;
        }
        
        const char* config_json = create_basic_config_json();
        err = lumyn_ApplyConfig(&cx.base, config_json, strlen(config_json));
        if (err != LUMYN_OK) {
            fprintf(stderr, "Failed to apply configuration: %s\n", Lumyn_ErrorString(err));
            lumyn_Disconnect(&cx.base);
            lumyn_DestroyConnectorX(&cx);
            return 1;
        }
        
        printf("Waiting for device to finish writing config (~8s)...\n");
        sleep_seconds(8);

        char* verify_config = NULL;
        err = lumyn_RequestConfigAlloc(&cx.base, &verify_config, 15000);
        if (err == LUMYN_OK && verify_config) {
            if (strcmp(verify_config, config_json) == 0) {
                printf("On-wire verification: device echoed the applied config before reboot.\n");
            } else {
                printf("Warning: device responded with a different config before reboot (length %zu vs %zu).\n",
                       strlen(verify_config), strlen(config_json));
            }
            lumyn_FreeString(verify_config);
        } else {
            fprintf(stderr, "Pre-restart config read failed: %s (aborting restart)\n", Lumyn_ErrorString(err));
            lumyn_Disconnect(&cx.base);
            lumyn_DestroyConnectorX(&cx);
            return 1;
        }

        printf("Requesting device restart to persist changes...\n");
        lumyn_RestartDevice(&cx.base, 1000);

        lumyn_Disconnect(&cx.base);
        lumyn_DestroyConnectorX(&cx);

        printf("Waiting for device to reboot (~20s)...\n");
        sleep_seconds(20);

        printf("Reconnecting to read back the stored configuration...\n");

        cx_t cx_after = {0};
        err = lumyn_CreateConnectorX(&cx_after);
        if (err != LUMYN_OK) {
            fprintf(stderr, "Failed to re-create ConnectorX: %s\n", Lumyn_ErrorString(err));
            return 1;
        }

        char connected_port[256] = {0};
        if (!try_connect_after_reboot(port, &cx_after, connected_port, sizeof(connected_port), &err)) {
            fprintf(stderr, "Reconnection failed after restart.\n");
            lumyn_DestroyConnectorX(&cx_after);
            return 1;
        }

        if (connected_port[0] != '\0' && strcmp(connected_port, port) != 0) {
            printf("Reconnected on %s after reboot (was %s).\n", connected_port, port);
        }

        char* device_config = NULL;
        err = lumyn_RequestConfigAlloc(&cx_after.base, &device_config, 15000);
        if (err == LUMYN_OK && device_config) {
            printf("Device reports configuration:\n%s\n", device_config);
            lumyn_FreeString(device_config);
        } else {
            fprintf(stderr, "Failed to request stored config: %s\n", Lumyn_ErrorString(err));
        }

        lumyn_Disconnect(&cx_after.base);
        lumyn_DestroyConnectorX(&cx_after);
    } else {
        printf("\nUse --apply <port> to send to device or --save <file> to save JSON\n");
    }
    
    return 0;
}
