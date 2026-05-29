@echo off
setlocal

:: ==========================================
:: MY SHOP ERP - AUTO BACKUP SCRIPT
:: ==========================================

:: Change this URL to your actual Vercel app URL!
:: Example: set "URL=https://my-shop-erp.vercel.app/api/backup"
set "URL=http://localhost:5000/api/backup"

:: Secure folder where backups will be saved
:: Change this to your preferred path (e.g., C:\ERP_Backups)
set "BACKUP_DIR=C:\ERP_Backups"

:: ==========================================

echo [INFO] Starting Backup Process...
if not exist "%BACKUP_DIR%" (
    echo [INFO] Creating backup folder: %BACKUP_DIR%
    mkdir "%BACKUP_DIR%"
)

:: Get current date and time to create a unique filename
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%-%MM%-%DD%_%HH%-%Min%"

set "FILE_PATH=%BACKUP_DIR%\ERP_Backup_%TIMESTAMP%.json"

echo [INFO] Downloading database backup from %URL% ...
curl -s -f -o "%FILE_PATH%" "%URL%"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Backup saved securely to: %FILE_PATH%
) else (
    echo [ERROR] Backup failed! Please check your internet connection and URL.
)

:: Wait 3 seconds and close
timeout /t 3 /nobreak >nul
exit
