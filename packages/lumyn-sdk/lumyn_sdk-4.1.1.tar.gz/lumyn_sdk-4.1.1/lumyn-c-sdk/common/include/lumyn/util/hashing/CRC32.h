#pragma once

#include <stddef.h>
#include <stdint.h>

static inline uint32_t crc32_init(void) { return 0xFFFFFFFFu; }

static inline uint32_t crc32_final(uint32_t crc) { return crc ^ 0xFFFFFFFFu; }

static inline uint32_t crc32_update(uint32_t crc, const uint8_t* data,
                                    size_t len) {
  while (len--) {
    crc ^= (uint32_t)(*data++);
    for (int i = 0; i < 8; ++i) {
      if (crc & 1u) {
        crc = (crc >> 1) ^ 0xEDB88320u;
      } else {
        crc >>= 1;
      }
    }
  }
  return crc;
}
