#
# Simomusu93-FW: il framework maple per STM32F1 aggiunge -Wl,--warn-unresolved-symbols, che trasforma una funzione
# mancante in un semplice avviso: il firmware viene creato lo stesso e la chiamata salta all'indirizzo 0.
# (Così è nato il bug di navaismo su kill_screen().) Qui togliamo l'opzione: una funzione mancante = errore.
#
Import("env")

flags = env.get("LINKFLAGS", [])
env.Replace(LINKFLAGS=[f for f in flags if f != "-Wl,--warn-unresolved-symbols"])
print("Simomusu93-FW: link rigoroso attivo (funzioni mancanti = errore)")
