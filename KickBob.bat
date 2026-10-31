@echo off
chcp 65001 >nul
title KickBob - PRE ALPHA 0.0.0

where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0kickbob.py" %*
    goto :eof
)

echo Python not found, opening in Edge app mode instead...
start "" msedge --app="https://kick.com/browse?sort=featured&languages=he"
