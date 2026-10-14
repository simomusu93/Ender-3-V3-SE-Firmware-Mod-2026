/**
 * Simomusu93-FW: misuratore della RAM libera minima (stack + heap) – "stack painting".
 *
 * All'avvio la RAM non usata, tra la cima dell'heap e lo stack, viene riempita con 0xA5.
 * Più tardi si cerca il punto più basso in cui lo stack ha scritto: tutto ciò che è ancora 0xA5
 * sopra la cima attuale dell'heap non è MAI stato usato. Quello è il margine reale.
 */
#include "simomusu93_ram.h"

#ifdef __arm__

extern "C" void* _sbrk(int incr);

static uint8_t *paint_lo = nullptr, *paint_hi = nullptr;
static const uint8_t PATTERN = 0xA5;

static inline uint8_t* current_sp() {
  uint8_t *sp;
  __asm__ volatile ("mov %0, sp" : "=r"(sp));
  return sp;
}

void simomusu93_ram_paint() {
  paint_lo = (uint8_t*)_sbrk(0);
  paint_hi = current_sp() - 256;            // lascia stare lo stack in uso adesso
  for (uint8_t *p = paint_lo; p < paint_hi; ++p) *p = PATTERN;
}

uint32_t simomusu93_ram_free_min() {
  if (!paint_lo || paint_hi <= paint_lo) return 0;
  uint8_t *p = (uint8_t*)_sbrk(0);           // l'heap può essere cresciuto dopo il riempimento
  if (p < paint_lo) p = paint_lo;
  uint8_t *start = p;
  while (p < paint_hi && *p == PATTERN) ++p; // primo byte toccato dallo stack nel suo punto più profondo
  return uint32_t(p - start);
}

uint32_t simomusu93_ram_painted() {
  return (paint_lo && paint_hi > paint_lo) ? uint32_t(paint_hi - paint_lo) : 0;
}

#else // compilazione sul PC (banco di prova)

void simomusu93_ram_paint() {}
uint32_t simomusu93_ram_free_min() { return 0; }
uint32_t simomusu93_ram_painted() { return 0; }

#endif
