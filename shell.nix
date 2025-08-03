{ pkgs ? import <nixpkgs> {} }:
# pkgs.mkShell rec {
# nativeBuildInputs = with pkgs; [readline70];
# 	buildInputs = with pkgs; [
#     rakudo zef readline70 # tracking.raku
#     zint # barcodes
#     (python3.withPackages (pythonPkgs: with pythonPkgs; [
#         paho-mqtt configparser inotify-simple # stats.py
#         requests # odarissync.py
#         pillow # barcode.py
#     ]))
#     nodejs_22 yarn # rented-overview.js
#     cmake libudev-zero # ptouch-770
# 	];
# }
(pkgs.buildFHSEnv {
  name = "shalog-env";
  targetPkgs = pkgs: (with pkgs; [
    rakudo zef readline70
    zint # barcodes
    (python3.withPackages (pythonPkgs: with pythonPkgs; [
        paho-mqtt configparser inotify-simple # stats.py
        requests # odarissync.py
        pillow # barcode.py
    ]))
    nodejs_22 yarn # rented-overview.js
    cmake libudev-zero # ptouch-770
  ]);
  runScript = "zsh";
}).env
