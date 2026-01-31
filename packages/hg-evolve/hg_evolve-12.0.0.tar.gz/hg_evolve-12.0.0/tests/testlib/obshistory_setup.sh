. $TESTDIR/testlib/common.sh

cat >> $HGRCPATH <<EOF
[ui]
interactive = true
[phases]
publish=False
[extensions]
evolve =
[experimental]
evolution.effect-flags = yes
EOF

sync() {
   hg pull -R $TESTTMP/server . -q
}
