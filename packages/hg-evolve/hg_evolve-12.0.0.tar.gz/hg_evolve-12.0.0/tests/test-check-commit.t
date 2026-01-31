#require test-repo

  $ . "$RUNTESTDIR/helpers-testrepo.sh"

Enable obsolescence to avoid the warning issue when obsmarkers are found

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > EOF

Go back in the hg repo

  $ cd $TESTDIR/..

  $ REVSET='not public() and ::. and not desc("# no-check-commit")'

  $ mkdir "$TESTTMP/p"
  $ REVS=`testrepohg log -r "$REVSET" -T.`
  $ if [ -n "$REVS" ] ; then
  >   testrepohg export --git -o "$TESTTMP/p/%n-%h" -r "$REVSET"
  >   for f in `ls "$TESTTMP/p"`; do
  >      "$RUNTESTDIR/../contrib/check-commit" < "$TESTTMP/p/$f" > "$TESTTMP/check-commit.out"
  >      if [ $? -ne 0 ]; then
  >          node="${f##*-}"
  >          echo "Revision $node does not comply with rules"
  >          echo '------------------------------------------------------'
  >          cat ${TESTTMP}/check-commit.out
  >          echo
  >     fi
  >   done
  > fi
