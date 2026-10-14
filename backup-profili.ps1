# Copia i profili utente di Creality Print nella cartella profili/ del progetto (solo lettura su Creality Print).
# Uso: powershell -ExecutionPolicy Bypass -File backup-profili.ps1

$crealityRoot = Join-Path $env:APPDATA "Creality\Creality Print"
$versione = Get-ChildItem $crealityRoot -Directory | Where-Object { $_.Name -match '^\d+(\.\d+)*$' } |
    Sort-Object { [version]($_.Name + '.0' * (3 - ($_.Name.Split('.').Count - 1))) } | Select-Object -Last 1
if (-not $versione) { Write-Error "Creality Print non trovato in $crealityRoot"; exit 1 }

$userDir = Join-Path $versione.FullName "user"
$destinazione = Join-Path $PSScriptRoot "profili"
$mappa = @{ machine = "stampante"; filament = "filamenti"; process = "processo" }

$copiati = 0
Get-ChildItem $userDir -Directory | ForEach-Object {
    foreach ($tipo in $mappa.Keys) {
        $src = Join-Path $_.FullName $tipo
        if (-not (Test-Path $src)) { continue }
        Get-ChildItem $src -File -Filter *.json | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $destinazione $mappa[$tipo]) -Force
            $copiati++
        }
    }
}
Write-Output "Creality Print $($versione.Name): copiati $copiati profili in $destinazione"
