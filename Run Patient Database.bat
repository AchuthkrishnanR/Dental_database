@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if not errorlevel 1 goto use_py

where python >nul 2>&1
if errorlevel 1 goto no_python

python server.py
goto finished

:use_py
py -3 server.py
goto finished

:no_python
echo Python 3 is required to run Patient Database.
echo Install Python 3, then open this file again.
echo No extra Python packages are required.
pause

:finished
endlocal
