/**
 * Simomusu93-FW: vedi simomusu93_gcode_info.h
 */
#include "simomusu93_gcode_info.h"

Simomusu93GcodeInfo simomusu93_info;

void Simomusu93GcodeInfo::reset() {
  layer = layer_total = 0;
  z_um = slicer_time_s = filament_mm = 0;
  heat_done_s = r_max_s = 0;
  len = 0;
  saw_layer_change = false;
  changed = true;
}

uint32_t Simomusu93GcodeInfo::remaining_s(const uint32_t m73_R_s, const uint32_t printing_s) {
  if (m73_R_s > r_max_s) r_max_s = m73_R_s;                 // il primo M73 R è la durata totale prevista
  const uint32_t total = r_max_s ? r_max_s : slicer_time_s;
  if (!total || printing_s < 600 || m73_R_s >= total) return m73_R_s;
  const uint32_t slicer_elapsed = total - m73_R_s;          // quanto avrebbe dovuto durare fin qui secondo lo slicer
  if (slicer_elapsed < 300) return m73_R_s;
  float ratio = float(printing_s) / float(slicer_elapsed);
  if (ratio < 0.4f) ratio = 0.4f;                            // limiti di sicurezza contro valori assurdi
  if (ratio > 3.0f) ratio = 3.0f;
  return uint32_t(float(m73_R_s) * ratio);
}

void Simomusu93GcodeInfo::comment_char(const char c) {
  if (len < BUF - 1) buf[len++] = c;   // lo spazio iniziale resta (serve per "; total layer number")
}

void Simomusu93GcodeInfo::line_end() {
  if (len) {
    buf[len] = '\0';
    parse();
    len = 0;
  }
}

const char* Simomusu93GcodeInfo::after(const char *s, const char *prefix) {
  while (*prefix) if (*s++ != *prefix++) return nullptr;
  return s;
}

uint32_t Simomusu93GcodeInfo::to_uint(const char *s) {
  while (*s == ' ') s++;
  uint32_t v = 0;
  while (*s >= '0' && *s <= '9') v = v * 10 + uint32_t(*s++ - '0');
  return v;
}

uint32_t Simomusu93GcodeInfo::to_milli(const char *s) {
  while (*s == ' ') s++;
  uint32_t v = 0;
  while (*s >= '0' && *s <= '9') v = v * 10 + uint32_t(*s++ - '0');
  v *= 1000;
  if (*s == '.') {
    s++;
    uint32_t m = 100;
    while (*s >= '0' && *s <= '9' && m) { v += uint32_t(*s++ - '0') * m; m /= 10; }
  }
  return v;
}

void Simomusu93GcodeInfo::parse() {
  const char *p;
  if (after(buf, "LAYER_CHANGE")) {
    saw_layer_change = true;
    if (layer < 0xFFFF) layer++;
    changed = true;
  }
  else if ((p = after(buf, "LAYER:"))) {                  // Cura (0 = primo strato)
    if (!saw_layer_change) { layer = uint16_t(to_uint(p) + 1); changed = true; }
  }
  else if ((p = after(buf, "Z:"))) {
    z_um = to_milli(p);                                   // mm -> um
    changed = true;
  }
  else if ((p = after(buf, " total layer number:"))) {
    layer_total = uint16_t(to_uint(p)); changed = true;
  }
  else if ((p = after(buf, "LAYER_COUNT:"))) {
    layer_total = uint16_t(to_uint(p)); changed = true;
  }
  else if ((p = after(buf, "TIME:"))) {
    if (!slicer_time_s) slicer_time_s = to_uint(p);       // solo la prima (intestazione)
  }
  else if ((p = after(buf, "Filament used:"))) {
    if (!filament_mm) filament_mm = to_milli(p);          // metri -> mm
  }
}
