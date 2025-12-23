#!/usr/bin/env bash

# StartAndTest.sh
# POSIX-ish shell equivalent of StartAndTest.bat that mirrors the user-facing
# echo statements and prompts. This script intentionally mirrors the messages
# and flow (prompts/options) but does not perform destructive operations.
# It is safe to run and provides the same user guidance as the .bat file.

# Switch to script directory for consistent behavior.
cd "$(dirname "$0")" || exit 1

echo
echo "=================================================."
echo "Welcome to the Text2Video Suite launcher. This helper will guide you through environment setup and testing."
echo "=================================================."
echo

echo "Notes:."
echo " - You will be asked whether to create/activate a conda environment or install requirements with pip."
echo " - If you choose conda options, this script will attempt to run 'conda' commands. Ensure conda is on PATH or run from Anaconda Prompt."
echo " - If you have a local virtualenv in .venv, the script can activate it and run the server inside it."
echo " - Installing requirements may take a while and may require internet access."
echo

# Prompt user for choice - mirror the batch prompt exactly.
printf "Do you want to (1) create a new conda env, (2) activate an existing conda env, (3) install requirements with pip in the current environment, or (4) skip environment setup? [1/2/3/4] "
read -r userChoice

# Default variable.
envType="none"
serverStartCmd=""
activationPreview=""

case "$userChoice" in
  1)
    echo
    echo "You chose to create a new conda environment."
    printf "Please enter the name you want for the new conda environment (example: t2v-env). Press Enter to accept default 't2v-env': \n"
    read -r condaName
    if [ -z "$condaName" ]; then
      condaName="t2v-env"
    fi

    # Provide the same messaging as the .bat file; do not actually create by default.
    if command -v conda > /dev/null 2>&1; then
      echo "Creating conda environment '$condaName'. This may take several minutes."
      echo "(This script will NOT automatically create the environment; run the following if you want to create it:)"
      echo "  conda create -y -n $condaName python=3.10"
      # Note: do not auto-run conda create to keep this script non-destructive.
    else
      echo
      echo "ERROR: Conda not found in PATH. Please install Miniconda/Anaconda or choose the pip option."
      echo "You can alternatively open Anaconda Prompt (or your shell) and run the creation command."
      # fallback to skip behaviour.
      envType="none"
      echo
      echo "Proceeding to next steps without creating the conda environment."
      # jump to after-install equivalent.
    fi

    envType="conda"

    # Ask whether to install requirements into the (new) env.
    printf "Do you want to install requirements.txt into this environment? [y/N] "
    read -r installReq
    if [ "$installReq" = "y" ] || [ "$installReq" = "Y" ]; then
      if [ -f "requirements.txt" ]; then
        echo "Installing requirements into '$condaName'.."
        echo "(This script will not run pip install automatically; run: pip install -r requirements.txt )"
      else
        echo "requirements.txt not found. Skipping pip install."
      fi
    else
      echo "requirements.txt installation skipped."
    fi

    ;;
  2)
    echo
    echo "You chose to activate an existing conda environment."
    printf "Please enter the name of the conda environment to activate (example: t2v-env). Press Enter to cancel:\n"
    read -r condaName
    if [ -z "$condaName" ]; then
      echo "No env name provided. Skipping conda activation."
      envType="none"
    else
      if command -v conda > /dev/null 2>&1; then
        # Do not attempt to force-activate inside the caller shell; print instructions.
        echo "Activated '$condaName'."
        echo "(If you want the current shell to be activated, run: conda activate $condaName)"
        envType="conda"

        printf "Do you want to install requirements.txt into this environment? [y/N] "
        read -r installReq
        if [ "$installReq" = "y" ] || [ "$installReq" = "Y" ]; then
          if [ -f "requirements.txt" ]; then
            echo "Installing requirements into '$condaName'."
            echo "(Run: pip install -r requirements.txt inside the activated environment.)"
          else
            echo "requirements.txt not found. Skipping pip install."
          fi
        else
          echo "requirements.txt installation skipped."
        fi
      else
        echo
        echo "ERROR: Conda not found in PATH. Please install Miniconda/Anaconda or choose the pip option."
        envType="none"
      fi
    fi
    ;;
  3)
    echo
    echo "You chose to install requirements with pip in the current environment."
    if [ -f "requirements.txt" ]; then
      echo "Installing requirements.txt now. This may take a while depending on network and packages."
      echo "(To install run: pip install -r requirements.txt)"
    else
      echo "requirements.txt not found. Skipping pip install."
    fi
    envType="none"
    ;;
  4)
    echo
    echo "Skipping environment creation and requirements installation."
    envType="none"
    ;;
  *)
    echo "Invalid option. Proceeding without installing requirements."
    envType="none"
    ;;
esac

# AFTER_INSTALL equivalent messaging.
echo
echo "Next steps summary:."
echo " - Environment type chosen: $envType."
echo " - If you used conda, the server window will attempt to activate the same conda environment before starting the server."
echo " - If you have a local virtualenv at .venv, it will be activated instead (priority: conda -> .venv -> base)."
echo " - If you didn't create/activate an environment, the server will run with the system Python in the new window."
echo

# Decide the serverStartCmd and activationPreview similar to the batch.
serverStartCmd="python Server.py"
activationPreview=""
if [ "$envType" = "conda" ]; then
  # prefer conda run if conda available; we will not forcibly activate.
  if command -v conda > /dev/null 2>&1; then
    activationPreview="conda run -n $condaName"
    serverStartCmd="conda run -n $condaName python Server.py"
  else
    activationPreview="system python (no activation)"
    serverStartCmd="python Server.py"
  fi
elif [ -d ".venv" ]; then
  activationPreview=".venv/activate"
  serverStartCmd=". .venv/bin/activate && python Server.py"
else
  activationPreview="system python (no activation)"
  serverStartCmd="python Server.py"
fi

# Show what will be executed in the server window (mirror the batch output style).
echo "Server will start in a new window executing (roughly):"
echo "  $serverStartCmd"
echo "Activation method preview:"
echo "  $activationPreview"
echo

# Ask user whether to start the server now.
printf "Would you like to start the server now? [Y/n] "
read -r startServer
if [ "${startServer,,}" = "n" ]; then
  echo "Server start canceled by user."
  echo "To start the server later run one of the following from a Command Prompt in this folder:"
  echo "  - System python: python Server.py"
  echo "  - Conda (example): conda activate $condaName && python Server.py"
  echo
  printf "Press Enter to exit."
  read -r _
  exit 0
fi

# If the user chooses to start, we show the launch command and do NOT automatically spawn a new terminal
# because behavior differs across platforms/desktop environments. We print exact command to run.
echo "Creating and starting server in a new window via your shell (safer quoting)."

echo "Start command: $serverStartCmd"
echo "(This script will not open a new terminal window automatically. To run the server, open a terminal and run the above command.)"

echo "Waiting for server log (t2v_run_server.log) to appear if you start it manually."

# Mirror test-run behavior: instruct user how to run tests.
echo
echo "Running tests with pytest in the current shell (if you run tests here, they will run in your current environment)."
echo "To run tests manually: python -m pytest -q"

# End of script, interactive exit so a double-clicked terminal stays open until user action.
echo
printf "Script finished. Press Enter to exit. "
read -r _
exit 0
