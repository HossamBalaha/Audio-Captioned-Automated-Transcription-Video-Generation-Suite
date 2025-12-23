@echo off
REM RunTests.bat - helper similar to StartServer.bat but for running pytest.
REM Provides interactive choices: create/activate conda env, install requirements, or use pip/.venv/system python.
cd /d "%~dp0"

setlocal EnableDelayedExpansion

echo.
echo ==================================================
echo RunTests helper - will guide environment setup and run pytest.
echo ==================================================
echo.
echo Notes:
echo  - For conda environments it's recommended to run this from Anaconda Prompt if you have activation issues.
echo  - This script prefers `conda run -n <env>` which works from normal cmd as well.
echo.
echo Choose an option:
echo  1) Create a new conda env.
echo  2) Activate an existing conda env (for installing requirements).
echo  3) Install requirements with pip in the current environment.
echo  4) Skip environment setup and run tests.
echo.
set /p userChoice="Enter choice [1/2/3/4]: "
if "%userChoice%"=="1" goto CREATE_CONDA
if "%userChoice%"=="2" goto ACTIVATE_CONDA
if "%userChoice%"=="3" goto PIP_INSTALL
if "%userChoice%"=="4" goto RUN_SETUP

echo Invalid option. Proceeding to run setup.

:CREATE_CONDA
echo.
set /p condaName=Enter conda environment name (default: t2v-env):
if "%condaName%"=="" set condaName=t2v-env
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo ERROR: 'conda' not found in PATH. Install conda or run from Anaconda Prompt.
  pause
  goto :eof
)
echo Creating conda env '%condaName%' (may take a few minutes)...
call conda create -y -n %condaName% python=3.10
if %ERRORLEVEL% neq 0 (
  echo Failed to create conda environment.
  pause
  goto :eof
)
set "envType=conda"
echo Conda environment created.
goto RUN_SETUP

:ACTIVATE_CONDA
echo.
set /p condaName="Enter existing conda environment name (leave blank to cancel): "
if "%condaName%"=="" (
  echo No env chosen. Returning to setup.
  set "envType=none"
  goto RUN_SETUP
)
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo ERROR: 'conda' not found in PATH. Install conda or run from Anaconda Prompt.
  pause
  goto :eof
)
set "envType=conda"
echo Conda environment selected: %condaName%
set /p installReq="Install requirements into this environment now? [y/N]: "
if /I "%installReq%"=="Y" (
  if exist requirements.txt (
    echo Installing requirements into '%condaName%'...
    conda run -n %condaName% pip install -r requirements.txt
    echo requirements installation finished.
  ) else (
    echo requirements.txt not found. Skipping.
  )
)
goto RUN_SETUP

:PIP_INSTALL
echo.
if exist requirements.txt (
  echo Installing requirements with pip in current environment...
  pip install -r requirements.txt
  echo requirements installation finished.
) else (
  echo requirements.txt not found. Nothing to install.
)
set "envType=none"
goto RUN_SETUP

:RUN_SETUP
echo.
echo Environment setup complete. Ready to run tests.

REM Find conda executable if available for later use.
where conda >nul 2>&1
if %ERRORLEVEL%==0 (
  for /f "usebackq delims=" %%A in (`where conda`) do set "condaExe=%%~A"
) else (
  set "condaExe="
)

set /p startNow="Proceed to run pytest in this window? [Y/n]: "
if /I "%startNow%"=="N" (
  echo Run canceled.
  pause
  goto :eof
)

REM --- Run pytest in same window ---
if "%envType%"=="conda" (
  if defined condaExe (
    echo Using conda executable: "%condaExe%"
    echo Running pytest with conda run -n %condaName% ...
    REM Use --no-capture-output so conda forwards stdout/stderr to this console, and run a cmd /C that runs pytest unbuffered.
    "%condaExe%" run -n %condaName% --no-capture-output cmd /C "python -u -m pytest"
    set "testExit=%ERRORLEVEL%"
    goto END
  ) else (
    echo 'conda' not found when attempting to run. Please ensure conda is on PATH or run from Anaconda Prompt.
    pause
    exit /b 1
  )
) else (
  if exist ".venv\Scripts\activate.bat" (
    echo Activating .venv and running pytest.
    call ".venv\Scripts\activate.bat"
    if %ERRORLEVEL% neq 0 (
      echo Failed to activate .venv.
      pause
      exit /b 1
    )
    where python >nul 2>&1 || (
      echo Python not found after activating .venv. Aborting.
      pause
      exit /b 1
    )
    python -u -m pytest
    set "testExit=%ERRORLEVEL%"
    goto END
  ) else (
    echo No .venv present. Using system python to run pytest.
    where python >nul 2>&1 || (
      echo Python not found in PATH. Install Python or create a venv/conda env.
      pause
      exit /b 1
    )
    python -u -m pytest
    set "testExit=%ERRORLEVEL%"
    goto END
  )
)

:END
echo Tests finished. Exit code: %testExit%.
if "%testExit%"=="0" (
  pause
  exit /b 0
) else (
  echo pytest exited with code %testExit%.
  pause
  exit /b %testExit%
)
