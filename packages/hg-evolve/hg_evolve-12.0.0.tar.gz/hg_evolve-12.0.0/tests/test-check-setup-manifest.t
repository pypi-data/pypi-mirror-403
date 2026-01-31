#require test-repo check-manifest

Enable obsolescence to avoid the warning issue when obsmarkers are found

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > EOF

Run check manifest:

  $ cd $TESTDIR/..
  $ check-manifest
  lists of files in version control and sdist match
