# Guida: caricare Simomusu93-FW e tornare al firmware originale

Stampante: Creality Ender-3 V3 SE · scheda **CR4NS200320C13** (chip GD32F303). [English version](UPDATE-GUIDE.md).

| File | Dove |
|---|---|
| Firmware nuovo | `firmware/build/Simomusu93-FW_0.9.bin` |
| Firmware originale (backup) | `firmware/originale-creality-1.1.0/Ender3 V3 SE GD303SWV1.1.0_HWCR4NS200320C13_20250422.bin` |

---

## 0. Prima di iniziare (una volta sola)

1. **Aspetta che la stampa in corso sia finita.**
2. **Controlla la scheda**: menu **Controllo → Info**. In fondo, alla voce versione hardware, deve comparire **CR4NS200320C13**.
   ✅ Verificato il 14/10/2026: scheda CR4NS200320C13, firmware attuale V1.0.7 (il backup 1.1.0 ufficiale è più recente: va bene).
   Se c'è scritto **C14** (o F401): **fermati**, questo firmware non è per la tua scheda.
3. **Annota** (o fotografa) la schermata Info e lo **Z-offset** attuale (dalla foto del 13/10: circa **−1,06**).
4. **Recupera `KRATOS FINAL.gcode`** dalla microSD e rimettilo in Download (era stato sovrascritto sul PC).
5. Prepara una **microSD dedicata** all'aggiornamento (va bene anche quella della stampante, ma meglio vuota):
   - formattata **FAT32** (tasto destro sull'unità in Esplora file → Formatta → FAT32);
   - tieni sul PC anche il firmware originale, per poter tornare indietro in qualsiasi momento.

## 1. Caricare Simomusu93-FW

1. Copia `Simomusu93-FW_0.9.bin` nella **cartella principale** della microSD (non dentro altre cartelle).
2. **Rinominalo con un nome mai usato prima**: massimo 8 lettere/numeri, **senza spazi e senza altri punti**, ad esempio `fw09.bin`.
   Nomi come `sm93_0.8.bin` (due punti) non vanno: Windows li salva con un nome corto tipo `SM93_0~1.BIN`, uguale per 0.6, 0.7, 0.8…,
   e il bootloader li scambia per il firmware già installato (successo il 14/10/2026).
   Il bootloader ignora un file con un nome già installato: ogni volta usa un nome nuovo (`fw09b.bin`, …).
3. Rimuovi la microSD dal PC in sicurezza (icona "Rimozione sicura").
4. **Spegni la stampante** con l'interruttore.
5. Inserisci la microSD nello slot della stampante.
6. **Accendi** e **non toccare niente per almeno 30 secondi**: il bootloader copia il firmware (10–15 s di solito).
   Lo schermo può restare nero o fermo in questo tempo: è normale.
   **Non spegnere durante questa fase.**
7. Quando compare il menu, vai in **Controllo → Info**: deve esserci **`Simomusu93 0.9`**.
   Se c'è ancora la versione vecchia: il file non è stato letto → rinominalo con un altro nome nuovo e ripeti dal punto 4.
8. Togli la microSD e cancella il `.bin` (o lascialo: con lo stesso nome non verrà reinstallato).

## 2. Dopo il primo avvio (obbligatorio)

Il firmware nuovo **azzera le impostazioni salvate** (Z-offset, livellamento, PID) quando arrivi dal firmware Creality o da 0.1/0.2. La lingua resta.
Dalla 0.3 in poi le impostazioni restano: basta controllare lo Z-offset.

1. **Livellamento → Z-offset automatico** (la sonda di pressione misura l'ugello).
2. **Livellamento → livellamento automatico del piatto** (griglia 4×4).
3. **Controllo → Salva impostazioni**.
4. Confronta lo Z-offset con quello annotato: se è molto diverso (più di ~0,2 mm), ripeti il punto 1.

## 3. Prove (resta vicino alla stampante)

Usa i file di `modelli/miei/test-firmware/` (istruzioni nel README di quella cartella):

1. **Cubo 20 mm** (≈20 min): riscaldamento stabile, stampa regolare, fine stampa normale.
2. **Torre M73** (≈1 h): tempo rimanente vicino a quello di Creality Print, riga **"Strato X/Y"** che cresce.
3. **Menu Controllo**, in fondo: **Statistiche** (apri e torna), **Suono** (Sì↔No), **Sensore filo** (Sì↔No),
   **Reset**: un solo clic → compare "Clic ancora: RESET" → **gira la manopola** per annullare (non fare il secondo clic).
   Scendi fino all'ultima voce e risali fino a "Indietro": ogni voce deve comparire una sola volta.
4. **Controllo → Info**: annota "RAM libera min" (riga gialla al posto di "Contattaci") appena acceso e dopo la torre.

Se qualcosa non va (riscaldamento strano, blocchi, scritte sovrapposte): **spegni** e passa al punto 4.
Una foto dello schermo aiuta a capire il problema.

## 3b. Anteprima del G-code (dalla 0.9)

La stampante mostra l'immagine del modello nella schermata di conferma solo se il G-code contiene il blocco dell'anteprima. Per aggiungerlo:
- **in automatico**: in Creality Print, impostazioni del Processo → *Altro* (vista avanzata/esperto) → **Script di post-elaborazione**, scrivi
  `"C:\Users\<utente>\.venvs\pio\Scripts\python.exe" "<cartella del progetto>\strumenti\anteprima_gcode.py";` (con i tuoi percorsi)
  e ogni G-code esportato avrà l'anteprima;
- **a mano**: trascina uno o più G-code sul file `strumenti/anteprima_gcode.bat`.
Senza il blocco resta l'omino di Creality. Il disegno dura 1–4 secondi (nel titolo compare "Anteprima...").

## 4. Tornare al firmware originale (backup)

Il pacchetto ufficiale del sito Creality (`…HWCR4NS200320C13C14_SWV1.1.0_GD303STM32F401.rar`) contiene due file:
quello nella cartella principale, `…GD303…HWCR4NS200320C13….bin`, è per la scheda **C13**; quello in `STM32F4_UPDATE/` è per la C14: **non copiarlo**.

Stessa procedura del punto 1, con il file originale:

1. Copia `Ender3 V3 SE GD303SWV1.1.0_HWCR4NS200320C13_20250422.bin` nella cartella principale della microSD.
2. Rinominalo con un **nome nuovo**, ad esempio `orig110.bin`.
3. Stampante **spenta** → inserisci la microSD → **accendi** → aspetta 30 secondi senza toccare.
4. **Controllo → Info**: deve comparire la versione Creality (es. V1.1.0).
5. Anche qui le impostazioni vengono azzerate: rifai **Z-offset automatico**, **livellamento** e **Salva**.

Il bootloader (la parte che legge la microSD all'accensione) **non viene mai sovrascritto** da questi file:
per questo si può sempre rimettere il firmware originale.

## Problemi comuni

| Cosa succede | Cosa fare |
|---|---|
| La versione in Info non cambia | Nome del `.bin` già usato o file non nella cartella principale → nome nuovo, ripeti |
| Schermo nero per più di 2 minuti | Spegni, controlla che la SD sia FAT32 e il file sia quello giusto, riprova con nome nuovo; altrimenti carica il firmware originale |
| Errore di livellamento / Z-offset | Rifai Z-offset automatico prima del livellamento; ugello pulito |
| Qualunque dubbio | Torna all'originale (punto 4): è sempre possibile |
