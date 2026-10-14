/**
 * Simomusu93-FW: anteprima del G-code (vedi simomusu93_thumb.h).
 * Algoritmo da navaismo/Marlin_bugfix_2.1_E3V3SE (GPL-3.0), adattato a Marlin 2.0.8 / scheda C13.
 */
#include "../../inc/MarlinConfig.h"

#if ENABLED(DWIN_CREALITY_LCD) && ENABLED(SDSUPPORT)

#include "simomusu93_thumb.h"
#include "../../sd/cardreader.h"
#include "../../lcd/dwin/dwin_lcd.h"
#include <string.h>

static constexpr uint8_t THUMB_SIZE = 96;
static constexpr uint8_t HEADER_SCAN_LINES = 60;   // il blocco viene messo subito dopo l'intestazione di Creality Print

// Rettangolo di un colore: una "striscia" di pixel uguali, allungata in verticale finché le righe sotto sono uguali
struct ThumbRun {
  uint8_t x0, x1, y0, y1;   // coordinate dentro l'anteprima (0..95)
  uint16_t color;           // RGB565, 0 = sfondo (non disegnato)
};

// 1024 strisce = 6 KB di RAM. Se un'immagine ne ha di più, si disegna quello che c'è e si riparte:
// nessun pixel perso, solo qualche cambio di colore in più (navaismo usa 1536 = 9 KB; caso peggiore misurato ~1420).
static constexpr uint16_t MAX_THUMB_RUNS = 1024;
static constexpr uint8_t MAX_RUNS_PER_ROW = THUMB_SIZE / 2;  // fra due strisce c'è almeno un pixel di sfondo
static ThumbRun thumb_runs[MAX_THUMB_RUNS];
static uint8_t thumb_emitted[(MAX_THUMB_RUNS + 7) / 8];
static uint16_t open_prev[MAX_RUNS_PER_ROW], open_cur[MAX_RUNS_PER_ROW];

// Pausa ogni 10 comandi: inviati tutti di seguito riempiono il buffer dello schermo, che si blocca fino a
// spegnere la stampante (valori trovati da navaismo provando sulla C13). Sempre delay(), mai safe_delay():
// idle() farebbe ridisegnare altro allo schermo in mezzo, cambiando il colore corrente.
static void thumb_throttle() {
  static uint8_t frames = 0;
  if (++frames >= 10) { delay(16); frames = 0; }
  HAL_watchdog_refresh();   // il disegno dura qualche secondo: il watchdog scatta dopo 4 s
}

static uint16_t parse_hex4(const char *p) {
  uint16_t v = 0;
  for (uint8_t i = 0; i < 4; i++) {
    const char c = p[i];
    uint8_t n;
    if      (c >= '0' && c <= '9') n = c - '0';
    else if (c >= 'A' && c <= 'F') n = c - 'A' + 10;
    else if (c >= 'a' && c <= 'f') n = c - 'a' + 10;
    else return 0;
    v = (v << 4) | n;
  }
  return v;
}

static bool read_line(char *buf, const size_t size) {
  size_t i = 0;
  while (!card.eof()) {
    const int16_t c = card.get();
    if (c < 0) break;
    if (c == '\n' || c == '\r') { if (i == 0) continue; break; }
    if (i + 1 < size) buf[i++] = char(c);
  }
  buf[i] = '\0';
  return i > 0;
}

// Un colore alla volta: un cambio colore, poi tutti i rettangoli di quel colore
static void flush_runs(const uint16_t count, const uint16_t x, const uint16_t y) {
  memset(thumb_emitted, 0, (count + 7) / 8);
  for (uint16_t i = 0; i < count; i++) {
    if (TEST(thumb_emitted[i >> 3], i & 7)) continue;
    const uint16_t color = thumb_runs[i].color;
    DWIN_Set_Color(color, 0xFFFF);
    thumb_throttle();
    for (uint16_t j = i; j < count; j++) {
      if (TEST(thumb_emitted[j >> 3], j & 7) || thumb_runs[j].color != color) continue;
      SBI(thumb_emitted[j >> 3], j & 7);
      const ThumbRun &r = thumb_runs[j];
      DWIN_Fill_Rect_Raw(x + r.x0, y + r.y0, x + r.x1, y + r.y1);
      thumb_throttle();
    }
  }
}

bool simomusu93_render_thumb(const char *filename, const uint16_t x, const uint16_t y) {
  HAL_watchdog_refresh();
  if (card.isPrinting()) return false;   // mai durante una stampa: il file aperto è quello in stampa

  char name[FILENAME_LENGTH + 1];        // openFileRead() riscrive card.filename
  strncpy(name, filename, sizeof(name) - 1);
  name[sizeof(name) - 1] = '\0';

  card.openFileRead(name);
  if (!card.isFileOpen()) return false;

  char line[4 * THUMB_SIZE + 8];
  bool found = false;
  for (uint8_t n = 0; n < HEADER_SCAN_LINES && read_line(line, sizeof(line)); n++) {
    const char *p = line;
    if (*p++ != ';') continue;
    while (*p == ' ') p++;
    if (strncmp(p, "E3V3SE_THUMB_RAW16_BEGIN", 24) == 0) { found = true; break; }
  }

  uint8_t row = 0;
  if (found) {
    uint16_t count = 0;
    uint8_t prev_n = 0;
    while (row < THUMB_SIZE && read_line(line, sizeof(line))) {
      HAL_watchdog_refresh();
      const char *p = line;
      if (*p++ != ';') continue;
      while (*p == ' ') p++;
      if (strncmp(p, "E3V3SE_THUMB_RAW16_END", 22) == 0) break;
      if (strlen(p) < 4 * THUMB_SIZE) break;   // riga incompleta: si ferma qui

      uint8_t cur_n = 0, pi = 0;
      for (uint8_t px = 0; px < THUMB_SIZE;) {
        const uint16_t color = parse_hex4(p + px * 4);
        if (color == 0) { px++; continue; }
        uint8_t px2 = px;
        while (px2 + 1 < THUMB_SIZE && parse_hex4(p + (px2 + 1) * 4) == color) px2++;

        // Le strisce di una riga sono ordinate e separate: basta scorrere quelle della riga sopra
        while (pi < prev_n && thumb_runs[open_prev[pi]].x1 < px) pi++;
        bool merged = false;
        if (pi < prev_n) {
          ThumbRun &r = thumb_runs[open_prev[pi]];
          if (r.x0 == px && r.x1 == px2 && r.color == color) {
            r.y1 = row;
            if (cur_n < MAX_RUNS_PER_ROW) open_cur[cur_n++] = open_prev[pi];
            pi++;
            merged = true;
          }
        }
        if (!merged) {
          thumb_runs[count] = { px, px2, row, row, color };
          if (cur_n < MAX_RUNS_PER_ROW) open_cur[cur_n++] = count;
          count++;
        }
        px = px2 + 1;
      }
      memcpy(open_prev, open_cur, cur_n * sizeof(uint16_t));
      prev_n = cur_n;
      row++;

      // Una riga aggiunge al massimo MAX_RUNS_PER_ROW strisce: se non ci stanno, disegna quelle che ci sono
      if (MAX_THUMB_RUNS - count < MAX_RUNS_PER_ROW) {
        flush_runs(count, x, y);
        count = 0;
        prev_n = 0;
      }
    }
    if (count) flush_runs(count, x, y);
  }

  card.closefile();
  return row > 0;
}

#endif
