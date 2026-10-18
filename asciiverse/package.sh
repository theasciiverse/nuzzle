#!/bin/sh
# Packs the build into dist/nuzzle-<target>.tar.gz for av: the binary at the
# top with its default config files in cfg/, the man page, README.md,
# LICENSE and PATCHES.md.
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
stage=stage/nuzzle
rm -rf "$stage" && mkdir -p "$stage" dist
cp out/nuzzle man/nuzzle.6 README.md LICENSE PATCHES.md "$stage/"
cp -r cfg "$stage/cfg"
tar -czf "dist/nuzzle-$target.tar.gz" -C "$stage" .
ls dist
