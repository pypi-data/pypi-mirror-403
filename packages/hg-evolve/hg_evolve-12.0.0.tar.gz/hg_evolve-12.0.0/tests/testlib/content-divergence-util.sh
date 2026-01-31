#!/bin/sh
# setup config and various utility to test content-divergence resolution

. $TESTDIR/testlib/common.sh

cat >> $HGRCPATH <<EOF
[ui]
# simpler log output
logtemplate ="{rev}:{node|short} ({phase}): {desc|firstline} {if(troubles, '[{troubles}]')}\n"

[phases]
# non publishing server
publish=False

[extensions]
evolve=
rebase=
EOF

setuprepos() {
    echo creating test repo for test case $1
    mkdir $1
    cd $1

    echo - upstream
    hg init upstream
    cd upstream
    mkcommit O
    hg phase --public .
    cd ..
    echo - local
    hg clone -q upstream local
    echo - other
    hg clone -q upstream other
    echo 'cd into `local` and proceed with env setup'
}
