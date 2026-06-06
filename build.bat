@echo off
echo Building T^&S PowerTech ERP Desktop Application...
echo Please wait, this might take a few minutes...

echo Running PyInstaller...
python -m PyInstaller --name "MyShopERP" --clean --noconsole --onefile --icon="logo.ico" --collect-all supabase --hidden-import supabase --add-data "templates;templates" --add-data "static;static" --add-data ".env;." desktop_app.py

echo.
echo Build complete! 
echo You can find your application: dist\MyShopERP.exe
echo.
echo The application is now fully standalone! You do not need to copy any .env files.
pause
