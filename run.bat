@echo off
chcp 65001 >nul
color a
title Neo Prompt Launcher
echo =========================
echo   AITISPEC - Neo Prompt
echo =========================
echo.

:: Переход в папку, где находится bat-файл
cd /d "%~dp0"

:: Проверка существования виртуального окружения
if not exist ".venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo.
    echo Запустите сначала install.ps1 -create_env
    pause
    exit /b 1
)

:: Активация окружения
call .venv\Scripts\activate.bat

:: Запуск приложения
python Neo-Prompt.py
