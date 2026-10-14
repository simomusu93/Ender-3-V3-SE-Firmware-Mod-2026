# Banco di prova Simomusu93-FW: controlla il firmware compilato e simula la stampa di un G-code, senza stampante.
#
# Uso (da PowerShell):
#   .\banco_prova.ps1 -Gcode "C:\percorso\file.gcode"
#   .\banco_prova.ps1 -Gcode "...\file.gcode" -Minuti 10,60,300
#
# Livello 1: verifica_firmware.py   – struttura del .bin, funzionalità presenti, memoria e stack
# Livello 2: simula_gcode.exe       – il modulo del firmware che legge il G-code, fatto girare sul file vero
# Livello 3: anteprima_schermo.py   – come apparirebbe lo schermo (originale Creality vs Simomusu93-FW)
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

Write-Output "`n===== ESITO ====="
Write-Output ("Livello 1 (firmware):   " + $(if ($l1 -eq 0) { "OK" } else { "PROBLEMI" }))
Write-Output ("Livello 2 (G-code):     " + $(if ($l2 -eq 0) { "OK" } else { "PROBLEMI" }))
Write-Output "Anteprime e CSV in:     $out"
