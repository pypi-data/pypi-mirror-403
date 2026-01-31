#!/bin/sh
# Clone or update core Mercurial repo at the provided path. Useful for CI
# runners that don't have a shared repo setup, e.g. the shell runner that is
# currently used for Windows CI.

URL=https://mirror.octobus.net/hg
if hg root -R "$1"; then
    hg pull -R "$1" "$URL"
else
    rm -rf "$1"
    hg clone "$URL" "$1"
fi
