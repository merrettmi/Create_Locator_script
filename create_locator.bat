@echo off
@REM  M:\Processing_Scripts\Create_Locator_Service\create_locator.bat

cls
setlocal enabledelayedexpansion

rem --- Get Wi-Fi SSID (may be empty if on Ethernet only) ---
for /f "usebackq tokens=*" %%A in (`
    powershell -NoProfile -Command "(Get-NetConnectionProfile | Where-Object {$_.InterfaceAlias -like 'Wi-Fi*'}).Name"
`) do (
    set "SSID=%%A"
)

echo Current SSID: "%SSID%"

rem --- Get IPv4 address (first one ipconfig reports) ---
rem --- Get IPv4 from the physical Ethernet adapter only ---
for /f "tokens=2 delims=:" %%A in ('
    ipconfig ^| findstr /i /c:"Ethernet adapter Ethernet" /c:"IPv4 Address"
') do (
    set "ip=%%A"
)
set "ip=%ip: =%"
echo Current IP: "%ip%"


rem --- Decide if on City Network ---
set "ONCITY=0"

rem Condition 1: IP starts with 172.24
if "%ip:~0,6%"=="172.24" set "ONCITY=1"

if "%ip:~0,6%"=="10.1.9" set "ONCITY=1"

rem Condition 2: Wi-Fi SSID is CITY.local
if /i "%SSID%"=="CITY.local" set "ONCITY=1"
@rem echo "oncity=%ONCITY%"

if "%ONCITY%"=="1" (
    echo *** On City Network ***
) else (
    echo *** Not on City Network ***
)



cd /d "%~dp0"

echo ----------------------------------------
echo Running locator build
echo Script path: %~dp0
echo Python: ArcGIS Pro (propy)
echo ----------------------------------------




@REM if /I "%COMPUTERNAME%"=="AlienMike" (
if "!ONCITY!" NEQ "1" (
    echo Running on AlienMike

    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py"  --all --fgdb-base "D:\City_STUFF\Create_Locator_v4\resulting_locators" --project-root "D:\City_STUFF\Create_Locator_v4"
    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --list --dataset city_boundary --use-local-fdgb --fgdb-base "D:\City_STUFF\Create_Locator_v4\results" --project-root "D:\City_STUFF\Create_Locator_v4"


    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset address_points --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset city_boundary --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset yukon --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset streets --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset neighbourhood --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset parcels --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    @REM @call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --dataset condo_address --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .

    @REM call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --all --use-local-gdb --local_gdb ./copyOfMasterData.gdb  --fgdb-base .\results\processing --project-root .
    call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "D:\City_STUFF\Create_Locator_v4\build_locator.py" --all  --fgdb-base .\results\processing --project-root .
) else (
    call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" "M:\Processing_Scripts\Create_Locator_Service\build_locator.py" --all  --fgdb-base .\results\processing --project-root .
        @REM   --use-local-gdb --local_gdb ./copyOfMasterData.gdb
)

echo got errorlevel: %errorlevel%
if errorlevel 1 (
    echo Error during cleanup. Exiting.
    exit /b 1
)
endlocal