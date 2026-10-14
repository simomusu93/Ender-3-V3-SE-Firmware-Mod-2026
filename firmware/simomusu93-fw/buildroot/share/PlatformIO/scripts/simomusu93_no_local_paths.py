#
# Simomusu93-FW: toglie dal firmware il nome utente del PC su cui è compilato.
# Gli assert del framework usano __FILE__, che contiene per esempio "C:\Users\<nome>\.platformio\packages\...".
# Il GCC di questa toolchain non ha -fmacro-prefix-map, quindi dopo la compilazione il nome viene sostituito
# nel .bin con "x" della stessa lunghezza: nessun byte si sposta, cambia solo il testo dei messaggi di assert.
#
import os
Import("env")

def _strip_user(source, target, env):
    home = os.path.expanduser("~")
    name = os.path.basename(home.rstrip("\\/"))
    if not name:
        return
    for t in target:
        path = str(t)
        data = open(path, "rb").read()
        new = data
        for sep in ("\\", "/"):
            old = ("Users" + sep + name + sep).encode()
            new = new.replace(old, ("Users" + sep + "x" * len(name) + sep).encode())
        if new != data:
            assert len(new) == len(data)
            open(path, "wb").write(new)
            print("Simomusu93-FW: nome utente tolto dai percorsi nel firmware")

env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", _strip_user)
