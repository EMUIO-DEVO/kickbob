@echo off
chcp 65001 >nul
title Build KickBob EXE (PRE ALPHA 0.0.4)
cd /d "%~dp0"

where python >nul 2>nul
if not %errorlevel%==0 (
    echo Python is not installed. Install it from https://www.python.org/downloads/ ^(check "Add Python to PATH"^)
    pause
    exit /b 1
)

echo Installing build requirements...
python -m pip install --upgrade pyinstaller pywebview || goto :fail

echo Building KickBob.exe ...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name KickBob ^
  --icon kickbob.ico ^
  --add-data "kickbob.ico;." ^
  kickbob.py || goto :fail

copy /y "dist\KickBob.exe" "KickBob_PRE_ALPHA_0.0.4.exe" >nul

echo.
echo Done! Your EXE is here:
echo   %~dp0KickBob_PRE_ALPHA_0.0.4.exe
pause
exit /b 0

:fail
echo.
echo Build failed. See the messages above.
pause
exit /b 1
