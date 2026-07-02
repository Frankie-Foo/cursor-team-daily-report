@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo Cursor 统一日报 - 一键安装
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_oneclick.ps1"
if errorlevel 1 pause
