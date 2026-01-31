#require unix-permissions

Test that sqlite3 cache files inherit the permissions of the .hg
directory like other cache files.

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > evolve =
  > EOF
  $ hg init test
  $ cd test
  $ chmod 700 .hg
  $ hg debugupdatecache
  $ ls -l .hg/cache/evoext_*.sqlite
  -rw------- * .hg/cache/evoext_obshashrange_v2.sqlite (glob)
  -rw------- * .hg/cache/evoext_stablerange_v2.sqlite (glob)
  $ rm -r .hg/cache
  $ chmod 770 .hg
  $ hg debugupdatecache
  $ ls -l .hg/cache/evoext_*.sqlite
  -rw-rw---- * .hg/cache/evoext_obshashrange_v2.sqlite (glob)
  -rw-rw---- * .hg/cache/evoext_stablerange_v2.sqlite (glob)
  $ rm -r .hg/cache
  $ chmod 774 .hg
  $ hg debugupdatecache
  $ ls -l .hg/cache/evoext_*.sqlite
  -rw-rw-r-- * .hg/cache/evoext_obshashrange_v2.sqlite (glob)
  -rw-rw-r-- * .hg/cache/evoext_stablerange_v2.sqlite (glob)
