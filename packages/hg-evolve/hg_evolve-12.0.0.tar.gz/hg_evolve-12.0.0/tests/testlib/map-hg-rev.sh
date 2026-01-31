#!/bin/sh
set -eu

case $1 in
    default)
        echo default
        ;;
    mercurial-*)
        exp=$(echo "$1" | cut -d- -f2 | sed 's#\.#\\.#g')
        echo 'max(tag("re:^'"$exp"'"))'
        ;;
    *)
        echo stable
        ;;
esac
