# utility to setup pythonpath to point into the tested repository

export SRCDIR="`dirname $TESTDIR`"
if [ -n "$PYTHONPATH" ]; then
    export HGTEST_ORIG_PYTHONPATH=$PYTHONPATH
    if uname -o 2> /dev/null | grep -q Msys; then
        export PYTHONPATH="$SRCDIR;$PYTHONPATH"
    else
        export PYTHONPATH=$SRCDIR:$PYTHONPATH
    fi
else
    export PYTHONPATH=$SRCDIR
fi

for SP in "$HGTMP"/install/lib/python*/site-packages/; do
    # find site-packages directory for each Python version (there's most likely
    # only one, but let's be safe)
    if [ -d "$SP" ]; then
        # adding path to our extensions to the current virtualenv
        echo "$SRCDIR" > "$SP/evolve.pth"
    fi
done
