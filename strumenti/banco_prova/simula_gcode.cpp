// Banco di prova Simomusu93-FW – livello 2: simulazione della lettura di un G-code.
//
// Compila lo STESSO file del firmware (feature/simomusu93/simomusu93_gcode_info.cpp) e lo alimenta con un G-code reale,
// carattere per carattere, imitando GCodeQueue::get_sdcard_commands() / process_stream_char() di Marlin.
// Per ogni comando M73 calcola cosa mostrerebbe lo schermo:
//   - Simomusu93-FW: % e tempo rimanente dai comandi M73, strato dai commenti
//   - firmware Creality originale: % e tempo stimati dai byte letti (formula di dwin.cpp)
//
// Uso: simula_gcode <file.gcode> <out.csv>
#include "../../firmware/simomusu93-fw/Marlin/src/feature/simomusu93/simomusu93_gcode_info.cpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>

static int fail = 0;
#define CHECK(cond, ...) do { if (cond) printf("  OK    "); else { printf("  ERRORE "); fail++; } printf(__VA_ARGS__); printf("\n"); } while (0)

static bool ends_with_ci(const char *s, const char *suf) {
  const size_t a = strlen(s), b = strlen(suf);
  if (a < b) return false;
  for (size_t i = 0; i < b; i++) { char x = s[a - b + i], y = suf[i]; if (x >= 'A' && x <= 'Z') x += 32; if (x != y) return false; }
  return true;
}

int main(int argc, char **argv) {
  if (argc != 3) { printf("uso: simula_gcode <file.gcode> <out.csv>\n"); return 2; }
  // SICUREZZA: il G-code si legge soltanto. L'uscita deve essere un .csv diverso dall'ingresso,
  // e viene scritta in un file temporaneo rinominato solo alla fine (un G-code è stato sovrascritto una volta).
  if (!ends_with_ci(argv[2], ".csv") || ends_with_ci(argv[2], ".gcode") || !strcmp(argv[1], argv[2]) || !_stricmp(argv[1], argv[2])) {
    printf("RIFIUTATO: l'uscita deve essere un file .csv diverso dal G-code (ricevuto: %s)\n", argv[2]); return 3;
  }
  FILE *f = fopen(argv[1], "rb");
  if (!f) { printf("non apro %s\n", argv[1]); return 2; }
  fseek(f, 0, SEEK_END); const long size = ftell(f); fseek(f, 0, SEEK_SET);
  char tmp_csv[1024]; snprintf(tmp_csv, sizeof tmp_csv, "%s.tmp", argv[2]);
  FILE *csv = fopen(tmp_csv, "w");
  if (!csv) { printf("non creo %s\n", tmp_csv); return 2; }
  fprintf(csv, "byte_letti;perc_file;strato;totale;z_mm;m73_P;m73_R_min;tempo_trascorso_min;stima_creality_min\n");

  simomusu93_info.reset();
  // stato come in queue.cpp
  enum { NORMAL, EOL } state = NORMAL;
  char cmd[96]; int n = 0;
  long pos = 0;
  int m73_count = 0, layer_changes_seen = 0, max_layer = 0;
  long first_m73_R = -1;
  double worst_creality_ratio = 0, worst_at_min = 0;
  int c;
  uint16_t last_layer = 0; bool layer_monotonic = true;

  while ((c = fgetc(f)) != EOF) {
    pos++;
    const char ch = (char)c;
    if (ch == '\n' || ch == '\r') {
      simomusu93_info.line_end();                 // <- chiamata aggiunta in get_sdcard_commands()
      cmd[n] = 0;
      if (simomusu93_info.layer != last_layer) {
        if (simomusu93_info.layer < last_layer) layer_monotonic = false;
        last_layer = simomusu93_info.layer;
      }
      if (simomusu93_info.layer > max_layer) max_layer = simomusu93_info.layer;
      if (n >= 4 && cmd[0] == 'M' && cmd[1] == '7' && cmd[2] == '3' && cmd[3] == ' ') {
        const char *p = strchr(cmd, 'P'), *r = strchr(cmd, 'R');
        if (p && r) {
          const long P = atol(p + 1), R = atol(r + 1);
          if (first_m73_R < 0) first_m73_R = R;
          const double elapsed = double(first_m73_R - R);                       // minuti trascorsi (secondo lo slicer)
          const double frac = double(pos) / double(size);
          // dwin.cpp Creality: _remain_time = elapsed * (filesize / index) - elapsed
          const double creality = (pos > 0 && elapsed > 0) ? elapsed * (double(size) / double(pos)) - elapsed : 0;
          if (elapsed >= 30 && R > 0 && creality / R > worst_creality_ratio) { worst_creality_ratio = creality / R; worst_at_min = elapsed; }
          fprintf(csv, "%ld;%.2f;%u;%u;%.2f;%ld;%ld;%.0f;%.0f\n", pos, frac * 100, simomusu93_info.layer, simomusu93_info.layer_total,
                  simomusu93_info.z_um / 1000.0, P, R, elapsed, creality);
          m73_count++;
        }
      }
      n = 0; state = NORMAL;
      continue;
    }
    if (state == EOL) { simomusu93_info.comment_char(ch); continue; }   // <- chiamata aggiunta in get_sdcard_commands()
    if (ch == ';') { state = EOL; continue; }
    if (n < (int)sizeof(cmd) - 1) cmd[n++] = ch;
  }
  simomusu93_info.line_end();
  fclose(f); fclose(csv);
  remove(argv[2]);                                         // sostituisce il CSV precedente (solo .csv, verificato sopra)
  if (rename(tmp_csv, argv[2]) != 0) { printf("non rinomino %s\n", tmp_csv); return 2; }

  // conteggio indipendente dei ;LAYER_CHANGE per confronto
  f = fopen(argv[1], "rb"); char line[256];
  while (fgets(line, sizeof line, f)) if (!strncmp(line, ";LAYER_CHANGE", 13)) layer_changes_seen++;
  fclose(f);

  printf("File: %s (%.1f MB)\n", argv[1], size / 1048576.0);
  printf("Intestazione: totale strati %u, tempo slicer %lu s (%.1f h), filamento %.2f m\n",
         simomusu93_info.layer_total, (unsigned long)simomusu93_info.slicer_time_s, simomusu93_info.slicer_time_s / 3600.0,
         simomusu93_info.filament_mm / 1000.0);
  printf("Controlli:\n");
  CHECK(simomusu93_info.layer_total > 0, "totale strati letto dall'intestazione (%u)", simomusu93_info.layer_total);
  CHECK(max_layer == simomusu93_info.layer_total, "ultimo strato contato (%d) = totale dichiarato (%u)", max_layer, simomusu93_info.layer_total);
  CHECK(max_layer == layer_changes_seen, "strati contati (%d) = righe ;LAYER_CHANGE nel file (%d)", max_layer, layer_changes_seen);
  CHECK(layer_monotonic, "il numero di strato non torna mai indietro");
  CHECK(m73_count > 0, "comandi M73 presenti (%d): tempo e %% dallo slicer disponibili", m73_count);
  CHECK(simomusu93_info.slicer_time_s > 0, "tempo stimato dallo slicer letto (;TIME)");
  // Tempo rimanente auto-tarato (Simomusu93GcodeInfo::remaining_s) con velocità diverse dal 100%.
  // Modello: la stampa reale dura k volte quella prevista (k=0.7 circa = manopola al 160%), + 4 min di riscaldamento.
  {
    f = fopen(argv[1], "rb");
    const double ks[] = { 1.0, 0.7, 1.3 };
    for (double k : ks) {
      rewind(f); double worst = 0, worst_raw = 0; long R0 = -1;
      simomusu93_info.r_max_s = 0;                                   // come a inizio stampa
      while (fgets(line, sizeof line, f)) {
        if (strncmp(line, "M73 ", 4)) continue;
        const char *r = strchr(line, 'R'); if (!r) continue;
        const long R = atol(r + 1); if (R0 < 0) R0 = R;
        const double printing_s = (R0 - R) * 60.0 * k;           // tempo di stampa reale (riscaldamento escluso)
        const double est = simomusu93_info.remaining_s(uint32_t(R * 60), uint32_t(printing_s)); // chiamata a ogni M73, come nel firmware
        if (printing_s < 15 * 60 || R < 10) continue;            // si valuta dopo 15 min, esclusi gli ultimi minuti
        const double truth = R * 60.0 * k;
        const double err = fabs(est - truth) / truth, err_raw = fabs(R * 60.0 - truth) / truth;
        if (err > worst) worst = err;
        if (err_raw > worst_raw) worst_raw = err_raw;
      }
      CHECK(worst < 0.10, "velocità x%.2f: errore massimo del tempo rimanente %.0f%% (senza auto-taratura %.0f%%)", 1.0 / k, worst * 100, worst_raw * 100);
    }
    fclose(f);
  }

  if (worst_creality_ratio > 0)
    printf("Confronto: la stima del firmware Creality originale arriva a %.1f volte il tempo reale rimanente (dopo %.0f min di stampa)\n",
           worst_creality_ratio, worst_at_min);
  printf("Risultato: %s\n", fail ? "PROBLEMI TROVATI" : "TUTTO OK");
  return fail ? 1 : 0;
}
