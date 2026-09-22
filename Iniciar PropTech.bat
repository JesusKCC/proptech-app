@echo off
title PropTech Peru - Plataforma Comercial
color 0A

cd /d "%~dp0"

echo.
echo =======================================================
echo    PROPTECH PERU - GESTION COMERCIAL DE CENTROS COMERCIALES
echo =======================================================
echo.

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.14 launcher.py
    goto :end
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python launcher.py
    goto :end
)

echo [ERROR] No se encontro Python en el sistema.
echo Por favor asegurese de tener Python instalado.
echo.

:end
echo.
echo Presione cualquier tecla para salir...
pause > nul
