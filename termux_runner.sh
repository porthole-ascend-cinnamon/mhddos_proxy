#!/bin/bash

git config --global --add safe.directory /storage/emulated/0/mhddos_proxy
git config --global --add safe.directory ~/mhddos_proxy

BRANCH="main"
PID=""

RED="\033[1;31m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
RESET="\033[0m"

PYTHON=$1
SCRIPT_ARGS="${@:2}"

trap 'shutdown' SIGINT SIGQUIT SIGTERM ERR

function shutdown() {
    echo -e "\n${BLUE}---> Shutting down...${RESET}"
    stop_script
    exit
}

function stop_script() {
  if [ -n "$PID" ];
  then
    kill -INT $PID
    wait $PID
    PID=""
  fi
}

function update_script() {
    git reset -q --hard
    git checkout -q $BRANCH
    git pull -q || echo -e "${RED}git pull failed${RESET}"
    $PYTHON -m pip install -q -r termux_requirements.txt
}

echo -e "\n${GREEN}---------------------Auto-update enabled---------------------${RESET}"
$PYTHON -m pip install -q -r termux_requirements.txt

while true
do

  git fetch -q origin $BRANCH || echo -e "${RED}git fetch failed${RESET}"

  if [ -n "$(git diff --name-only origin/$BRANCH)" ]
  then
    echo -e "\n${GREEN}[$(date +"%d-%m-%Y %T")] - New version available, updating the script!${RESET}"
    stop_script
    update_script
    bash runner.sh $PYTHON $SCRIPT_ARGS
  fi

  while [ -z "$PID" ]
  do

    AUTO_MH=1 $PYTHON runner.py $SCRIPT_ARGS & PID=$!
    sleep 1

    if [ "${SCRIPT_ARGS}" == "--help" ]
    then
      exit 0
    fi

    if ! kill -0 $PID
    then
      PID=""
      echo -e "\n${RED}Error starting - retry in 30 seconds! Ctrl+C to exit${RESET}"
      sleep 30
    fi

  done

  sleep 600

done
