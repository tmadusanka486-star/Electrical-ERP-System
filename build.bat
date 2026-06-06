@echo off
echo Building T^&S PowerTech ERP Desktop Application...
echo Please wait, this might take a few minutes...

echo Running PyInstaller...
python -m PyInstaller --name "MyShopERP" --noconsole --onefile --collect-all supabase --collect-all gotrue --collect-all postgrest --collect-all realtime --collect-all storage3 --collect-all httpx --add-data "templates;templates" --add-data "static;static" desktop_app.py

echo.
echo Build complete! 
echo You can find your application: dist\MyShopERP.exe
echo.
echo IMPORTANT: Make sure to copy your .env file into the same folder 
echo as MyShopERP.exe so it can connect to your Supabase Database!
pause
