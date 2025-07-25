#!/bin/bash

host="10.42.42.222"
port="9100"

function code128 () {
  zint --barcode 20 --notext --height 50 --scale 0.5 --direct --data "$1" |\
  convert mch-logo-12mm.png PNG:- +append +antialias -gravity center -font DejaVu-Sans-Mono-Bold -pointsize 20 "label:$1" -append -gravity west -extent x128 pbm:-
}

function aztec () {
  zint --barcode 92 --vers 4 --scale 2 --direct --data "$1" |\
  convert mch-logo-24mm.png -append -gravity center PNG:- +antialias -font DejaVu-Sans-Mono-Bold -pointsize 20 -size 128x "caption:$1" -append -rotate 90 pbm:-
}

function checktape () {
  echo "Trying label printer on wifi at $host"
  width="$(curl -s http://$host/general/status.html | grep -Po '\d+(?=mm)')"
  echo -n "Detected $width mm tape, ";

  if [ "$width" != "$1" ]; then
    echo -e "\033[1;91mplease load $1 mm tape instead!\033[0m";
    # do not exit, send the incorrent print command anyway
    # it'll show a useful error on the label printer
    # this might help if the user isn't looking at the laptop
    # because they might be witing for a label that's never going to come
    # in which case they're probably looking at the label printer
  fi;
}

if lsusb | grep -iE Brother.+PT > /dev/null; then
  echo "Detected label printer on USB"

  if [ "$1" == "code128" ]; then
    # FIXME: tmp hack to use old script
    ptouch-770-old/code128.pl "${@:2}"; exit
    code128 "$2" | ptouch-770/ptouch-770-write-usb 0 12

  elif [ "$1" == "aztec" ]; then
    # FIXME: tmp hack to use old script
    ptouch-770-old/aztec.pl "${@:2}"; exit
    aztec "$2" | ptouch-770/ptouch-770-write-usb 0 24
  fi;

else
  if [ "$1" == "code128" ]; then
    checktape "12"
    echo "printing Code128 barcode";
    code128 "$2" | ptouch-770/ptouch-770-write-stdout 12 | nc $host $port;

  elif [ "$1" == "aztec" ]; then
    checktape "24"
    echo "printing Aztec barcode";
    aztec "$2" | ptouch-770/ptouch-770-write-stdout 24 | nc $host $port;
  fi;
fi
