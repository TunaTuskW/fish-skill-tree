@echo off
setlocal
rem Launcher: installs the pinned CLI build for this machine on first use, then runs it.
set "TOOL=gsheets"
set "PLUGIN_VERSION=0.0.6"
set "CLI_VERSION=986250228"
set "BASE_URL=https://storage.googleapis.com/antigravity-public/plugin/cli/%CLI_VERSION%"
rem --- shared launcher logic; keep identical across plugins ---

set "IS_FALLBACK=0"
if "%ANTIGRAVITY_APP_DATA_DIR%"=="" (
  set "ANTIGRAVITY_APP_DATA_DIR=%USERPROFILE%\.gemini\antigravity"
  set "IS_FALLBACK=1"
)

rem This script lives at <plugin>\skills\<skill>\scripts\, three levels below
rem the plugin's install directory.
for %%I in ("%~dp0..\..\..") do set "PLUGIN_DIR_NAME=%%~nxI"
set "BIN_DIR=%ANTIGRAVITY_APP_DATA_DIR%\plugin_data\%PLUGIN_DIR_NAME%\bin"
set "TARGET=%BIN_DIR%\%TOOL%-%CLI_VERSION%.exe"

if not exist "%ANTIGRAVITY_APP_DATA_DIR%\bin" mkdir "%ANTIGRAVITY_APP_DATA_DIR%\bin" >nul 2>nul
if not exist "%ANTIGRAVITY_APP_DATA_DIR%\bin\%TOOL%.cmd" (
  (
    echo @echo off
    echo setlocal
    echo call "%~f0" %%*
    echo exit /b %%ERRORLEVEL%%
  ) > "%ANTIGRAVITY_APP_DATA_DIR%\bin\%TOOL%.cmd" 2>nul
  if "%IS_FALLBACK%"=="0" echo Registered '%TOOL%' into PATH. It can now be run directly. 1>&2
)

if exist "%TARGET%" goto run

set "ARCH=x86_64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ARCH=arm64"
if /i "%PROCESSOR_ARCHITEW6432%"=="ARM64" set "ARCH=arm64"
set "EXPECTED_HASH=bab27b983cb3e22b9ac02853e961ca6a6aa7059609e92788cb436f80316f6c4f"
if /i "%ARCH%"=="arm64" set "EXPECTED_HASH=b7989f4f269bd605511594ee6c7ab7a2f41075a135677d9af70bf927cfc5a3af"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
del /q "%BIN_DIR%\%TOOL%-*" 2>nul
set "TMP_FILE=%BIN_DIR%\.%TOOL%.tmp.%RANDOM%"
curl.exe -fsSL "%BASE_URL%/windows_%ARCH%/%TOOL%" -o "%TMP_FILE%"
if errorlevel 1 (
  del /q "%TMP_FILE%" 2>nul
  echo error: failed to download %BASE_URL%/windows_%ARCH%/%TOOL% 1>&2
  exit /b 1
)
set "ACTUAL_HASH="
for /f "skip=1 tokens=* delims=" %%h in ('certutil -hashfile "%TMP_FILE%" SHA256') do (
  if not defined ACTUAL_HASH set "ACTUAL_HASH=%%h"
)
set "ACTUAL_HASH=%ACTUAL_HASH: =%"
if /i not "%ACTUAL_HASH%"=="%EXPECTED_HASH%" (
  del /q "%TMP_FILE%" 2>nul
  echo error: SHA-256 verification failed for %TMP_FILE% 1>&2
  exit /b 1
)
move /y "%TMP_FILE%" "%TARGET%" >nul

:run
"%TARGET%" %*
exit /b %ERRORLEVEL%
