# Banco di prova Simomusu93-FW: controlla il firmware compilato e simula la stampa di un G-code, senza stampante.
#
# Uso (da PowerShell):
#   .\banco_prova.ps1 -Gcode "C:\percorso\file.gcode"
#   .\banco_prova.ps1 -Gcode "...\file.gcode" -Minuti 10,60,300
#
# Livello 1: verifica_firmware.py   – struttura del .bin, funzionalità presenti, memoria e stack
# Livello 2: simula_gcode.exe       – il modulo del firmware che legge il G-code, fatto girare sul file vero
# Livello 3: anteprima_schermo.py   – come apparirebbe lo schermo (originale Creality vs Simomusu93-FW)
# Livello 4: simula_anteprima.exe   – il codice dell'anteprima del firmware disegna su uno schermo finto (0.9)
param(
  [Parameter(Mandatory = $true)][string]$Gcode,
  [string]$Bin   = "",   # vuoto = il Simomusu93-FW_*.bin più recente in firmware\build
  [string]$Build = "",   # vuoto = %PLATFORMIO_BUILD_DIR% (o %USERPROFILE%\.pio-build\simomusu93) + \STM32F103RET6_creality
  [double[]]$Minuti = @(30, 120, 0)
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
if (-not $Bin) {
  $Bin = (Get-ChildItem (Join-Path $here "..\..\firmware\build\Simomusu93-FW_*.bin") | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
if (-not $Build) {
  $root = if ($env:PLATFORMIO_BUILD_DIR) { $env:PLATFORMIO_BUILD_DIR } else { Join-Path $env:USERPROFILE ".pio-build\simomusu93" }
  $Build = Join-Path $root "STM32F103RET6_creality"
}
# Python con PlatformIO, ziglang e pillow: %SIMOMUSU93_PY% oppure il venv in %USERPROFILE%\.venvs\pio
$py = if ($env:SIMOMUSU93_PY) { $env:SIMOMUSU93_PY } else { Join-Path $env:USERPROFILE ".venvs\pio\Scripts\python.exe" }
$nome = [IO.Path]::GetFileNameWithoutExtension($Gcode)
$out  = Join-Path $here "risultati\$nome"
New-Item -ItemType Directory -Force $out | Out-Null

Write-Output "===== LIVELLO 1: firmware ====="
& $py -I (Join-Path $here "verifica_firmware.py") $Build $Bin
$l1 = $LASTEXITCODE

Write-Output "`n===== LIVELLO 2: simulazione G-code ====="
$exe = Join-Path $here "simula_gcode.exe"
$src = Join-Path $here "simula_gcode.cpp"
$fw  = Join-Path $here "..\..\firmware\simomusu93-fw\Marlin\src\feature\simomusu93\simomusu93_gcode_info.cpp"
if (-not (Test-Path $exe) -or (Get-Item $src).LastWriteTime -gt (Get-Item $exe).LastWriteTime -or (Get-Item $fw).LastWriteTime -gt (Get-Item $exe).LastWriteTime) {
  Write-Output "(ricompilo il simulatore con il codice attuale del firmware)"
  Push-Location $here; & $py -m ziglang c++ -O2 -std=c++17 -w -o simula_gcode.exe simula_gcode.cpp 2>$null; Pop-Location
}
$csv = Join-Path $out "risultati.csv"
& $exe $Gcode $csv
$l2 = $LASTEXITCODE

Write-Output "`n===== LIVELLO 3: anteprime schermo ====="
# 0 = metà stampa
$tot = (Import-Csv $csv -Delimiter ';' | Select-Object -First 1).m73_R_min
$m = $Minuti | ForEach-Object { if ($_ -eq 0) { [math]::Round([double]$tot / 2) } else { $_ } }
& $py (Join-Path $here "anteprima_schermo.py") $csv $nome $out @m

Write-Output "`n===== LIVELLO 4: anteprima del file (0.9) ====="
# Copia del G-code con il blocco dell'anteprima (lo script lavora sempre su una copia, mai sul file originale)
$stub = Join-Path $here "anteprima_stub\feature\simomusu93"
New-Item -ItemType Directory -Force $stub | Out-Null
$fwdir = Join-Path $here "..\..\firmware\simomusu93-fw\Marlin\src\feature\simomusu93"
Copy-Item (Join-Path $fwdir "simomusu93_thumb.cpp"), (Join-Path $fwdir "simomusu93_thumb.h") $stub -Force
$gthumb = Join-Path $out "con_anteprima.gcode"
Copy-Item $Gcode $gthumb -Force
& $py -I (Join-Path $here "..\anteprima_gcode.py") $gthumb
Push-Location $here; & $py -m ziglang c++ -O1 -std=c++17 -w -o simula_anteprima.exe simula_anteprima.cpp anteprima_stub\feature\simomusu93\simomusu93_thumb.cpp 2>$null; Pop-Location
$rawf = Join-Path $out "anteprima_disegnata.raw"
if (-not (Select-String -Path $gthumb -Pattern "E3V3SE_THUMB_RAW16_BEGIN" -SimpleMatch -Quiet)) {
  Write-Output "(il G-code non contiene un'anteprima dello slicer: sulla stampante resterà l'omino)"
  $l4 = 0
} else {
  & (Join-Path $here "simula_anteprima.exe") $gthumb $rawf
  $l4 = $LASTEXITCODE
}
if ($l4 -eq 0 -and (Test-Path $rawf)) { & $py -I (Join-Path $here "verifica_anteprima.py") $gthumb $rawf (Join-Path $out "anteprima_disegnata.png"); $l4 = $LASTEXITCODE }
# Stessa anteprima nel formato BTT_TFT (quello che Creality Print scrive da solo con "96x96/BTT_TFT"), in cima al file
if ($l4 -eq 0 -and (Select-String -Path $Gcode -Pattern "png begin 96*96" -SimpleMatch -Quiet)) {
  $gbtt = Join-Path $out "con_anteprima_btt.gcode"
  & $py -I (Join-Path $here "verifica_anteprima.py") --crea-btt $Gcode $gbtt
  & (Join-Path $here "simula_anteprima.exe") $gbtt $rawf
  $l4 = $LASTEXITCODE
  if ($l4 -eq 0) { & $py -I (Join-Path $here "verifica_anteprima.py") $gbtt $rawf (Join-Path $out "anteprima_disegnata_btt.png"); $l4 = $LASTEXITCODE }
  Remove-Item $gbtt -ErrorAction SilentlyContinue
}
Remove-Item $gthumb, $rawf -ErrorAction SilentlyContinue

Write-Output "`n===== ESITO ====="
Write-Output ("Livello 1 (firmware):   " + $(if ($l1 -eq 0) { "OK" } else { "PROBLEMI" }))
Write-Output ("Livello 2 (G-code):     " + $(if ($l2 -eq 0) { "OK" } else { "PROBLEMI" }))
Write-Output ("Livello 4 (anteprima):  " + $(if ($l4 -eq 0) { "OK" } else { "PROBLEMI (o file senza anteprima)" }))
Write-Output "Anteprime e CSV in:     $out"
