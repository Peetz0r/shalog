{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell rec {
	buildInputs = with pkgs; [
    rakudo zef readline
    python3 nodejs_22
    cmake libudev-zero # ptouch-770
	];
}
