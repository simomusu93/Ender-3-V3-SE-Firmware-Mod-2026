/**
 * Simomusu93-FW: informazioni lette dai commenti del G-code durante la stampa da SD.
 *
 * Riconosce (Creality Print / OrcaSlicer / Cura):
 *   ;LAYER_CHANGE                 -> strato + 1
 *   ;LAYER:n                      -> strato = n + 1   (Cura, numerazione da 0)
 *   ; total layer number: N       -> totale strati    (Creality Print / Orca)
 *   ;LAYER_COUNT:N                -> totale strati    (Cura)
 *   ;Z:12.4                       -> altezza corrente (usata se il totale non è noto, es. ripresa dopo blackout)
 *   ;TIME:50986.40                -> tempo stimato dallo slicer, secondi
 *   ;Filament used:92.99225m      -> filamento previsto
 *
 * Volutamente senza dipendenze da Marlin: lo stesso file viene compilato anche sul PC
 * dal banco di prova (strumenti/banco_prova) e fatto girare sui G-code reali.
 */
#pragma once

#include <stdint.h>

class Simomusu93GcodeInfo {
public:
  uint16_t layer;          // strato corrente, 1 = primo; 0 = non ancora noto
  uint16_t layer_total;    // totale strati; 0 = non noto
  uint32_t z_um;           // ultima altezza ";Z:" in micrometri; 0 = non nota
  uint32_t slicer_time_s;  // tempo stimato dallo slicer
  uint32_t filament_mm;    // filamento previsto in mm
  bool changed;            // c'è qualcosa di nuovo da mostrare (lo azzera chi disegna)
  uint32_t heat_done_s;    // secondi di stampa al termine del PRIMO riscaldamento (0 = non ancora)
  uint32_t r_max_s;        // R più grande visto (= durata totale prevista dallo slicer)

  void reset();

  // Tempo rimanente "auto-tarato": il tempo M73 R dello slicer (calcolato al 100% di velocità) moltiplicato per
  // il rapporto tra tempo reale di stampa e tempo previsto dallo slicer fino a ora. Si adatta a velocità diverse
  // dal 100% (es. 160% dalla manopola), accelerazioni reali, pause brevi. Prima di 10 min di stampa usa R così com'è.
  // Va chiamata a ogni aggiornamento: ricorda anche il primo (= più grande) R come durata totale prevista.
  uint32_t remaining_s(const uint32_t m73_R_s, const uint32_t printing_s);
  void comment_char(const char c);   // un carattere che si trova dopo ';' sulla riga
  void line_end();                   // fine della riga (con o senza commento)

private:
  static const uint8_t BUF = 32;
  char buf[BUF];
  uint8_t len;
  bool saw_layer_change;

  void parse();
  static const char* after(const char *s, const char *prefix);   // s inizia con prefix? -> resto, altrimenti nullptr
  static uint32_t to_uint(const char *s);
  static uint32_t to_milli(const char *s);                       // "12.345" -> 12345
};

extern Simomusu93GcodeInfo simomusu93_info;
