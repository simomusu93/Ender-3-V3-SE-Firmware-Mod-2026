// Banco di prova Simomusu93-FW – livello 4: il codice dell'anteprima del firmware (feature/simomusu93/simomusu93_thumb.cpp,
// copiato in anteprima_stub/ da banco_prova.ps1) disegna su uno schermo 240x320 finto; salva i pixel e conta i comandi.
// Uso: simula_anteprima.exe <file.gcode> <uscita.raw>
#include "anteprima_stub/inc/MarlinConfig.h"
#include "anteprima_stub/sd/cardreader.h"
#include "anteprima_stub/feature/simomusu93/simomusu93_thumb.h"
#include <vector>

FILE *CardReader::f = nullptr; long CardReader::size = 0, CardReader::pos = 0; bool CardReader::printing = false;
CardReader card;

static uint16_t screen[320][240];
static uint16_t cur = 0;
static long sets = 0, fills = 0, pauses = 0, overdraw = 0;
static std::vector<std::vector<int>> hits(320, std::vector<int>(240, 0));

void delay(unsigned long) { pauses++; }
void HAL_watchdog_refresh() {}
void DWIN_Set_Color(uint16_t fc, uint16_t) { cur = fc; sets++; }
void DWIN_Fill_Rect_Raw(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1) {
  fills++;
  for (int y = y0; y <= y1; y++) for (int x = x0; x <= x1; x++) { if (hits[y][x]++) overdraw++; screen[y][x] = cur; }
}

int main(int argc, char **argv) {
  if (argc < 3) { printf("uso: simula_anteprima <file.gcode> <uscita.raw>\n"); return 2; }
  const bool ok = simomusu93_render_thumb(argv[1], 72, 25);   // stessa posizione dell'omino Creality

  FILE *o = fopen(argv[2], "wb");   // 96x96 valori RGB565 (little endian) dell'area dell'anteprima
  for (int y = 25; y < 121; y++) for (int x = 72; x < 168; x++) fwrite(&screen[y][x], 2, 1, o);
  fclose(o);

  long outside = 0;
  for (int y = 0; y < 320; y++) for (int x = 0; x < 240; x++) if (hits[y][x] && (x < 72 || x >= 168 || y < 25 || y >= 121)) outside++;
  // Tempo: ~2,7 ms per comando misurati da navaismo sulla C13 (1030 comandi = 2,75 s, pause comprese)
  printf("  %s  anteprima trovata e disegnata: %ld cambi colore + %ld rettangoli (%ld pause), circa %.1f s sullo schermo\n",
         ok ? "OK   " : "ERRORE", sets, fills, pauses, (sets + fills) * 0.0027);
  printf("  %s  nessun pixel disegnato due volte (%ld) e niente fuori dall'area 96x96 (%ld)\n",
         overdraw == 0 && outside == 0 ? "OK   " : "ERRORE", overdraw, outside);
  return ok && overdraw == 0 && outside == 0 ? 0 : 1;
}
