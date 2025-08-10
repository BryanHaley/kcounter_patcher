python.exe patch_killcount_mod.py -d "Half-Life WON" patch

@echo off
call "%~dp0Bunnymod XT\update.bat"
cd "%~dp0Half-Life WON"
"..\Bunnymod XT\Injector" hl.exe -gl -32bpp -w 1280 -h 960 -window -game valve_WON -noforcemparms
"..\RInput\RInput.exe" hl.exe
::Remove "::" on the next line to launch the game with high priority.
::wmic process where name="hl.exe" CALL setpriority "high priority"

:wait_for_hl_exit
timeout /t 1
wmic process where name="hl.exe" get name |find "hl.exe">nul
if %errorlevel%==0 goto :wait_for_hl_exit

cd "%~dp0"
python.exe patch_killcount_mod.py -d "Half-Life WON" clean