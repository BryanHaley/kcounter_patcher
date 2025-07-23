:wait_for_hl_exit
timeout /t 0.1
wmic process where name="hl.exe" get name |find "hl.exe">nul
if %errorlevel%==0 goto :wait_for_hl_exit

cd "%~dp0"
patch_killcount_mod.exe clean