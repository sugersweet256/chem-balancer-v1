@echo off
chcp 65001 >nul
cd /d "%~dp0"
for /f "delims=" %%i in ('python -c "import pathlib, PySide6; print(pathlib.Path(PySide6.__file__).parent / 'designer.exe')"') do set "DESIGNER=%%i"
if not exist "%DESIGNER%" (
    echo 没有找到 Qt Designer。
    echo 请确认已安装 PySide6：python -m pip install PySide6
    pause
    exit /b 1
)
start "" "%DESIGNER%" "%~dp0src\ui\main_window.ui"
