@echo off
@setlocal enabledelayedexpansion
echo Marketing dashboard refreshing ...
echo File Being Processed: %0% > logfile.txt
set LOG="%~d0%~p0logfile.txt"
echo. >> %LOG%
echo Start Processing: %DATE% %TIME:~0,8% >> %LOG%
cd .\scripts\
echo.
for %%i in (*.py) do (
	echo Start Refreshing %%~ni
	echo Start %%~ni Refreshing: !DATE! !TIME:~0,8! >> %LOG%
	python %%i
	echo %%~ni Errors Occured: !ERRORLEVEL! >> %LOG%
	echo Finish %%~ni Refreshing: !DATE! !TIME:~0,8! >> %LOG%
	echo %%~ni Have Been Refreshed!
	echo.
)
echo Finish Processing: %DATE% %TIME:~0,8% >> %LOG%
echo Check logfile.txt for more details.
pause