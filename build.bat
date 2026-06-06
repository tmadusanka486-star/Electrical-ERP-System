@echo off
echo Building T^&S PowerTech ERP Desktop Application...
echo Please wait, this might take a few minutes...

echo Running PyInstaller in Directory Mode (for fast startup)...
python -m PyInstaller --name "MyShopERP" --clean --noconsole --onedir --icon="logo.ico" --collect-all supabase --hidden-import supabase --add-data "templates;templates" --add-data "static;static" --add-data ".env;." desktop_app.py
echo Copying logo file...
copy logo.ico dist\MyShopERP\

echo.
echo Packaging into a professional Windows Installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

echo.
echo Build complete! 
echo You can find your installation setup: dist\MyShopERP_Setup.exe
echo.
echo The application is now fully standalone and installs like a professional program!
pause
