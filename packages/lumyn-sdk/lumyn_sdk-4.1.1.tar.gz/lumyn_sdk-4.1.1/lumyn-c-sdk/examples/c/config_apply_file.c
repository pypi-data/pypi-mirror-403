/**
 * @file config_apply_file.c
 * @brief Apply a configuration JSON file to a device via the C API.
 *
 * Mirrors the configuration workflow used in the Python and Java vendordeps:
 * 1. Load a JSON file (deploy/lumyn_config.json by default)
 * 2. Print or save the payload for inspection
 * 3. Use `lumyn_ApplyConfig` to push the JSON to the connected device
 *
 * Usage:
 *   config_apply_file --config deploy/lumyn_config.json --apply COM3
 */

#include <lumyn/c/lumyn_sdk.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <glob.h>
#include <unistd.h>
#endif

static char *read_text_file(const char *path, size_t *out_len)
{
    if (!path) {
        return NULL;
    }

    FILE *file = fopen(path, "rb");
    if (!file) {
        return NULL;
    }

    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }

    long length = ftell(file);
    if (length < 0) {
        fclose(file);
        return NULL;
    }
    rewind(file);

    char *buffer = (char *)malloc((size_t)length + 1);
    if (!buffer) {
        fclose(file);
        return NULL;
    }

    size_t read = fread(buffer, 1, (size_t)length, file);
    if (read != (size_t)length) {
        free(buffer);
        fclose(file);
        return NULL;
    }

    buffer[read] = '\0';
    if (out_len) {
        *out_len = read;
    }

    fclose(file);
    return buffer;
}

static void print_usage(const char *prog)
{
    printf("Usage: %s [--config <file>] [--apply <port>] [--save <file>]\n", prog);
    printf("  --config <file>  Path to JSON configuration (defaults to deploy/lumyn_config.json)\n");
    printf("  --apply <port>   Serial port to connect to (e.g., COM3 or /dev/ttyACM0)\n");
    printf("  --save <file>    Save the JSON payload to a file before applying\n");
}

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

int main(int argc, char *argv[])
{
    const char *port = NULL;
    const char *config_path = "deploy/lumyn_config.json";
    const char *save_path = NULL;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--apply") == 0 && i + 1 < argc) {
            port = argv[++i];
        } else if (strcmp(argv[i], "--config") == 0 && i + 1 < argc) {
            config_path = argv[++i];
        } else if (strcmp(argv[i], "--save") == 0 && i + 1 < argc) {
            save_path = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
    }

    size_t config_len = 0;
    char *config_json = read_text_file(config_path, &config_len);
    if (!config_json) {
        fprintf(stderr, "Failed to read configuration from %s\n", config_path);
        return 1;
    }

    if (save_path) {
        FILE *dest = fopen(save_path, "w");
        if (dest) {
            fwrite(config_json, 1, config_len, dest);
            fclose(dest);
            printf("Configuration saved to %s\n", save_path);
        } else {
            fprintf(stderr, "Unable to save configuration to %s\n", save_path);
        }
    }

    if (!port) {
        printf("Configuration payload (%zu bytes):\n", config_len);
        printf("%s\n", config_json);
        printf("\nUse --apply <port> to push the JSON to a device.\n");
        free(config_json);
        return 0;
    }

    cx_t cx = {0};
    lumyn_error_t err = lumyn_CreateConnectorX(&cx);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to create ConnectorX: %s\n", Lumyn_ErrorString(err));
        free(config_json);
        return 1;
    }

    if (!try_connect(port, &cx, &err)) {
        fprintf(stderr, "Unable to connect to %s after multiple attempts\n", port);
        lumyn_DestroyConnectorX(&cx);
        free(config_json);
        return 1;
    }

    printf("Applying configuration to %s...\n", port);
    err = lumyn_ApplyConfig(&cx.base, config_json, config_len);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to apply configuration: %s\n", Lumyn_ErrorString(err));
        lumyn_Disconnect(&cx.base);
        lumyn_DestroyConnectorX(&cx);
        free(config_json);
        return 1;
    }

    // Give the device time to finish receiving and writing the config
    printf("Waiting for device to finish writing config (~15s)...\n");
    sleep_seconds(15);

    // Verify while still connected (no reboot yet)
    char *verify_config = NULL;
    err = lumyn_RequestConfigAlloc(&cx.base, &verify_config, 20000);
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
        free(config_json);
        return 1;
    }

    printf("Requesting device restart to persist changes...\n");
    lumyn_RestartDevice(&cx.base, 1000);

    // Tear down the current instance to force a clean reconnect after reboot
    lumyn_Disconnect(&cx.base);
    lumyn_DestroyConnectorX(&cx);

    printf("Waiting for device to reboot (~20s)...\n");
    sleep_seconds(20);

    printf("Reconnecting to read back the stored configuration...\n");

    cx_t cx_after = {0};
    err = lumyn_CreateConnectorX(&cx_after);
    if (err != LUMYN_OK) {
        fprintf(stderr, "Failed to re-create ConnectorX: %s\n", Lumyn_ErrorString(err));
        free(config_json);
        return 1;
    }

    char connected_port[256] = {0};
    if (!try_connect_after_reboot(port, &cx_after, connected_port, sizeof(connected_port), &err)) {
        fprintf(stderr, "Reconnection failed after restart.\n");
        lumyn_DestroyConnectorX(&cx_after);
        free(config_json);
        return 1;
    }

    if (connected_port[0] != '\0' && strcmp(connected_port, port) != 0) {
        printf("Reconnected on %s after reboot (was %s).\n", connected_port, port);
    }

    char *device_config = NULL;
    err = lumyn_RequestConfigAlloc(&cx_after.base, &device_config, 15000);
    if (err == LUMYN_OK && device_config) {
        printf("Device reports configuration:\n%s\n", device_config);
        lumyn_FreeString(device_config);
    } else {
        fprintf(stderr, "Failed to request stored config: %s\n", Lumyn_ErrorString(err));
    }

    lumyn_Disconnect(&cx_after.base);
    lumyn_DestroyConnectorX(&cx_after);
    free(config_json);
    return 0;
}
