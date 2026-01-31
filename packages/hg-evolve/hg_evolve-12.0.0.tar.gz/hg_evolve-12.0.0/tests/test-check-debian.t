#require test-repo

Enable obsolescence to avoid the warning issue when obsmarkers are found

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > EOF

  $ "$PYTHON" "$TESTDIR/testlib/check-min-versions.py" \
  > "$TESTDIR/../hgext3rd/evolve/metadata.py" "$TESTDIR/../debian/control"

  $ "$PYTHON" "$TESTDIR/testlib/check-min-versions.py" \
  > "$TESTDIR/../hgext3rd/topic/__init__.py" "$TESTDIR/../debian/control"
