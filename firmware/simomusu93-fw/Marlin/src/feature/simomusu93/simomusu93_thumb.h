/**
 * Simomusu93-FW: anteprima del G-code sullo schermo della V3 SE.
 *
 * Lo schermo della V3 SE non decodifica i JPG/PNG che Creality Print mette nel G-code (per questo Creality mostra
 * sempre l'omino). Lo script strumenti/anteprima_gcode.py aggiunge al G-code un blocco
 *   ; E3V3SE_THUMB_RAW16_BEGIN 96x96
 *   ; <96 pixel RGB565 in esadecimale, 4 cifre per pixel>   (96 righe)
 *   ; E3V3SE_THUMB_RAW16_END
 * e il firmware lo disegna a rettangoli pieni, raggruppati per colore.
 *
 * Formato e algoritmo (RLE per riga, fusione verticale, raggruppamento per colore, pausa ogni 10 comandi)
 * ripresi da navaismo/Marlin_bugfix_2.1_E3V3SE (GPL-3.0, Marlin/src/e3v3se/ThumbRender.cpp), adattati a Marlin 2.0.8.
 */
#pragma once

#include <stdint.h>

// Disegna l'anteprima del file con l'angolo in alto a sinistra in (x, y). false = il file non ha l'anteprima.
bool simomusu93_render_thumb(const char *filename, const uint16_t x, const uint16_t y);
