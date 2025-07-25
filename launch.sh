#!/usr/bin/env bash

trap ":" INT # prevent ctrl+c from quitting

echo -e "Starting...\n\n";
while true; do
  ./tracking.raku
  echo -e "\n\nOops, sorry!\nRestarting...\n\n"
done
