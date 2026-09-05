@echo off
chcp 65001 >nul
echo ========================================
echo   万能媒体浏览器 - 打包脚本
echo ========================================
echo.

setlocal enabledelayedexpansion

:: 设置Python
set PYTHON=py -3.12

:: 清理旧的构建
echo [1/5] 清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist MediaBrowser.spec del /q MediaBrowser.spec

:: 提取VLC运行时
echo [2/5] 提取VLC运行时...
if exist vlc-temp rmdir /s /q vlc-temp
mkdir vlc-temp
powershell -Command "Expand-Archive -Path 'vlc-portable.zip' -DestinationPath 'vlc-temp' -Force"

:: 找到VLC目录（可能在vlc-3.0.21下）
set VLC_DIR=
for /d %%D in (vlc-temp\*) do (
    if exist "%%D\libvlc.dll" set VLC_DIR=%%D
)
if "%VLC_DIR%"=="" (
    if exist "vlc-temp\libvlc.dll" set VLC_DIR=vlc-temp
)
if "%VLC_DIR%"=="" (
    echo 错误: 无法找到VLC运行时目录
    exit /b 1
)
echo VLC目录: %VLC_DIR%

:: 用PyInstaller打包
echo [3/5] PyInstaller打包中...
%PYTHON% -m PyInstaller ^
    --name "MediaBrowser" ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --add-data "%VLC_DIR%\libvlc.dll;." ^
    --add-data "%VLC_DIR%\libvlccore.dll;." ^
    --add-data "%VLC_DIR%\plugins;plugins" ^
    --collect-submodules PySide6 ^
    main.py

if %errorlevel% neq 0 (
    echo 错误: PyInstaller打包失败
    exit /b 1
)

:: 复制VLC的dll到输出目录（add-data可能不够，确保复制）
echo [4/5] 复制VLC运行时到输出目录...
copy /y "%VLC_DIR%\libvlc.dll" "dist\MediaBrowser\" >nul
copy /y "%VLC_DIR%\libvlccore.dll" "dist\MediaBrowser\" >nul
if exist "dist\MediaBrowser\plugins" rmdir /s /q "dist\MediaBrowser\plugins"
xcopy /e /i /y /q "%VLC_DIR%\plugins" "dist\MediaBrowser\plugins" >nul

:: 清理临时文件
echo [5/5] 清理临时文件...
rmdir /s /q vlc-temp
rmdir /s /q build

echo.
echo ========================================
echo   打包完成!
echo   输出目录: dist\MediaBrowser\
echo   主程序: dist\MediaBrowser\MediaBrowser.exe
echo ========================================
echo.
echo 提示: 可以将整个 MediaBrowser 文件夹压缩分发
pause
