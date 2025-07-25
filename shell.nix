{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell rec {
	buildInputs = with pkgs; [
    rakudo zef readline # tracking.raku
    zint # barcodes
    (python3.withPackages (pythonPkgs: with pythonPkgs; [
        paho-mqtt configparser inotify-simple # stats.py
        requests # odarissync.py
        pillow # barcode.py
    ]))
    nodejs_22 yarn # rented-overview.js
    cmake libudev-zero # ptouch-770
	];
}
