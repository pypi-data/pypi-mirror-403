#require test-repo

Enable obsolescence to avoid the warning issue when obsmarkers are found

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > EOF

  $ "$PYTHON" "$TESTDIR/testlib/check-compat-strings.py" \
  > "$TESTDIR/../hgext3rd/" "$RUNTESTDIR/.."
