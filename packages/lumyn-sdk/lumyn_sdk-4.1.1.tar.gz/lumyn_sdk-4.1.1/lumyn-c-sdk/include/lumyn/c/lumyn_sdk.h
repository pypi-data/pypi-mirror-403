/**
 * @file lumyn_sdk.h
 * @brief Main Lumyn SDK header - includes all SDK functionality
 *
 * This is the main umbrella header for the Lumyn SDK. Including this header
 * provides access to all SDK functionality. For more modular inclusion,
 * you can include specific headers:
 *
 * - lumyn_common.h    - Base types, error codes, and export macros
 * - lumyn_device.h    - Device creation and connection management
 * - lumyn_events.h    - Event handling
 * - lumyn_led.h       - LED control functions
 * - lumyn_direct_led.h - High-performance DirectLED API
 * - lumyn_modules.h   - Module registration and data
 * - lumyn_modules_typed.h - Typed module helper parsers
 * - lumyn_config.h    - Configuration parsing
 */
#pragma once

// Include all modular headers
#include "lumyn_common.h"
#include "lumyn_device.h"
#include "lumyn_events.h"
#include "lumyn_led.h"
#include "lumyn_direct_led.h"
#include "lumyn_modules.h"
#include "lumyn_modules_typed.h"
#include "lumyn_config.h"
