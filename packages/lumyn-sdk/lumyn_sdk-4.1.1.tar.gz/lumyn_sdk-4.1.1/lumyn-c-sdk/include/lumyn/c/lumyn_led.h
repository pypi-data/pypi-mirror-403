/**
 * @file lumyn_led.h
 * @brief LED control functions
 *
 * This header contains functions for controlling LEDs on Lumyn devices,
 * including colors, animations, image sequences, and text.
 */
#pragma once

#include "lumyn_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

  // =============================================================================
  // Basic Color Control
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_SetColor(cx_base_t *inst, const char *zone_id, lumyn_color_t color);
  LUMYN_SDK_API lumyn_error_t lumyn_SetGroupColor(cx_base_t *inst, const char *group_id, lumyn_color_t color);

  // =============================================================================
  // Animation Control
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_SetAnimation(
      cx_base_t *inst,
      const char *zone_id,
      lumyn_animation_t animation,
      lumyn_color_t color,
      uint32_t delay_ms,
      bool reversed,
      bool one_shot);

  LUMYN_SDK_API lumyn_error_t lumyn_SetGroupAnimation(
      cx_base_t *inst,
      const char *group_id,
      lumyn_animation_t animation,
      lumyn_color_t color,
      uint32_t delay_ms,
      bool reversed,
      bool one_shot);

  LUMYN_SDK_API lumyn_error_t lumyn_SetAnimationSequence(cx_base_t *inst, const char *zone_id, const char *sequence_id);
  LUMYN_SDK_API lumyn_error_t lumyn_SetGroupAnimationSequence(cx_base_t *inst, const char *group_id, const char *sequence_id);

  // =============================================================================
  // Image Sequence Control
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_SetImageSequence(
      cx_base_t *inst,
      const char *zone_id,
      const char *sequence_id,
      lumyn_color_t color,
      bool set_color,
      bool one_shot);

  LUMYN_SDK_API lumyn_error_t lumyn_SetGroupImageSequence(
      cx_base_t *inst,
      const char *group_id,
      const char *sequence_id,
      lumyn_color_t color,
      bool set_color,
      bool one_shot);

  // =============================================================================
  // Text Control
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_SetText(
      cx_base_t *inst,
      const char *zone_id,
      const char *text,
      lumyn_color_t color,
      lumyn_matrix_text_scroll_direction_t direction,
      uint32_t delay_ms,
      bool one_shot);

  LUMYN_SDK_API lumyn_error_t lumyn_SetGroupText(
      cx_base_t *inst,
      const char *group_id,
      const char *text,
      lumyn_color_t color,
      lumyn_matrix_text_scroll_direction_t direction,
      uint32_t delay_ms,
      bool one_shot);

  LUMYN_SDK_API lumyn_error_t lumyn_SetTextAdvanced(
      cx_base_t *inst,
      const char *zone_id,
      const char *text,
      lumyn_color_t color,
      lumyn_matrix_text_scroll_direction_t direction,
      uint32_t delay_ms,
      bool one_shot,
      lumyn_color_t bg_color,
      lumyn_matrix_text_font_t font,
      lumyn_matrix_text_align_t align,
      lumyn_matrix_text_flags_t flags,
      int8_t y_offset);

  LUMYN_SDK_API lumyn_error_t lumyn_SetGroupTextAdvanced(
      cx_base_t *inst,
      const char *group_id,
      const char *text,
      lumyn_color_t color,
      lumyn_matrix_text_scroll_direction_t direction,
      uint32_t delay_ms,
      bool one_shot,
      lumyn_color_t bg_color,
      lumyn_matrix_text_font_t font,
      lumyn_matrix_text_align_t align,
      lumyn_matrix_text_flags_t flags,
      int8_t y_offset);

  // =============================================================================
  // Direct Buffer Control (Low-level)
  // =============================================================================

  LUMYN_SDK_API lumyn_error_t lumyn_CreateDirectBuffer(cx_base_t *inst, const char *zone_id, size_t buffer_length, int full_refresh_interval_ms);
  LUMYN_SDK_API lumyn_error_t lumyn_UpdateDirectBuffer(cx_base_t *inst, const char *zone_id, const uint8_t *data, size_t length, bool delta);

#ifdef __cplusplus
} // extern "C"
#endif
