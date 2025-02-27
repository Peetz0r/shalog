#!/bin/bash

trap ":" INT # prevent ctrl+c from quitting

while true; do
  ./tracking.p6
  echo -e "\n\nOops, sorry!\nRestarting...\n\n"
done