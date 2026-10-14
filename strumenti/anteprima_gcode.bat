@echo off
rem Simomusu93-FW: trascina uno o piu' G-code su questo file per aggiungere l'anteprima per la stampante (firmware 0.9+).
rem Il G-code viene modificato sul posto; senza anteprima dello slicer resta com'e'.
set PY=%USERPROFILE%\.venvs\pio\Scripts\python.exe
if not exist "%PY%" set PY=python
"%PY%" -I "%~dp0anteprima_gcode.py" %*
pause
